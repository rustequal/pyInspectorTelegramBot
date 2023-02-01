# Changelog

All notable changes to this project will be documented in this file.

## [1.14] - 2023-02-01

- Changed the command "/user_add". Now, in order to create a new user, the owner must create a password and forward it to the new user. This eliminates the need to find a new user in the Telegram group if the bot is used only for working in channels.
- The logic of transferring the owner's rights has been changed. Now, when the owner's rights are transferred, the old owner becomes a regular user, and the new owner is removed from the users, if he was one.
- The format of the configuration file "config.json" has been changed for optimal implementation of the previous function.
- The "/set_owner" command has been renamed to "/owner" for simplicity.
- Minor fixes and optimizations

## [1.13] - 2023-01-30

- Added a patch to fix the "pyTelegramBotAPI 4.9.0" library [bug](https://github.com/eternnoir/pyTelegramBotAPI/issues/1896)
- Minor fixes and optimizations

## [1.12] - 2023-01-30

- Added support for Telegram channels. Now the bot can be added to the channel administrators and receive information about new and existing channel members. Added commands "/channel_add", "/channel_del" and "/channel_list". See the "Usage" section  for more information.
- Now you can get information about groups and channels if their messages are copied to bot's chat. You can get the following information: ID, Title, Username and Type.
- If a member of groups and channels is a bot, then this information is now displayed in the member summary.

## [1.11] - 2023-01-29

- The bot has been translated to asynchronous algorithms and the AIOHTTP library. Tests under heavy load show a significant gain in performance, up to 5 times faster.
- The log file is now saved in UTF-8 encoding.

## [1.10] - 2023-01-28

- Minor fixes and optimizations

## [1.08] - 2023-01-26

- The algorithm for determining new members of groups has been transferred to the "chat_member_handler" call. It is more reliable than identifying members by system chat messages.
- Now you can send any media messages (pictures, animations, etc.) to the bot's chat, not just text messages.

## [1.07] - 2023-01-24

- Minor fixes and optimizations

## [1.06] - 2023-01-23

- The command "/chat_member" is renamed to "/member" for simplicity.

## [1.05] - 2023-01-22

- Added the ability to determine information about a group member by forwarding his message to the bot's chat. If the member's information is hidden by his privacy settings, then this method will not work.

## [1.03] - 2023-01-22

- Added the command "/chat_member" to display summary information about a group member.
