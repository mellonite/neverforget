from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import time

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# initialize a dictionary for chats
# where key is chat id and value is another dictionary of alerts
chats = {}

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi!')

    # add alert defaults
    chats[update.message.chat_id] = {'blaze':'4:20', 'neverforget':'9:11'}


def stop(bot, update):
    bot.sendMessage(update.message.chat_id, text = 'Bye!')
    chats.pop(update.message.chat_id)
    print(myChats)


def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='I will send you messages about the time. '
                                            + '\n Default reminders are /blaze and /neverforget'
                                            + '\n\n/start receiving reminders. '
                                            + '\n/stop removes all reminders'
                                            + '\n/add your own reminders'
                                            + '\n\nFor /add, use syntax: /add hh:mm message'
                                            + '\nExample: "/add 11:11 wish" will send a /wish reminder at 11:11')

def add(bot, update):
    splitMsg = update.message.text.split(' ')
    alertTime = splitMsg[1]
    alertMsg = splitMsg[2]
    chats[update.message.chat_id][alertMsg] = alertTime

    bot.sendMessage(update.message.chat_id, text='OK, at ' + alertTime + ' I will remind you to ' + alertMsg + ' every day')
    print('added: ')
    print(chats[update.message.chat_id])
    print()

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def sendAlerts(bot):
    # for all the alert values in the allAlerts dictionary
    for c in chats:
        for a in chats[c]:
            print('chats[c]: ' + str(chats[c]))
            splitTime = chats[c][a].split(':') # splits time into two parts
            hour = splitTime[0]
            minute = splitTime[1]
            print(hour + ':' + minute)
            print(str(time.localtime().tm_hour) + ':' + str(time.localtime().tm_min))
            if time.localtime().tm_hour == int(hour) and time.localtime().tm_min == int(minute):
                bot.sendMessage(c, text='/'+ a)


def main():
    # Create the EventHandler and pass it your bot's token.
    TOKEN = open('token', 'r').read()

    updater = Updater(TOKEN)
    jobQ = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("stop", stop))
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
