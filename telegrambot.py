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
import json
from emoji import emojize


##                                   GLOBAL VARIABLES                                              ##
reply_kb_markup = None
inline_reply_markup_actions = None
inline_reply_markup_rules = None
ip_pfSense = "192.168.1.61"
username_pfSense = "root"
pwd_pfSense = "pfsense"
### EMOJI ###
red_exclamation_mark = emojize(":exclamation:", use_aliases=True) 
white_check_mark = emojize(":white_check_mark:", use_aliases=True)
red_cross_block = emojize(":x:", use_aliases=True)
raised_hand = emojize(":raised_hand:", use_aliases=True)
warning = emojize(":warning:", use_aliases=True)
#############

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
    global ip_pfSense

    result = None
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip_pfSense, username=username_pfSense, password=pwd_pfSense)

    stdin, stdout, stderr = client.exec_command(command_pfSense)
    
    
    firstline = stdout.readlines()[0].rstrip()
    
    client.close()

    return firstline
        


def list_rules(update, context):

    print("LIST RULES")
    update.message.reply_text('Choose interface:', reply_markup=inline_reply_markup_rules)



def parse_rule(json_rule):
    
    rule_enabled = "" #text for disabled or enabled rule
    rule_tracker = "" #text for rule's id tracker
    rule_type = None #emoji for the rule's type
    rule_address_family = "" #text for version of IP protocol (IPv4,IPv6,IPv4+6)
    rule_protocol = "" #text for type of protocol (TCP,UDP,TCP/UDP,ICMP...)
    rule_source_addr = "" #text for source address of rule
    rule_source_port = "" #text for source port of rule
    rule_dest_addr = "" #text for destination address of rule
    rule_dest_port = "" #text for destination port of rule
    rule_description = "" #text for description of rule

    #Identify if rule is enabled or not
    if("disabled" not in json_rule): #"disabled":""
        rule_enabled = "YES"
    else:
        rule_enabled = warning + "NO" + warning 

    #Identify id tracker of rule:
    rule_tracker = json_rule['tracker']


    #Identify type of rule:
    if(json_rule['type'] == "pass"):
        rule_type = white_check_mark
    elif(json_rule['type'] == "block"):
        rule_type = red_cross_block
    elif(json_rule['type'] == "reject"):
        rule_type = raised_hand
   

    #Identify address family version:
    if(json_rule['ipprotocol'] == "inet"):
        rule_ipprot = "ip4"
    elif(json_rule['ipprotocol'] == "inet6"):
        rule_ipprot = "ip6"
    elif(json_rule['ipprotocol'] == "inet46"):
        rule_ipprot = "ip4+6"
   

    #Identify type of protocol ("protocol": is present only if is different from "Any"):
    if("protocol" in json_rule):
        rule_protocol = json_rule['protocol']
    else:
        rule_protocol = "Any"
   

    #Identify source address:
    if("network" in json_rule['source']): #ex: "source":{"network":"wan"} ==> WAN net or "source":{"network":"lanip"} ==> LAN ip
        if("ip" in json_rule['source']['network']):
            rule_source_addr = json_rule['source']['network'].replace(json_rule['source']['network'][-2:],'').upper() + " ip" #extract interface name and add "ip"
        else:
            rule_source_addr = json_rule['source']['network'].upper() + " net"
    elif("any" in json_rule['source']): #ex: "source":{"any":""}
        rule_source_addr = "Any"
    elif("address" in json_rule['source']): #ex: "source":{"address":"alias or ip"} or for net "source":{"address":"56.56.56.56\/23"}
        rule_source_addr = json_rule['source']['address'].replace('\\','') #replace is for net like 1.1.1.1\/32
    else:
        rule_source_addr = json_rule['source']
    
    if("not" in json_rule['source']): #ex: "source":{"network":"lan","not":""} there's "not" ==> Invert match checkbox checked in frontend
        rule_source_addr = red_exclamation_mark + rule_source_addr #concat "!"


    #Identify source port ( or range of source ports), only if is present in JSON "protocol":"tcp\/udp" or "protocol":"tcp" or "protocol":"udp" ):
    if("port" in json_rule['source']):
        if("-" in json_rule['source']['port']): #it's a range of ports, ex: "source":{"network":"opt1ip","port":"33-78"}
            splitted_ports = json_rule['source']['port'].split("-")
            rule_source_port = "from " + splitted_ports[0] + " to " + splitted_ports[1]
        else: #it's a single port
            rule_source_port = json_rule['source']['port']
    else:
        rule_source_port = "*"


    #Identify destination address: 
    if("network" in json_rule['destination']): #ex: "destination":{"network":"wan"} ==> WAN net or "destination":{"network":"lanip"} ==> LAN ip
        if("ip" in json_rule['destination']['network']):
            rule_dest_addr = json_rule['destination']['network'].replace(json_rule['destination']['network'][-2:],'').upper() + " ip" #extract interface name and add "ip"
        elif("(self)" in json_rule['destination']['network']): #ex: "destination":{"network":"(self)"}
            rule_dest_addr = "This Firewall"
        else:
            rule_dest_addr = json_rule['destination']['network'].upper() + " net"
    elif("any" in json_rule['destination']): #ex: "destination":{"any":""}
        rule_dest_addr = "Any"
    elif("address" in json_rule['destination']): #ex: "destination":{"address":"alias or ip"} or for net "destination":{"address":"56.56.56.56\/23"}
        rule_dest_addr = json_rule['destination']['address'].replace('\\','') #replace is for net like 1.1.1.1\/32
    else:
        rule_dest_addr = json_rule['destination']
    
    if("not" in json_rule['destination']): #ex: "destination":{"network":"lan","not":""} there's "not" ==> Invert match checkbox checked in frontend
        rule_dest_addr = red_exclamation_mark + rule_dest_addr #concat "!"

  
    #Identify destination port ( or range of destination ports), only if is present in JSON "protocol":"tcp\/udp" or "protocol":"tcp" or "protocol":"udp" ):
    if("port" in json_rule['destination']):
        if("-" in json_rule['destination']['port']): #it's a range of ports, ex: "destination":{"network":"opt1ip","port":"33-78"}
            splitted_ports = json_rule['destination']['port'].split("-")
            rule_dest_port = "from " + splitted_ports[0] + " to " + splitted_ports[1]
        else: #it's a single port
            rule_dest_port = json_rule['destination']['port']
    else:
        rule_dest_port = "*"

    #Identify description 
    if(not json_rule['descr']): #empty string in Python are false
        rule_description = "no description"
    else:
        rule_description = json_rule['descr']


    return '''
tracker: {rule_tracker}
enabled: {rule_enabled}
type: {rule_type}
IP address family: {rule_ipprot}
protocol: {rule_protocol}
Source Address: {rule_source_addr}
Source Port: {rule_source_port}
Destination Address: {rule_dest_addr}
Destination Port: {rule_dest_port}
Description: {rule_description}
           '''.format(rule_tracker=rule_tracker,
                      rule_enabled=rule_enabled,
                      rule_type=rule_type,
                      rule_ipprot=rule_ipprot,
                      rule_protocol=rule_protocol,
                      rule_source_addr=rule_source_addr,
                      rule_source_port=rule_source_port,
                      rule_dest_addr=rule_dest_addr,
                      rule_dest_port=rule_dest_port,
                      rule_description=rule_description
                      )



def fetch_rules(update, context, interface):
    output = None
    JSONrules = None
    JSONstring = exec_command(f"/usr/local/bin/php /root/readRules.php {interface}")
    result = exec_command("echo $?")
    
    if(result == "0"):
        #output = "JSON created"
        JSONrules = json.loads(JSONstring)
        print(JSONrules)
    else:
        pass
        #output = "An error occurred"
    print(result)
    return JSONrules
    
def show_rules(update, context, interface):
    JSONrules = fetch_rules(update, context, interface)

    for rule in JSONrules:
        context.bot.send_message(chat_id=update.effective_chat.id, text=parse_rule(rule), reply_markup=reply_kb_markup)


def show_actions(update, context):
    
    print("SHOW ACTIONS")
    update.message.reply_text('Choose action:', reply_markup=inline_reply_markup_actions)



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
    #Alcuni utenti confusi potrebbero provare ad inviare comandi al bot che non puo' comprendere in quanto non aggiunti al dispatcher
    #Dunque e' possibile usare un MessageHandler con il filtro "command" per rispondere a tutti i comandi che non sono riconosciuti dai precedenti handler
    #Tale Handler deve essere aggiunto come ultimo altrimenti verrebbe attivato prima che CommandHandler abbia la possibilita'� di
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
   
    context.bot.send_message(chat_id=update.effective_chat.id, text="Monitor your network with this Bot!")
    
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
    elif(query.data == "list_wan_rules"):
        show_rules(update,context,"wan")
    elif(query.data == "list_lan_rules"):
        show_rules(update,context,"lan")
    elif(query.data == "list_opt1_rules"):
        show_rules(update,context,"opt1")



def main():

    #__________________________________________________
    #Read token from api_telegram file

    with open(PATH_API,"r") as file:

        TOKEN=file.read().replace("\n","") #replace is necessary because at the end of file there is a "\n" to delete


    #__________________________________________________
    #Initialize logging file
    logging.basicConfig(filename=PATH_LOG,filemode="a",format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",level=logging.INFO)


    #__________________________________________________
    #Initialize filters class
    filter_keyboard_list_rules = FilterKeyboardListRules()
    filter_keyboard_show_actions = FilterKeyboardShowActions()
    
    #__________________________________________________
    #Instantiate the Updater
    updater = Updater(token=TOKEN,use_context=True)

    #__________________________________________________
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
    
    #Initialize keyboard for actions here, so as to be created at start of bot
    inline_keyboard_actions = [
                [InlineKeyboardButton("Open netA", callback_data='open_netA'),
                    InlineKeyboardButton("Close netA", callback_data='close_netA')],
                ]
    
    #Initialize keyboard for interface's rules here, so as to be created at start of bot
    inline_keyboard_rules = [
                [InlineKeyboardButton("WAN", callback_data='list_wan_rules'),
                    InlineKeyboardButton("LAN", callback_data='list_lan_rules'),
                    InlineKeyboardButton("OPT1", callback_data='list_opt1_rules')],
                ]

    main_menu_keyboard = [[KeyboardButton("List rules")],[KeyboardButton("Show actions")]]

    #Modify the global variable
    global inline_reply_markup_actions
    inline_reply_markup_actions = InlineKeyboardMarkup(inline_keyboard_actions)
    
    global inline_reply_markup_rules
    inline_reply_markup_rules = InlineKeyboardMarkup(inline_keyboard_rules)

    #Modify the global variable
    global reply_kb_markup
    reply_kb_markup = ReplyKeyboardMarkup(main_menu_keyboard)

    
    #________________________________________________
    #Start the Bot
    updater.start_polling()

    clear_env() #clean log file every <WAIT_SECONDS> seconds
    logging.info("SERVER STARTED")
    updater.idle() #Run the bot until the user presses Ctrl-C or the process receives SIGINT,
                   #SIGTERM or SIGABRT



if __name__ == '__main__':
    main()
