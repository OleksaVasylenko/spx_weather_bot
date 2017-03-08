#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram.ext import (Updater, CommandHandler, Filters,
                          MessageHandler, ConversationHandler, Job)
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from time import mktime, localtime, sleep, asctime, strptime, strftime
from utils import UserSettings
import logging
import os
import sys
import weather
import shelve

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

LOCATION = 0


def start(bot, update):
    chat_id = update.message.chat_id
    update.message.reply_text('Hi! I am weather bot.\n'
                              'Send /setlocation to check the weather in your city.')
    with shelve.open('usersettings.db') as db:
        db[str(chat_id)] = UserSettings(update.message.from_user)


def ask_location(bot, update):
    location_keyboard = KeyboardButton(text='Send my location via GPS',
                                       request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_keyboard]])
    bot.sendMessage(chat_id=update.message.chat_id,
                    text='Please enter your city:',
                    reply_markup=reply_markup)
    return LOCATION


def store_location(bot, update):
    chat_id = update.message.chat_id
    if getattr(update.message, 'location', False):  # location data is name or coordinates?
        user_loc = update.message.location
        user_loc = (user_loc.latitude, user_loc.longitude)
    else:
        user_loc = update.message.text
    with shelve.open('usersettings.db') as db:
        user = db[str(chat_id)]
        user.set_location(user_loc)
        db[str(chat_id)] = user
    res = ('You`ve just set your location as {}.\n'
    'Now you can check out weather with /getweather command').format(user_loc)
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=chat_id, text=res, reply_markup=reply_markup)
    return ConversationHandler.END


def restart(bot, update):
    update.message.reply_text('Bot is restarting...')
    sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def getweather(bot, update):
    if isinstance(update, Job):  # call came from update or from job_queue?
        job = update
        chat_id = job.context
    else:
        chat_id = update.message.chat_id
    with shelve.open('usersettings.db') as db:
        location = db[str(chat_id)].location
    if location:
        summary = weather.curr_weather(location) + '\n' + asctime(localtime())
    else:
        summary = 'You haven`t set your location. Please hit /setlocation'
    bot.sendMessage(chat_id=chat_id, text=summary, parse_mode='HTML')


def notify(bot, update, args, job_queue):
    chat_id = update.message.chat_id
    try:
        alarm = args[0]                                          # extract time command
        date_alarm = strftime('%Y.%m.%d ', localtime()) + alarm  # retrieving current date & concatenating date + time
        struct_alarm = strptime(date_alarm, '%Y.%m.%d %H:%M')    # parsing date&time str to time tuple (struct_time obj)
        sec_alarm = mktime(struct_alarm)                         # alarm represented in seconds
    except (IndexError, ValueError):
        update.message.reply_text('Usage:\n /notify HH:MM')
        return
    if (sec_alarm - mktime(localtime())) > 0:
        offset = sec_alarm - mktime(localtime())               # difference between alarm time and current time, secs
    else:
        offset = 86400 + (sec_alarm - mktime(localtime()))     # offsetting to next day
    job = Job(getweather, 86400, repeat=True, context=chat_id)
    job_queue.put(job, next_t=offset)
    update.message.reply_text('Notification set on {}'.format(alarm))


def cancel(bot, update):
    chat_id = update.message.chat_id
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=chat_id, text='Okay, maybe next time.', reply_markup=reply_markup)
    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update {} caused error "{}"'.format(update, error))


def main():
    updater = Updater(token='331318669:AAHiHNvO0J8tX7ys61SKZuOl0g-UtKo3Xe4')
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setlocation', ask_location)],
        states={
            LOCATION:
                [MessageHandler(Filters.text | Filters.location, store_location)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Adding handlers to dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('r', restart))
    dp.add_handler(CommandHandler('getweather', getweather))
    dp.add_handler(CommandHandler('notify', notify,
                                  pass_args=True, pass_job_queue=True))
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
