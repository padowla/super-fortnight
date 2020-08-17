# -*- coding: utf-8 -*-


'''
    Made with API from telegram-bot-api installed with pip...
    https://python-telegram-bot.org/
'''

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext.dispatcher import run_async
from telegram import MessageEntity
import time, threading
from telegram.ext import BaseFilter
from telegram import ChatAction
import paramiko


##                                   GLOBAL VARIABLES                                              ##
reply_kb_markup = None
inline_reply_markup = None
IP_pfSense = "192.168.1.3"
username_pfSense = "root"
pwd_pfSense = "pfsense"


##                                   CUSTOM FILTERS                                                ##
class FilterKeyboardListRules(BaseFilter):
    
    def filter(self,message):
        
        return "List rules" in message.text


class FilterKeyboardShowActions(BaseFilter):

    def filter(self,message):

        return "Show actions" in message.text



##                                   GLOBAL FUNCTIONS                                               ##



def exec_command(command_pfSense):
    
    global username_pfSense
    global pwd_pfSense
    global IP_pfSense

    result = None
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(IP_pfSense, username=username_pfSense, password=pwd_pfSense)

    stdin, stdout, stderr = client.exec_command(command_pfSense)
    
    
    firstline = stdout.readlines()[0].rstrip()
    
    client.close()

    return firstline
        


def list_rules(update, context):
    print("LIST RULES")
    exec_command("/usr/local/bin/php /root/script.php enable")
    output = "rules enabled"
    context.bot.send_message(chat_id=update.effective_chat.id, text=output, reply_markup=reply_kb_markup)
    


def show_actions(update, context):
    
    print("SHOW ACTIONS")
    update.message.reply_text('Choose action:', reply_markup=inline_reply_markup)



def open_netA(update,context):

    output = None
    result = exec_command("/usr/local/bin/php /root/handleNetA.php disable && echo $?")
    print(f"result ==> {result}")
    if(result == "0"):
        output = "netA is now open"
    else:
        output = "An error occurred"

    context.bot.send_message(chat_id=update.effective_chat.id, text=output, reply_markup=reply_kb_markup)



def close_netA(update,context):
    output = None
    result = exec_command("/usr/local/bin/php /root/handleNetA.php enable && echo $?")
    print(f"result ==> {result}")
    if(result == "0"):
        output = "netA is now closed"
    else:
        output = "An error occurred"

    context.bot.send_message(chat_id=update.effective_chat.id, text=output, reply_markup=reply_kb_markup)



def unknown_command(update,context):
    #Alcuni utenti confusi potrebbero provare ad inviare comandi al bot che non può comprendere in quanto non aggiunti al dispatcher
    #Dunque è possibile usare un MessageHandler con il filtro "command" per rispondere a tutti i comandi che non sono riconosciuti dai precedenti handler
    #Tale Handler deve essere aggiunto come ultimo altrimenti verrebbe attivato prima che CommandHandler abbia la possibilità di
    #poter esaminare l'aggiornamento. Una volta gestito infatti un aggiornamento tutti gli altri gestori vengono ignorati
    #Per aggirare questo fenomeno è possibile  passare l'argomento "group" nel metodo add_handler con un valore intero diverso da 0
    context.bot.send_message(chat_id=update.effective_chat.id,text="Scusami ma non capisco ciò che mi chiedi...")


def unknown_text(update,context):
    #This callback handle unknown text/command
    context.bot.send_message(chat_id=update.effective_chat.id,text="⚠⚠⚠ Text or command not valid  ⚠⚠⚠")

def clear_env():
    WAIT_SECONDS = 86400 #il numero di secondi in un giorno
    with open(PATH_LOG,'w'):
        pass
    logging.info("ENVIRONMENT CLEARED")
    threading.Timer(WAIT_SECONDS,clear_env).start() #after WAIT_SECONDS start thread that clean log file 

#GLOBAL PATH
PATH_API='/home/centuser/ZabbixServerThesisBot/api_telegram'
PATH_LOG='/home/centuser/ZabbixServerThesisBot/mylog'

#_________________________________________________________________________________________________________
def start(update, context):
   
    inline_keyboard_actions = [
                [InlineKeyboardButton("Open netA", callback_data='open_netA'),
                 InlineKeyboardButton("Close netA", callback_data='close_netA')],
                ]
    

    main_menu_keyboard = [[KeyboardButton("List rules")],[KeyboardButton("Show actions")]]
    
    global inline_reply_markup
    inline_reply_markup = InlineKeyboardMarkup(inline_keyboard_actions)
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Monitor your network with this Bot!")
    
    #Modify the global variable
    global reply_kb_markup
    reply_kb_markup = ReplyKeyboardMarkup(main_menu_keyboard)
    
    # Send the message with menu
    context.bot.send_message(chat_id=update.effective_chat.id, text="Use keyboard to make your job easier...", reply_markup=reply_kb_markup) 

#__________________________________________________________________________________________________________



def button(update, context):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text="Selected option: {}".format(query.data))

    if(query.data == "open_netA"):
        open_netA(update,context)
    elif(query.data == "close_netA"):
        close_netA(update,context)



def main():

    #                                          __________________________________________________
    #Read token from api_telegram file

    with open(PATH_API,"r") as file:

        TOKEN=file.read().replace("\n","") #replace is necessary because at the end of file there is a "\n" to delete


    #                                          ___________________________________________________
    #Initialize logging file
    logging.basicConfig(filename=PATH_LOG,filemode="a",format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",level=logging.INFO)


    #                                          ___________________________________________________
    #Initialize filters class
    filter_keyboard_list_rules = FilterKeyboardListRules()
    filter_keyboard_show_actions = FilterKeyboardShowActions()
    
    #                                          ___________________________________________________
    #Instantiate the Updater
    updater = Updater(token=TOKEN,use_context=True)

    #                                          ___________________________________________________
    #Initialize handlers

    #    (1) "/start" Handler   #
    updater.dispatcher.add_handler(CommandHandler("start", start))

    #    (2) "List rules" Handler #
    updater.dispatcher.add_handler(MessageHandler(Filters.text & filter_keyboard_list_rules, list_rules))

    #    (3) "Show actions" Handler #
    updater.dispatcher.add_handler(MessageHandler(Filters.text & filter_keyboard_show_actions, show_actions))

    #    (4)    #
    #unknown_text_handler = MessageHandler(Filters.text,unknown_text)
    #updater.dispatcher.add_handler(unknown_text_handler)
    
    # (5) #
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    #   !!!!!!  L'HANDLER UNKNOWN COME ULTIMO !!!!!          #
    unknown_command_handler = MessageHandler(Filters.command,unknown_command)
    updater.dispatcher.add_handler(unknown_command_handler)
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#



    # Start the Bot
    updater.start_polling()

    clear_env() #clean log file every <WAIT_SECONDS> seconds
    logging.info("SERVER STARTED")
    updater.idle() #Run the bot until the user presses Ctrl-C or the process receives SIGINT,
                   #SIGTERM or SIGABRT



if __name__ == '__main__':
    main()

