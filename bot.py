"""
Telegram bot working in groups and channels. Sends available information about
new members to group administrators.
"""

import datetime
import logging
import hashlib
import base64
import json
import math
import sys
import re
import os
import string
import secrets
import threading
import asyncio
from telebot import asyncio_helper, util
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import BaseMiddleware
from mess import msg


def load_file(filename):
  try:
    with open(filename, 'r', encoding="utf-8") as file:
      data = json.load(file)
  except OSError:
    print('Could not load file:', filename)
    sys.exit(1)
  return data


def save_file(filename, data):
  try:
    with open(filename, 'w', encoding="utf-8") as file:
      file.write(json.dumps(data, indent=2))
  except OSError:
    print('Could not save file:', filename)
    sys.exit(1)


def get_fullname(first_name, last_name):
  return ' '.join(filter(None, (first_name, last_name)))


def get_user_dict(user_id, username, first_name, last_name, enabled):
  username = username if username else ''
  fullname = get_fullname(first_name, last_name)
  return {'id': user_id, 'username': username,
          'fullname': fullname, 'enabled': enabled}


def update_config():
  if 'channels' not in config:
    config['channels'] = []
  if 'owner' not in config:
    if config['owner_id']:
      config['owner'] = get_user_dict(config['owner_id'], '', '', '',
                                      config['owner_enabled'])
    else:
      config['owner'] = {}
    config.pop('owner_id')
    config.pop('owner_enabled')


NAME = 'Inspector Bot'
VERSION = '1.14'
CONFIG_FILE = 'config.json'
AGES_FILE = 'ages.json'
config = load_file(CONFIG_FILE)
update_config()
ages = load_file(AGES_FILE)
PASS_MAX_AGE = 120
PASS_LEN = 16
private = {'timer': None, 'password': ''}
bot = AsyncTeleBot(config['token'], parse_mode='HTML')
LOG_FILE = os.path.splitext(os.path.basename(__file__))[0] + '.log'
LOG_LEVEL = logging.INFO


def lang():
  return config['language']


def check_owner(user_id):
  return config['owner'] and user_id == config['owner']['id']


async def check_owner_set(chat_id, show_tip):
  if not config['owner']:
    text = msg[lang()]['mess_owner_not_set']
    if show_tip:
      text += msg[lang()]['mess_bot_help_tip']
    await bot.send_message(chat_id, text)


def get_ids(section):
  return [x['id'] for x in config[section]]


def get_enabled_uids():
  uids = [config['owner']['id'], ] \
      if config['owner'] and config['owner']['enabled'] else []
  for user in config['users']:
    if user['enabled'] and user['id'] not in uids:
      uids.append(user['id'])
  return uids


def get_owner(user):
  owner = get_user_dict(user.id, user.username, user.first_name,
                        user.last_name, True)
  if config['owner']:
    if config['owner']['id'] != user.id:
      uids = get_ids('users')
      if config['owner']['id'] not in uids:
        config['users'].append(config['owner'])
      if user.id in uids:
        index = uids.index(user.id)
        owner = config['users'][index]
        config['users'].pop(index)
    else:
      owner = config['owner']
  return owner


def get_timestamp(user_id):
  ids = list(ages.keys())
  nids = list(map(int, ids))
  min_id = nids[0]
  max_id = nids[len(nids) - 1]
  if user_id < min_id:
    return [-1, ages[ids[0]]]
  if user_id > max_id:
    return [1, ages[ids[-1]]]
  lid = nids[0]
  for i in range(len(ids)):
    if user_id <= nids[i]:
      uid = nids[i]
      lage = ages[str(lid)]
      uage = ages[str(uid)]
      did = 1 if uid == lid else uid - lid
      idratio = (user_id - lid) / did
      mid_date = math.floor(idratio * (uage - lage) + lage)
      return [0, mid_date]
    lid = nids[i]
  return [0, 0]


def get_age(user_id):
  tst = get_timestamp(user_id)
  if tst[0] < 0:
    res = msg[lang()]['before']
  elif tst[0] > 0:
    res = msg[lang()]['after']
  else:
    res = '~ '
  date = datetime.datetime.fromtimestamp(tst[1] / 1e3)
  return res + str(date.month).zfill(2) + '/' + str(date.year)


def password_generate():
  alph = string.ascii_letters + string.digits
  private['password'] = ''.join(secrets.choice(alph) for i in range(PASS_LEN))


def password_reset():
  private['password'] = ''


def is_command_allow_user(message, owner_set):
  res = not owner_set or config['owner']
  if res and config['owner']:
    uids = [config['owner']['id'], ] + get_ids('users')
    res = message.chat.id in uids
  return res


async def update_chat(chat_dict, chat_type):
  try:
    chat = await bot.get_chat(chat_dict['id'])
    if chat_dict['title'] != chat.title:
      chat_dict['title'] = chat.title
      save_file(CONFIG_FILE, config)
      logging.debug('%s ID:%d data updated: %s', chat_type.capitalize(),
                    chat_dict['id'], str(chat_dict))
  except asyncio_helper.ApiTelegramException:
    pass


async def update_user(user):
  for group in config['groups']:
    try:
      member = await bot.get_chat_member(group['id'], user['id'])
      fullname = get_fullname(member.user.first_name, member.user.last_name)
      if user['username'] != member.user.username \
          or user['fullname'] != fullname:
        user['username'] = member.user.username
        user['fullname'] = fullname
        save_file(CONFIG_FILE, config)
        logging.debug('User ID:%d data updated: %s', user['id'], str(user))
      break
    except asyncio_helper.ApiTelegramException:
      pass


def format_chat_id(chat_id):
  chat_id = chat_id[1:] if chat_id[0] == '@' else chat_id
  chat_id = '-' + chat_id if not chat_id or chat_id[0] != '-' else chat_id
  return chat_id


def get_chat_title(chat_type, title):
  return f'<u>{msg[lang()][chat_type]}: {title}</u>\n'


def get_user_text(user):
  user, text = user.to_dict(), ''
  keys = ['id', 'first_name', 'last_name', 'username', 'language_code',
          'is_premium', 'is_bot']
  for key in keys:
    if key in user and user[key]:
      if key == 'username':
        val = '@' + str(user[key])
      elif key in ['is_premium', 'is_bot']:
        val = msg[lang()]['yes']
      else:
        val = str(user[key])
      text += f'<b>{msg[lang()][key]}:</b> {val}\n'
  if user['id'] < int(list(ages.keys())[-1]):
    rd_key = msg[lang()]["registration_date"]
    text += f'<b>{rd_key}:</b> {get_age(user["id"])}\n'
  return text


def get_member_text(member):
  text = f'<b>{msg[lang()]["status"]}:</b> {str(member.status)}\n'
  return text


async def get_user_photo(user):
  photo = None
  try:
    upp = await bot.get_user_profile_photos(user.id)
    if upp.total_count > 0:
      file_id = upp.photos[0][0].file_id
      file = await bot.get_file(file_id)
      photo = await bot.download_file(file.file_path)
  except asyncio_helper.ApiException:
    pass
  except UnboundLocalError:
    pass
  log_text = f'Member ID:{user.id} profile photo '
  if photo is None:
    log_text += 'is not available'
  else:
    log_text += 'downloaded successfully'
  logging.debug(log_text)
  return photo


async def send_message(user, chat_type, title):
  text = get_chat_title(chat_type, title)
  text += get_user_text(user)
  photo = await get_user_photo(user)
  uids = get_enabled_uids()
  for user_id in uids:
    if photo is not None:
      await bot.send_photo(user_id, photo, text)
    else:
      await bot.send_message(user_id, text)
    logging.debug('Message about new member ID:%d sent to user ID:%d',
                  user.id, user_id)


@bot.chat_member_handler()
async def message_chat_member(cmu):
  chat_type = 'channel' if cmu.chat.type == 'channel' else 'group'
  ids = get_ids(chat_type + 's')
  if cmu.chat.id not in ids:
    return
  new = cmu.new_chat_member
  logging.debug('%s "%s" member update: {\'new_chat_member\': %s, '
                '\'difference\': %s}', chat_type.capitalize(),
                cmu.chat.title, str(new), str(cmu.difference))
  if 'is_member' in cmu.difference \
      and cmu.difference['is_member'] == [False, True] \
      or 'status' in cmu.difference \
      and cmu.difference['status'][0] in ['left', 'kicked'] \
      and cmu.difference['status'][1] not in ['restricted', 'kicked', 'left']:
    logging.info('New member in %s "%s": %s', chat_type,
                 cmu.chat.title, str(new))
    await send_message(new.user, chat_type, cmu.chat.title)


@bot.message_handler(commands=['owner'], chat_types=['private'])
async def command_owner(message):
  args = message.text.split()[1:]
  if len(args) != 1:
    return
  chat = message.chat
  reg = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{16,20}$'
  pat = re.compile(reg)
  if re.search(pat, args[0]):
    salt = base64.b64decode(config['owner_pass_salt'].encode('ascii'))
    if not salt:
      salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', args[0].encode('utf-8'), salt, 100000)
    if not config['owner'] or check_owner(chat.id) \
        or key == base64.b64decode(config['owner_pass_hash'].encode('ascii')):
      config['owner_pass_hash'] = base64.b64encode(key).decode('ascii')
      config['owner_pass_salt'] = base64.b64encode(salt).decode('ascii')
      config['owner'] = get_owner(chat)
      save_file(CONFIG_FILE, config)
      await bot.send_message(message.chat.id, msg[lang()]['mess_owner_succ']
                             + msg[lang()]['mess_bot_help_tip'])
      logging.info('Owner ID:%d has been set successfully',
                   config['owner']['id'])
  elif not config['owner'] or check_owner(chat.id):
    await bot.send_message(message.chat.id, msg[lang()]['mess_owner_password'])


@bot.message_handler(commands=['group_add'],
                     chat_types=['group', 'supergroup'])
async def command_group_add(message):
  await check_owner_set(message.chat.id, False)
  if not check_owner(message.from_user.id):
    return
  gids = get_ids('groups')
  group_dict = {'id': message.chat.id, 'title': message.chat.title}
  if message.chat.id in gids:
    config['groups'][gids.index(message.chat.id)] = group_dict
  else:
    config['groups'].append(group_dict)
  save_file(CONFIG_FILE, config)
  await bot.send_message(message.chat.id, msg[lang()]['mess_group_added'])
  logging.info('Group "%s" added: %s', message.chat.title, str(group_dict))


@bot.message_handler(commands=['group_del'], chat_types=['private'])
async def command_group_del(message):
  await check_owner_set(message.chat.id, True)
  if not check_owner(message.chat.id):
    return
  args = message.text.split()[1:]
  if len(args) != 1:
    return
  chat_id = format_chat_id(args[0])
  found = False
  for index, group in enumerate(config['groups']):
    if str(group['id']) == chat_id:
      group_dict = group
      config['groups'].pop(index)
      save_file(CONFIG_FILE, config)
      await bot.send_message(message.chat.id,
                             msg[lang()]['mess_group_deleted'])
      logging.info('Group "%s" deleted: %s', group_dict['title'],
                   str(group_dict))
      found = True
      break

  if not found:
    await bot.send_message(message.chat.id,
                           msg[lang()]['mess_group_not_found'])


@bot.message_handler(commands=['group_list'], chat_types=['private'])
async def command_group_list(message):
  await check_owner_set(message.chat.id, True)
  if not check_owner(message.chat.id):
    return
  if config['groups']:
    text = f'<b>{msg[lang()]["mess_group_list"]}:</b>\n'
    for group in config['groups']:
      await update_chat(group, 'group')
      text += f'{group["id"]} ({group["title"]})\n'
    await bot.send_message(message.chat.id, text)
  else:
    await bot.send_message(message.chat.id, msg[lang()]['mess_group_empty'])


@bot.message_handler(commands=['channel_add'], chat_types=['private'])
async def command_channel_add(message):
  await check_owner_set(message.chat.id, True)
  if not check_owner(message.chat.id):
    return
  args = message.text.split()[1:]
  if len(args) != 1:
    return
  chat_id = format_chat_id(args[0])
  try:
    chat = await bot.get_chat(chat_id)
    cids = get_ids('channels')
    channel_dict = {'id': chat.id, 'title': chat.title}
    if chat.id in cids:
      config['channels'][cids.index(chat.id)] = channel_dict
    else:
      config['channels'].append(channel_dict)
    save_file(CONFIG_FILE, config)
    await bot.send_message(message.chat.id, msg[lang()]['mess_channel_added'])
    logging.info('Channel "%s" added: %s', chat.title, str(channel_dict))
  except asyncio_helper.ApiTelegramException:
    await bot.send_message(message.chat.id,
                           msg[lang()]['mess_channel_not_found'])


@bot.message_handler(commands=['channel_del'], chat_types=['private'])
async def command_channel_del(message):
  await check_owner_set(message.chat.id, True)
  if not check_owner(message.chat.id):
    return
  args = message.text.split()[1:]
  if len(args) != 1:
    return
  chat_id = format_chat_id(args[0])
  found = False
  for index, channel in enumerate(config['channels']):
    if str(channel['id']) == chat_id:
      channel_dict = channel
      config['channels'].pop(index)
      save_file(CONFIG_FILE, config)
      await bot.send_message(message.chat.id,
                             msg[lang()]['mess_channel_deleted'])
      logging.info('Channel "%s" deleted: %s', channel_dict['title'],
                   str(channel_dict))
      found = True
      break

  if not found:
    await bot.send_message(message.chat.id,
                           msg[lang()]['mess_channel_not_found'])


@bot.message_handler(commands=['channel_list'], chat_types=['private'])
async def command_channel_list(message):
  await check_owner_set(message.chat.id, True)
  if not check_owner(message.chat.id):
    return
  if config['channels']:
    text = f'<b>{msg[lang()]["mess_channel_list"]}:</b>\n'
    for channel in config['channels']:
      await update_chat(channel, 'channel')
      text += f'{channel["id"]} ({channel["title"]})\n'
    await bot.send_message(message.chat.id, text)
  else:
    await bot.send_message(message.chat.id, msg[lang()]['mess_channel_empty'])


@bot.message_handler(commands=['lang'], chat_types=['private'])
async def command_lang(message):
  if config['owner'] and not check_owner(message.chat.id):
    return
  lkeys = list(msg.keys())
  index = (lkeys.index(lang()) + 1) % len(lkeys)
  config['language'] = lkeys[index]
  save_file(CONFIG_FILE, config)
  await bot.send_message(message.chat.id, msg[lang()]['mess_change_lang'])
  logging.info('Language changed to "%s"', lang())


@bot.message_handler(commands=['user_add'], chat_types=['private'])
async def command_user_add(message):
  await check_owner_set(message.chat.id, True)
  if not config['owner']:
    return
  args = message.text.split()[1:]
  if check_owner(message.chat.id):
    if len(args) > 0:
      return
    password_generate()
    await bot.send_message(message.chat.id, msg[lang()]['mess_user_pass']
                           % (PASS_MAX_AGE, private['password']))
    private['timer'] = threading.Timer(PASS_MAX_AGE, password_reset)
    private['timer'].start()
  else:
    user = message.chat
    uids = get_ids('users')
    password = private['password']
    if user.id in uids or not password or len(args) != 1 \
        or password != args[0]:
      return
    password_reset()
    user_dict = get_user_dict(user.id, user.username, user.first_name,
                              user.last_name, True)
    config['users'].append(user_dict)
    save_file(CONFIG_FILE, config)
    await bot.send_message(message.chat.id, msg[lang()]['mess_user_added']
                           + msg[lang()]['mess_bot_help_tip'])
    logging.info('User ID:%d added: %s', user.id, str(user_dict))


@bot.message_handler(commands=['user_del'], chat_types=['private'])
async def command_user_del(message):
  await check_owner_set(message.chat.id, True)
  if not check_owner(message.chat.id):
    return
  args = message.text.split()[1:]
  if len(args) != 1:
    return
  uname = args[0][1:] if args[0][0] == '@' else args[0]
  if not uname:
    return
  found = False
  for index, user in enumerate(config['users']):
    if uname in {str(user['id']), user['username']}:
      user_dict = user
      config['users'].pop(index)
      save_file(CONFIG_FILE, config)
      await bot.send_message(message.chat.id, msg[lang()]['mess_user_deleted'])
      logging.info('User ID:%d deleted: %s', user_dict['id'], str(user_dict))
      found = True
      break

  if not found:
    await bot.send_message(message.chat.id, msg[lang()]['mess_user_not_found'])


@bot.message_handler(commands=['user_list'], chat_types=['private'])
async def command_user_list(message):
  await check_owner_set(message.chat.id, True)
  if not check_owner(message.chat.id):
    return
  if config['users']:
    text = f'<b>{msg[lang()]["mess_user_list"]}:</b>\n'
    for user in config['users']:
      await update_user(user)
      text += str(user['id'])
      if user['username']:
        text += f' @{user["username"]}'
      text += f' ({user["fullname"]})\n'
    await bot.send_message(message.chat.id, text)
  else:
    await bot.send_message(message.chat.id, msg[lang()]['mess_user_empty'])


async def process_chat_member(chat_id, user_id):

  async def check_chat(chat, chat_type, data):
    await update_chat(chat, chat_type)
    member = None
    try:
      member = await bot.get_chat_member(chat['id'], user_id)
    except asyncio_helper.ApiTelegramException:
      pass
    if member is not None:
      if data[1]:
        data[1] += ', '
      data[1] += f'{chat_type.capitalize()} "{chat["title"]}" ' \
          f'(ID:{chat["id"]}): {str(member)}'
      if not data[0]:
        data[0] = get_user_text(member.user)
        data[2] = await get_user_photo(member.user)
      data[0] += '\n' + get_chat_title(chat_type, chat["title"])
      data[0] += get_member_text(member)

  data = ['', '', None]
  for group in config['groups']:
    await check_chat(group, 'group', data)
  for channel in config['channels']:
    await check_chat(channel, 'channel', data)

  if data[0]:
    if data[2] is not None:
      await bot.send_photo(chat_id, data[2], data[0])
    else:
      await bot.send_message(chat_id, data[0])
  else:
    await bot.send_message(chat_id, msg[lang()]['mess_user_not_found'])
  logging.info('Getting chat member ID:%s info: [%s]', user_id, data[1])


async def process_chat(chat_id, chat):

  def format_line(key, val):
    if val:
      val = '@' + val if key == 'username' else val
      return f'<b>{msg[lang()][key]}:</b> {val}\n'
    return ''

  text = format_line('id', chat.id)
  text += format_line('title', chat.title)
  text += format_line('username', chat.username)
  text += format_line('type', chat.type)
  await bot.send_message(chat_id, text)
  logging.info('Getting chat ID:%s info: [%s]', chat.id, str(chat))


@bot.message_handler(commands=['member'], chat_types=['private'])
async def command_chat_member(message):
  await check_owner_set(message.chat.id, True)
  if not is_command_allow_user(message, True):
    return
  args = message.text.split()[1:]
  if len(args) != 1:
    return
  user_id = args[0][1:] if args[0][0] == '@' else args[0]
  if not user_id or not user_id.isdigit():
    return
  await process_chat_member(message.chat.id, user_id)


@bot.message_handler(func=lambda message: message.forward_from is not None
                     or message.forward_sender_name is not None
                     or message.forward_from_chat is not None,
                     chat_types=['private'],
                     content_types=util.content_type_media)
async def message_forward_from(message):
  await check_owner_set(message.chat.id, True)
  if not is_command_allow_user(message, True):
    return
  if message.forward_from is None:
    if message.forward_from_chat is not None:
      await process_chat(message.chat.id, message.forward_from_chat)
    else:
      await bot.send_message(message.chat.id,
                             msg[lang()]['mess_member_hidden'])
  else:
    await process_chat_member(message.chat.id, message.forward_from.id)


@bot.message_handler(commands=['help'], chat_types=['private'])
async def command_help(message):
  if not is_command_allow_user(message, False):
    return
  text = f'<b>{msg[lang()]["mess_bot_commands"]}:</b>\n'
  if not config['owner'] or check_owner(message.chat.id):
    text += msg[lang()]['mess_bot_help_owner']
  text += msg[lang()]['mess_bot_help_user']
  await bot.send_message(message.chat.id, text)


async def command_start_stop(message, value, key):

  def set_owner_value():
    res = message.chat.id == config['owner']['id']
    if res:
      config['owner']['enabled'] = value
    return res

  def set_user_value():
    res = message.chat.id in uids
    if res:
      index = uids.index(message.chat.id)
      config['users'][index]['enabled'] = value
    return res

  await check_owner_set(message.chat.id, True)
  if config['owner']:
    uids = get_ids('users')
    if set_owner_value():
      usr_msg = f'Owner ID:{message.chat.id}'
      set_user_value()
    elif set_user_value():
      usr_msg = f'User ID:{message.chat.id}'
    else:
      return
    save_file(CONFIG_FILE, config)
    await bot.send_message(message.chat.id,
                           msg[lang()][key] + msg[lang()]['mess_bot_help_tip'])
    com_msg = 'started' if value else 'stopped'
    logging.info('%s %s the bot', usr_msg, com_msg)


@bot.message_handler(commands=['start'], chat_types=['private'])
async def command_start(message):
  await command_start_stop(message, True, 'mess_bot_started')


@bot.message_handler(commands=['stop'], chat_types=['private'])
async def command_stop(message):
  await command_start_stop(message, False, 'mess_bot_stopped')


class DebugLogMiddleware(BaseMiddleware):
  def __init__(self):
    self.update_types = ['message']

  async def pre_process(self, message, data):
    if message.chat.type != 'private':
      return
    if message.text is not None:
      cmd = message.text.split()
      if 'owner' in cmd[0]:
        text = cmd[0]
        if len(cmd) > 1:
          text += ' <PASSWORD>'
      else:
        text = message.text.replace('\n', ' ')
    else:
      text = message.content_type
    user_id = message.from_user.id if message.from_user is not None else None
    logging.debug('User ID:%s chat ID:%d sent a message "%s". '
                  'User details: %s', str(user_id), message.chat.id, text,
                  str(message.from_user))

  async def post_process(self, message, data, exception):
    pass


def setup_logging():
  logging.basicConfig(handlers=[
      logging.FileHandler(filename=LOG_FILE, encoding='utf-8')],
      format='%(asctime)s - %(levelname)s - %(message)s', level=LOG_LEVEL)
  if LOG_LEVEL == logging.DEBUG:
    bot.setup_middleware(DebugLogMiddleware())
  logging.info('%s version %s has started', NAME, VERSION)
  logging.debug('Python version: %s', sys.version.replace('\n', ''))


def main():
  setup_logging()
  if not config['token']:
    logging.error('The bot\'s authorization token is not set in "%s"',
                  CONFIG_FILE)
    sys.exit(1)
  asyncio.run(bot.infinity_polling(allowed_updates=["message", "chat_member"]))


if __name__ == '__main__':
  main()
