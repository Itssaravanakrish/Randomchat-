import telepot
from telepot.loop import MessageLoop
from telepot import exception
import config as conf
import time
from Log.logger import *
from pprint import pprint
import db as DB
import random
import string

START = "**👋 Welcome! \nHere you can chat anonymously with other users. \n\nThis bot is under development so I kindly ask you to use /report to report any bugs or recommend some changes. \n\nPress /find to find someone to chat with, /leave to leave the room, and /skip to go from room to room!**"

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def newUser(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    #check if user exist in database, if no ad it
    if not DB.query(DB.CHECK_USER,(chat_id,)):
        log(f"New user: {chat_id, msg['chat']['first_name'], 'User'}")
        DB.query(DB.INSERT_USER, (chat_id, msg['chat']['first_name'], 'User'))
        return START
    else:
        return f"Bentornato {msg['chat']['first_name']}"


def onAdminMsg(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    r = ''
    arg = msg['text'].split(" ")
    if arg[0] == "/alluser":
        r = DB.query(DB.SELECT_USERS)
    elif arg[0] == "/allrooms":
        r = DB.query(DB.SELECT_ROOMS)
    elif arg[0] == "/sendmessage":
        try:
            bot.sendMessage(int(arg[1]),arg[2:])
            r = "Message sent"
        except Exception as e:
            r = e
    elif arg[0] == "/ban":
        if int(arg[1:][0]) == conf.ID_ADMIN:
            r = "Seriously? Do you want to be banned from your bot? I will not let you! Its stupid, you're stupid!"
        elif DB.query(DB.BAN_USER,(arg[1:][0],True)) > 0:
            r = f"{arg[1:]} is banned"
    elif arg[0] == "/unban":
        if DB.query(DB.BAN_USER,(int(arg[1:][0]),False)) > 0:
            r = f"{arg[1:]} is unbanned"
    elif arg[0] == "/log":
        bot.sendDocument(chat_id,open("Log/logs.txt", 'rb'))
    elif arg[0] == "/help":
        r = """
/alluser
/allrooms
/allchats
/sendmessage "id" "text"
/ban "id"
/unban "id"
/log
        """
    else:
        r = onUserMsg(msg)
    return r

def onUserMsg(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    r = ''
    if content_type == 'text':
        if msg['text'] == '/start':
            r = newUser(msg)
        elif not DB.query(DB.CHECK_USER,(chat_id,)):
            r = "`Start the bot using `/start"
        elif msg['text'][0] == '/':
            ##########################    
            #   JOIN    #
            if msg['text']  == "/find":
                if DB.check_join(chat_id):
                    r = "**🔰 You are already, in a room.\n`/leave` to exit**"
                else:
                    if not DB.join_room(chat_id):
                        r = "**♻️ There are not free room now.\nTry later please!**"
                    else:
                        partner_id = DB.get_partner_by_id(chat_id)

                        if partner_id: 
                            try:
                                bot.sendMessage(partner_id[0][0],"`You have a partner! Say Hi!`", parse_mode= "Markdown")
                            except Exception as e:
                                log("Exception")
                                all_exception_handler()   
                            r = "**ℹ️ You are not alone in this room! Say Hi!**"
                        else:
                            r = "**📝 You are now in a waiting room\nWait for a user**"
            #   LEAVE   #
            elif msg['text']  == "/leave":
                if DB.check_join(chat_id):
                    partner_id = DB.get_partner_by_id(chat_id)
                    DB.leave_room(chat_id)
                    if partner_id:
                        try:
                            bot.sendMessage(partner_id[0][0],"**💠 Your partner has left this room. Change room /skip or wait for a new user**", parse_mode= "Markdown")
                        except Exception as e:
                            log("Exception")
                            all_exception_handler()
                    r = "**🏵️ You left the room, click** `/find` **to join another room**"
                else:
                    r = "📌 **You are not in a room, click** `/find` **to join one*"
            #   SKIP    #
            elif msg['text']  == "/skip":
                
                if DB.check_join(chat_id):
                    partner_id = DB.get_partner_by_id(chat_id)
                    #Leave
                    DB.leave_room(chat_id)
                    #Notice the partner
                    if partner_id:
                        try:
                            bot.sendMessage(partner_id[0][0],"**⛔ Your partner has left this room. Change room /skip or wait for a new user**", parse_mode= "Markdown")
                        except Exception as e:
                            log("Exception")
                            all_exception_handler()
                #Join
                if not DB.join_room(chat_id):
                    r = "**💠 There are not free room now.\nTry later please!**"
                else:
                    partner_id = DB.get_partner_by_id(chat_id)
                    if partner_id:    
                        try:
                            bot.sendMessage(partner_id[0][0], "**👨‍👩‍👦‍👦 You have a partner! Say And Chat Him!**", parse_mode= "Markdown")
                        except Exception as e:
                            log("Exception")
                            all_exception_handler()   
                        r = "You are not alone in this room! Say Hi!"
                    else:
                        r = "`You have changed the waiting room\nWait for a user`"
            #########################
            
            elif msg['text'][:8] == "/report":
                message = msg['text'].split(' ')
                if len(message) > 1:
                    bot.sendMessage(conf.ID_ADMIN, "📺 Message from " + str(chat_id) + " " + msg['text'][9:])
                else:
                    r = "`Use /report For Report`"
            else:
                r = "**⚠️ Unknow Command**"
        else:
            #Search for partner id
            if not DB.check_join(chat_id):
                r = "**⚙️ You are not in a room..** `/find`"
            else:    
                partner_id = DB.get_partner_by_id(chat_id)
                if not partner_id:
                    r ="**☕ You are alone here..wait or** `/skip `**this room**"
                else:
                    try:
                        bot.sendMessage(partner_id[0][0],msg['text'])
                    except Exception as e:
                        log("Exception")
                        all_exception_handler()  
    elif content_type == 'photo':
        if not DB.query(DB.CHECK_USER,(chat_id,)):
            r = "**⚠️ Do Not Send Photo Start the Bot using** `/start"
        else:
            partner_id = DB.get_partner_by_id(chat_id)
            if not partner_id:
                r ="**⚠️ Your partner has left this room**"
            else:
                try:
                    cap = ''
                    if 'caption' in msg:
                        cap = msg['caption']
                    bot.sendPhoto(partner_id[0][0],msg['photo'][-1]['file_id'], caption=cap)
                except Exception as e:
                    log("Exception")
                    all_exception_handler()  
    return r

def onMessage(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        #Preliminary check
        if DB.query(DB.CHECK_BAN,(chat_id,)):
            resp = "**📌 You are banned, repent of what you did**"
            bot.sendMessage(chat_id, resp)
            return
        elif content_type != 'text' and content_type != 'photo':
            bot.sendMessage(chat_id,"`From bot`: you can send only message or photo!", parse_mode = "Markdown")
            log(f"{chat_id} sent {content_type}")
            return

        #Handle message
        resp = ''
        if chat_id == conf.ID_ADMIN:
            resp = onAdminMsg(msg)
            if resp == None or resp == [] or resp == '' or resp == False:
                resp = "Nothing to say"
        else:
            resp = onUserMsg(msg)
            if resp == None or resp == [] or resp == '':
                return
        
        bot.sendMessage(chat_id, str(resp), parse_mode = "Markdown")
        log("Sent message to "+str(chat_id))

    except Exception as e:
        log("Exception")
        all_exception_handler()

def run():
    global bot
    bot = telepot.Bot(conf.TOKEN)
    MessageLoop(bot,onMessage).run_as_thread()
    log("Stranger chat bot started")
    bot.sendMessage(conf.ID_ADMIN,"♥️ Stranger chat bot started")
