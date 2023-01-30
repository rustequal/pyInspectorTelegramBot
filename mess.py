"""Text Messages"""

msg = {
  'en': {'id': 'ID',
         'first_name': 'First Name',
         'last_name': 'Last Name',
         'title': 'Title',
         'type': 'Type',
         'username': 'Username',
         'language_code': 'Language',
         'is_premium': 'Premium',
         'is_bot': 'Bot',
         'status': 'Status',
         'registration_date': 'Registration Date',
         'group': 'Group',
         'channel': 'Channel',
         'before': 'before ',
         'after': 'after ',
         'yes': 'yes',
         'mess_password':
            'The password must contain numbers, uppercase and lowercase ' \
            'letters. The password must be between 16 and 20 characters ' \
            'long.',
          'mess_owner_succ': 'The new owner has been set successfully. ' \
            'Save your chosen password and delete the message with it above',
          'mess_owner_not_set': 'You must first set the owner',
          'mess_group_not_found': 'Group not found',
          'mess_group_added': 'The group was added successfully',
          'mess_group_deleted': 'The group was deleted successfully',
          'mess_group_empty': 'Group settings are not set',
          'mess_group_list': 'Groups',
          'mess_channel_not_found': 'Channel not found',
          'mess_channel_added': 'The channel was added successfully',
          'mess_channel_deleted': 'The channel was deleted successfully',
          'mess_channel_empty': 'Channel settings are not set',
          'mess_channel_list': 'Channels',
          'mess_change_lang': 'Language switched to English',
          'mess_user_not_found': 'User not found',
          'mess_user_added': 'User added successfully',
          'mess_user_deleted': 'User deleted successfully',
          'mess_user_empty': 'No users added',
          'mess_user_list': 'Users',
          'mess_member_hidden': 'The account was hidden by the user',
          'mess_bot_commands': 'Bot commands',
          'mess_bot_started': 'The bot has started and will send messages',
          'mess_bot_stopped': 'The bot has been stopped and will not send ' \
              'messages',
          'mess_bot_help_tip': '.\nFor help, enter the command /help',
          'mess_bot_help_owner': '/set_owner <code>password</code> - set ' \
              'owner and password\n' \
              '/group_add - adding a group (use in group chat)\n' \
              '/group_del <code>id</code> - deleting a group from list\n' \
              '/group_list - show list of groups\n' \
              '/channel_add <code>id</code> - adding a channel\n' \
              '/channel_del <code>id</code> - deleting a channel from list\n' \
              '/channel_list - show list of channels\n' \
              '/lang - change the bot language\n' \
              '/user_add - adding a user (reply to user in group chat)\n' \
              '/user_del <code>user</code> - deleting a user\n' \
              '/user_list - show list of users\n',
          'mess_bot_help_user': '/start - start the bot\n' \
              '/stop - stop the bot\n' \
              '/member <code>id</code> - show info about chat member\n' \
              '/help - show list of bot commands'
          },

  'ru': {'id': 'ID',
         'first_name': 'Имя',
         'last_name': 'Фамилия',
         'title': 'Название',
         'type': 'Тип',
         'username': 'Имя пользователя',
         'language_code': 'Язык',
         'is_premium': 'Премиум',
         'is_bot': 'Бот',
         'status': 'Статус',
         'registration_date': 'Дата регистрации',
         'group': 'Группа',
         'channel': 'Канал',
         'before': 'до ',
         'after': 'после ',
         'yes': 'да',
         'mess_password':
            'Пароль должен содержать цифры, заглавные и строчные буквы. ' \
            'Длина пароля должна быть от 16 до 20 символов.',
          'mess_owner_succ': 'Новый владелец задан успешно. ' \
            'Сохраните выбранный пароль и удалите сообщение с ним выше',
          'mess_owner_not_set': 'Необходимо сначала задать владельца',
          'mess_group_not_found': 'Группа не найдена',
          'mess_group_added': 'Группа добавлена успешно',
          'mess_group_deleted': 'Группа удалена успешно',
          'mess_group_empty': 'Настройки групп не заданы',
          'mess_group_list': 'Группы',
          'mess_channel_not_found': 'Канал не найден',
          'mess_channel_added': 'Канал добавлен успешно',
          'mess_channel_deleted': 'Канал удален успешно',
          'mess_channel_empty': 'Настройки каналов не заданы',
          'mess_channel_list': 'Каналы',
          'mess_change_lang': 'Язык переключен на Русский',
          'mess_user_not_found': 'Пользователь не найден',
          'mess_user_added': 'Пользователь добавлен успешно',
          'mess_user_deleted': 'Пользователь удален успешно',
          'mess_user_empty': 'Пользователи не добавлены',
          'mess_user_list': 'Пользователи',
          'mess_member_hidden': 'Аккаунт скрыт пользователем',
          'mess_bot_commands': 'Команды бота',
          'mess_bot_started': 'Бот запущен и будет присылать сообщения',
          'mess_bot_stopped': 'Бот остановлен и не будет присылать сообщения',
          'mess_bot_help_tip': '.\nДля справки введите команду /help',
          'mess_bot_help_owner': '/set_owner <code>пароль</code> - задать' \
              ' владельца и его пароль\n' \
              '/group_add - добавить группу (выполняется в чате группы)\n' \
              '/group_del <code>id</code> - удалить группу из списка\n' \
              '/group_list - вывести список групп\n' \
              '/channel_add <code>id</code> - добавить канал\n' \
              '/channel_del <code>id</code> - удалить канал из списка\n' \
              '/channel_list - вывести список каналов\n' \
              '/lang - сменить язык бота\n' \
              '/user_add - добавить пользователя ' \
              '(ответ пользователю в чате группы)\n' \
              '/user_del <code>пользователь</code> - удалить пользователя\n' \
              '/user_list - вывести список пользователей\n',
          'mess_bot_help_user': '/start - запустить бота\n' \
              '/stop - остановить бота\n' \
              '/member <code>id</code> - вывести информацию об участнике\n' \
              '/help - показать список команд бота'
          }
}
