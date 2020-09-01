# super-fortnight

> Telegram bot in Python to remotely control pfsense.

> The development of this telegram bot is part of a three-year thesis project in Computer Engineering 
  on the remote control of the pfSense firewall based on the notifications sent by Zabbix via the bot to the net / sys admin.
  
> python-telegram-bot, pfsense, firewall, telegram, bot


(https://github.com/lilpilgit/super-fortnight/blob/master/image/screen_start_bot.png)()]


- This is a simple PoC of Telegram Bot. In this case we use two custom PHP script running on pfsense (<a href="https://github.com/lilpilgit/super-fortnight/blob/master/handleNetA.php" target="_blank">**script 1**</a> & <a href="https://github.com/lilpilgit/super-fortnight/blob/master/readRules.php" target="_blank">**script 2**</a> ) to enable/disable remotely some Firewall rules or list current firewall rules.

**PoC**
(https://github.com/lilpilgit/super-fortnight/blob/master/image/output_screerecord.gif)

## Installation

```bash

pip3 -r install requirements.txt
```



