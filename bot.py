"""
Telegram bot working in groups. Sends available information about new group
members to group administrators.
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
    sys.exit()
  return data


def save_file(filename, data):
  try:
    with open(filename, 'w', encoding="utf-8") as file:
      file.write(json.dumps(data, indent=2))
  except OSError:
    print('Could not save file:', filename)
    sys.exit()


NAME = 'Inspector Bot'
VERSION = '1.11'
CONFIG_FILE = 'config.json'
AGES_FILE = 'ages.json'
config = load_file(CONFIG_FILE)
ages = load_file(AGES_FILE)
bot = AsyncTeleBot(config['token'], parse_mode='HTML')
LOG_FILE = os.path.splitext(os.path.basename(__file__))[0] + '.log'
LOG_LEVEL = logging.INFO


def lang():
  return config['language']


def check_owner(user_id):
  return user_id == config['owner_id']


async def check_owner_set(chat_id, show_tip):
  if not config['owner_id']:
    text = msg[lang()]['mess_owner_not_set']
    if show_tip:
      text += msg[lang()]['mess_bot_help_tip']
    await bot.send_message(chat_id, text)


def get_ids(section):
  return [x['id'] for x in config[section]]


def get_enabled_uids():
  uids = [config['owner_id'], ] if config['owner_enabled'] else []
  for user in config['users']:
    if user['enabled'] and user['id'] not in uids:
      uids.append(user['id'])
  return uids


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


def is_command_allow_user(message, owner_set):
  res = not owner_set or config['owner_id']
  if res and config['owner_id']:
    uids = [config['owner_id'], ] + get_ids('users')
    res = message.chat.id in uids
  return res


async def update_group(group):
  try:
    chat = await bot.get_chat(group['id'])
    if group['title'] != chat.title:
      group['title'] = chat.title
      save_file(CONFIG_FILE, config)
      logging.debug('Group ID:%d data updated: %s', group['id'], str(group))
  except asyncio_helper.ApiTelegramException:
    pass


async def update_user(user):
  for group in config['groups']:
    try:
      member = await bot.get_chat_member(group['id'], user['id'])
      if user['username'] != member.user.username \
          or user['fullname'] != member.user.full_name:
        user['username'] = member.user.username
        user['fullname'] = member.user.full_name
        save_file(CONFIG_FILE, config)
        logging.debug('User ID:%d data updated: %s', user['id'], str(user))
      break
    except asyncio_helper.ApiTelegramException:
      pass


def get_user_text(user):
  user, text = user.to_dict(), ''
  keys = ['id', 'first_name', 'last_name', 'username', 'language_code',
          'is_premium']
  for key in keys:
    if key in user and not user[key] is None:
      if key == 'username':
        val = '@' + str(user[key])
      elif key == 'is_premium' and user[key]:
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


async def send_message(user, title):
  text = f'<u>{title}</u>\n' if title else ''
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
async def message_chat_member(message):
  gids = get_ids('groups')
  if message.chat.id not in gids:
    return
  new = message.new_chat_member
  logging.debug('Chat "%s" member update: {\'new_chat_member\': %s, '
                '\'difference\': %s}', message.chat.title, str(new),
                str(message.difference))
  if 'is_member' in message.difference \
      and message.difference['is_member'] == [False, True] \
      or 'status' in message.difference \
      and message.difference['status'][0] == 'left' \
      and message.difference['status'][1] not in ['restricted', 'kicked']:
    logging.info('New member in group "%s": %s',
                  message.chat.title, str(new))
    title = message.chat.title if len(config['groups']) > 1 else ''
    await send_message(new.user, title)


@bot.message_handler(commands=['set_owner'], chat_types=['private'])
async def command_set_owner(message):
  args = message.text.split()[1:]
  if len(args) != 1:
    return
  reg = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{16,20}$'
  pat = re.compile(reg)
  if re.search(pat, args[0]):
    salt = base64.b64decode(config['owner_pass_salt'].encode('ascii'))
    if not salt:
      salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', args[0].encode('utf-8'), salt, 100000)
    if check_owner(message.chat.id) or not config['owner_pass_hash'] \
        or key == base64.b64decode(config['owner_pass_hash'].encode('ascii')):
      config['owner_pass_hash'] = base64.b64encode(key).decode('ascii')
      config['owner_pass_salt'] = base64.b64encode(salt).decode('ascii')
      config['owner_id'] = message.chat.id
      save_file(CONFIG_FILE, config)
      await bot.send_message(message.chat.id, msg[lang()]['mess_owner_succ']
                             + msg[lang()]['mess_bot_help_tip'])
      logging.info('Owner ID:%d has been set successfully', config['owner_id'])
  else:
    await bot.send_message(message.chat.id, msg[lang()]['mess_password'])


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


@bot.message_handler(commands=['group_del'])
async def command_group_del(message):
  private = message.chat.type == 'private'
  await check_owner_set(message.chat.id, private)
  if not check_owner(message.from_user.id):
    return
  args = message.text.split()[1:]
  if not private:
    if args:
      return
    chat_id = str(message.chat.id)
  else:
    if len(args) != 1:
      return
    chat_id = args[0]
    chat_id = chat_id[1:] if chat_id[0] == '@' else chat_id
    chat_id = '-' + chat_id if not chat_id or chat_id[0] != '-' else chat_id
    if len(chat_id) < 2:
      return

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
      await update_group(group)
      text += f'{group["id"]} ({group["title"]})\n'
    await bot.send_message(message.chat.id, text)
  else:
    await bot.send_message(message.chat.id, msg[lang()]['mess_group_empty'])


@bot.message_handler(commands=['lang'], chat_types=['private'])
async def command_lang(message):
  if config['owner_id'] and not check_owner(message.chat.id):
    return
  lkeys = list(msg.keys())
  index = (lkeys.index(lang()) + 1) % len(lkeys)
  config['language'] = lkeys[index]
  save_file(CONFIG_FILE, config)
  await bot.send_message(message.chat.id, msg[lang()]['mess_change_lang'])
  logging.info('Language changed to "%s"', lang())


@bot.message_handler(commands=['user_add'], chat_types=['group', 'supergroup'])
async def command_user_add(message):
  await check_owner_set(message.chat.id, False)
  if not check_owner(message.from_user.id):
    return
  args = message.text.split()[1:]
  if args or message.reply_to_message is None \
      or message.reply_to_message.from_user.is_bot:
    return
  user = message.reply_to_message.from_user
  user_id = user.id
  username = user.username if user.username and user.username is not None \
      else ''
  fullname = ' '.join(filter(None, (user.first_name, user.last_name)))
  uids = get_ids('users')
  user_dict = {'id': user_id, 'username': username, 'fullname': fullname,
               'enabled': True}
  if user_id in uids:
    config['users'][uids.index(user_id)] = user_dict
  else:
    config['users'].append(user_dict)
  save_file(CONFIG_FILE, config)
  await bot.send_message(message.chat.id, msg[lang()]['mess_user_added'])
  logging.info('User ID:%d added: %s', user_id, str(user_dict))


@bot.message_handler(commands=['user_del'])
async def command_user_del(message):
  private = message.chat.type == 'private'
  await check_owner_set(message.chat.id, private)
  if not check_owner(message.from_user.id):
    return
  args = message.text.split()[1:]
  if not private:
    if args or message.reply_to_message is None \
        or message.reply_to_message.from_user.is_bot:
      return
    uname, reply = message.reply_to_message.from_user.id, True
  else:
    if len(args) != 1:
      return
    uname = args[0][1:] if args[0][0] == '@' else args[0]
    if not uname:
      return
    reply = False

  found = False
  for index, user in enumerate(config['users']):
    if reply:
      update = user['id'] == uname
    else:
      update = uname in {str(user['id']), user['username']}
    if update:
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
  text, log_text, photo = '', '', None
  for group in config['groups']:
    await update_group(group)
    member = None
    try:
      member = await bot.get_chat_member(group['id'], user_id)
    except asyncio_helper.ApiTelegramException:
      pass
    if member is not None:
      if log_text:
        log_text += ', '
      log_text += f'Group "{group["title"]}" (ID:{group["id"]}): ' \
          f'{str(member)}'
      if not text:
        text = get_user_text(member.user)
        photo = await get_user_photo(member.user)
      text += f'\n<u>{group["title"]}</u>\n'
      text += get_member_text(member)

  if text:
    if photo is not None:
      await bot.send_photo(chat_id, photo, text)
    else:
      await bot.send_message(chat_id, text)
  else:
    await bot.send_message(chat_id, msg[lang()]['mess_user_not_found'])
  logging.info('Getting chat member ID:%s info: [%s]', user_id, log_text)


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
                     or message.forward_sender_name is not None,
                     chat_types=['private'],
                     content_types=util.content_type_media)
async def message_forward_from(message):
  await check_owner_set(message.chat.id, True)
  if not is_command_allow_user(message, True):
    return
  if message.forward_from is None:
    await bot.send_message(message.chat.id, msg[lang()]['mess_member_hidden'])
  else:
    await process_chat_member(message.chat.id, message.forward_from.id)


@bot.message_handler(commands=['help'], chat_types=['private'])
async def command_help(message):
  if not is_command_allow_user(message, False):
    return
  text = f'<b>{msg[lang()]["mess_bot_commands"]}:</b>\n'
  if not config['owner_id'] or check_owner(message.chat.id):
    text += msg[lang()]['mess_bot_help_owner']
  text += msg[lang()]['mess_bot_help_user']
  await bot.send_message(message.chat.id, text)


async def command_start_stop(message, value, key):

  def set_owner_value():
    res = message.chat.id == config['owner_id']
    if res:
      config['owner_enabled'] = value
    return res

  def set_user_value():
    res = message.chat.id in uids
    if res:
      index = uids.index(message.chat.id)
      config['users'][index]['enabled'] = value
    return res

  await check_owner_set(message.chat.id, True)
  if config['owner_id']:
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
        text = message.text
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
  asyncio.run(bot.infinity_polling(allowed_updates=util.update_types))


if __name__ == '__main__':
  main()
