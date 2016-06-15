from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton, ParseMode
import logging
import time
import python3pickledb as pickledb

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# create database object
db = pickledb.load('bot.db', True)

helpText = 'I will send you messages about the time. ' \
           '\n\n/add your own reminders' \
           '\nUse syntax: /add HH:MM message' \
           '\nI run on a 24-hour clock!' \
           '\n\n/remove reminders you have added'

# initialize the database
if not db.get('alerts') :
    db.set('alerts', {})
    db.set('state', {})

#temporary storage
context = {}

# Create the EventHandler and pass it your bot's token.
TOKEN = open('token', 'r').read()

# Define the different states a chat can be in
MENU, AWAIT_CONFIRMATION, AWAIT_INPUT = range(3)


# Example handler. Will be called on the /set command and on regular messages
def remove_value(bot, update):
    chat_id = str(update.message.chat_id)
    user_id = update.message.from_user.id
    text = update.message.text

    state = db.get('state')
    chat_state = state.get(chat_id, MENU)
    chat_context = context.get(chat_id, None)

    # Since the handler will also be called on messages, we need to check if
    # the message is actually a command
    if chat_state == MENU and text[0] == '/':
        alerts = db.get('alerts')
        # check that he has alerts
        if chat_id not in alerts or not alerts[chat_id].keys():
            bot.sendMessage(chat_id, text='You have no reminders! See /help for more info.')
        else:
            state[chat_id] = AWAIT_INPUT  # set the state
            context[chat_id] = user_id  # save the user id to context
            msg = removeMsg(bot, update)
            bot.sendMessage(chat_id, text=msg, reply_markup=ForceReply())

    # If we are waiting for input and the right user answered
    elif chat_state == AWAIT_INPUT and chat_context == user_id:
        state[chat_id] = AWAIT_CONFIRMATION

        # Save the user id and the answer to context
        context[chat_id] = (user_id, update.message.text)
        reply_markup = ReplyKeyboardMarkup(
            [['Yes', 'No']],
            one_time_keyboard=True)
        bot.sendMessage(chat_id,
                        text="Are you sure you would like to remove *%s*?" % update.message.text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup)

    # If we are waiting for confirmation and the right user answered
    elif chat_state == AWAIT_CONFIRMATION and chat_context[0] == user_id:
        del state[chat_id]

        alerts = db.get('alerts')
        if text == 'Yes':
            bot.sendMessage(chat_id,
                            text="I will no longer remind you to *%s*." % str(context[chat_id][1]),
                            parse_mode=ParseMode.MARKDOWN)
            alerts[chat_id].pop(context[chat_id][1])
            db.set('alerts', alerts)
        else:
            bot.sendMessage(chat_id,
                            text="I will keep reminding you to *%s*, then." % str(context[chat_id][1]),
                            parse_mode=ParseMode.MARKDOWN)

        del context[chat_id]

    db.set('state', state)


def removeMsg(bot, update):
    chat_id = str(update.message.chat_id)
    message = 'Alright, which of these reminders would you like to remove?\n'

    # get all of the reminders saved for this chat
    alerts = db.get('alerts')

    reminders = [k for k in alerts[chat_id].keys()]

    for r in reminders:
        message += '\n' + r

    message += '\n\nIf you\'ve changed your mind, send /cancel.'
    return message

# Handler for the /cancel command.
# Sets the state back to MENU and clears the context
def cancel(bot, update):
    chat_id = update.message.chat_id
    state = db.get('state')
    del state[chat_id]
    db.set('state', state)
    del context[chat_id]

def help(bot, update):
    bot.sendMessage(update.message.chat_id, text=helpText)

addError = 'Please use the format: /add HH:MM message.' \
           '\nExample: /add 11:11 wish' \
           '\nI run on a 24-hour clock!'

existingAlert = 'I already remind you to *%s*!' \
                '\nPlease pick a new name for your reminder or /remove the existing one.'

def add(bot, update):
    chat_id = str(update.message.chat_id)
    splitMsg = update.message.text.split(' ')

    #Check the formatting
    if len(splitMsg) != 3:
        bot.sendMessage(update.message.chat_id, text=addError)
        return

    alertTime = splitMsg[1]

    checkTime = alertTime.split(':')

    # The time must consist only of two digits, one with no more than 2 digits
    # and one with exactly two digits
    if len(checkTime) != 2 or not checkTime[0].isdigit() or not checkTime[1].isdigit() \
       or len(checkTime[1]) != 2 or len(checkTime[0]) > 2:
        bot.sendMessage(update.message.chat_id, text=addError)
        return

    alertMsg = splitMsg[2]

    alerts = db.get('alerts')

    # if the chat_id does not yet exist in the database, add it
    if chat_id not in alerts:
        alerts[chat_id] = {}

    # Check that the alert doesn't already exist
    if alertMsg in alerts[chat_id]:
        bot.sendMessage(update.message.chat_id,
                        text=existingAlert % alertMsg,
                        parse_mode=ParseMode.MARKDOWN)
    else:
        alerts[chat_id][alertMsg] = alertTime
        bot.sendMessage(update.message.chat_id,
                        text='OK, at *%s* I will remind you to *%s* every day' % (alertTime, alertMsg),
                        parse_mode=ParseMode.MARKDOWN)
    db.set('alerts', alerts)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def sendAlerts(bot):
    # for all the alert values in the allAlerts dictionary
    alerts = db.get('alerts')
    for c in alerts: # for each chat in alerts dict
        for a in alerts[c]: # for each alert in chats
            splitTime = alerts[c][a].split(':') # splits time into two parts
            hour = splitTime[0]
            minute = splitTime[1]

            if time.localtime().tm_hour == int(hour) and time.localtime().tm_min == int(minute):
                bot.sendMessage(c, text='/'+ a)

def main():
    updater = Updater(TOKEN)
    jobQ = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    # The command
    updater.dispatcher.add_handler(CommandHandler('remove', remove_value))
    # The answer and confirmation
    updater.dispatcher.add_handler(MessageHandler([Filters.text], remove_value))
    updater.dispatcher.add_handler(CommandHandler('cancel', cancel))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("add", add))

    delay = 60 - time.localtime().tm_sec # don't start checking until the beginning of the next minute
    jobQ.put(sendAlerts, 60, True, next_t=delay, prevent_autostart=False) # begin checking the time

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
