#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram.ext import (Updater, CommandHandler, Filters,
                          MessageHandler, ConversationHandler, Job)
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from time import *
from utils import UserSettings
from config import bot_token, data_base
import sys
import os
import logging
import weather
import shelve
import dbm

# Changing working directory to the script`s directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

LOCATION = 0
NOTIFY_NUMBER = 0
FUNC = ''


def start(bot, update):
    chat_id = update.message.chat_id
    res = ('Hi, {}! I am weather bot.\n'
           'Send /setlocation to check the weather in your city.'
           ).format(update.message.from_user.first_name)
    bot.sendMessage(chat_id=chat_id, text=res)
    with shelve.open(data_base) as db:
        db[str(chat_id)] = UserSettings(update.message.from_user)


def ask_location(bot, update):
    location_keyboard = KeyboardButton(text='Send my location via GPS',
                                       request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_keyboard], ['cancel']])
    bot.sendMessage(chat_id=update.message.chat_id,
                    text='Please enter your city:',
                    reply_markup=reply_markup)
    return LOCATION


def store_location(bot, update):
    if update.message.text == 'cancel':
        return cancel(bot, update)
    chat_id = update.message.chat_id
    if getattr(update.message, 'location', False):  # location data is name or coordinates?
        user_loc = update.message.location
        user_loc = (user_loc.latitude, user_loc.longitude)
    else:
        user_loc = update.message.text
    with shelve.open(data_base) as db:
        user = db[str(chat_id)]
        user.set_location(user_loc)
        db[str(chat_id)] = user
    if type(user_loc) == tuple:
        user_loc = str(user_loc) + '. I will find nearest available weather station to you'
    res = (
        'You`ve just set your location as {}.\n'
        'Now you can check out weather with /today command'
        ).format(user_loc)
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=chat_id, text=res, reply_markup=reply_markup)
    return ConversationHandler.END


def restart(bot, update):
    update.message.reply_text('Bot is restarting...')
    sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def delay_comp(job, timeout):
    """
    Compensates delay of job execution
    :param job: Job instance
    :param timeout: integer number of seconds
    :return: None
    """
    interval = 86400
    # use this if the interval is less than 60 seconds
    timeout = int(str(timeout)[-1])
    if timeout:
        if job.interval == interval:
            job.interval -= timeout
        elif job.interval < interval:
            job.interval += interval - job.interval - timeout
    else:
        if job.interval != interval:
            job.interval = interval


def today(bot, update):
    if isinstance(update, Job):   # call came from update or from job_queue?
        chat_id = update.context  # same as job.context
    else:
        chat_id = update.message.chat_id
    try:
        with shelve.open(data_base, 'r') as db:
            location = db[str(chat_id)].location
    except (KeyError, dbm.error[0]):
        return unknown_user(bot, update)
    if location:
        summary = weather.today_weather(location)
        if getattr(update, 'interval', False):
            delay_comp(update, localtime()[5])
    else:
        summary = 'You haven`t set your location. Please hit /setlocation'
    bot.sendMessage(chat_id=chat_id, text=summary, parse_mode='HTML')


def tomorrow(bot, update):
    if isinstance(update, Job):   # call came from update or from job_queue?
        chat_id = update.context  # same as job.context
    else:
        chat_id = update.message.chat_id
    try:
        with shelve.open(data_base) as db:
            location = db[str(chat_id)].location
    except KeyError:
        return unknown_user(bot, update)
    if location:
        tom_date = gmtime(time() + 86400)
        summary = weather.tomorrow_weather(location, tom_date)
        if getattr(update, 'interval', False):
            delay_comp(update, localtime()[5])
    else:
        summary = 'You haven`t set your location. Please hit /setlocation'
    bot.sendMessage(chat_id=chat_id, text=summary, parse_mode='HTML')


# def notify(bot, update, args, job_queue, chat_data):
#     chat_id = update.message.chat_id
#     try:
#         alarm = args[0]                                          # extract time command
#         date_alarm = strftime('%Y.%m.%d ', localtime()) + alarm  # retrieving current date & concatenating date + time
#         struct_alarm = strptime(date_alarm, '%Y.%m.%d %H:%M')    # parsing date&time str to time tuple (struct_time obj)
#         sec_alarm = mktime(struct_alarm)                         # alarm represented in seconds
#     except (IndexError, ValueError):
#         update.message.reply_text('Usage:\n /notify HH:MM')
#         return
#     if (sec_alarm - mktime(localtime())) > 0:
#         offset = sec_alarm - mktime(localtime())                 # difference between alarm time and current time, secs
#     else:
#         offset = 86400 + (sec_alarm - mktime(localtime()))       # offsetting to next day
#     job = Job(tomorrow, 86400, repeat=True, context=chat_id)        # repeat every day
#     job_queue.put(job, next_t=offset)
#     chat_data[alarm] = job
#     update.message.reply_text(
#         'Notification is set on {}\n'
#         'to unset notifications send /del_notify'.format(alarm))


def notify(bot, update, args, chat_data):
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
        offset = sec_alarm - mktime(localtime())                 # difference between alarm time and current time, secs
    else:
        offset = 86400 + (sec_alarm - mktime(localtime()))       # offsetting to next day
    chat_data[chat_id] = (offset, alarm)
    choice_keyboard = [['today', 'tomorrow'],
                       ['cancel']]
    reply_markup = ReplyKeyboardMarkup(choice_keyboard)
    bot.sendMessage(chat_id=chat_id,
                    text='Please choose a forecast '
                         'which I`ll send you on that time.',
                    reply_markup=reply_markup)
    return FUNC


def set_notify(bot, update, job_queue, chat_data):
    chat_id = update.message.chat_id
    func = update.message.text
    if func == 'cancel':
        del chat_data[chat_id]
        return cancel(bot, update)
    offset, alarm = chat_data[chat_id]
    del chat_data[chat_id]
    job = Job(globals()[func], 86400, repeat=True, context=chat_id)        # repeat every day
    job_queue.put(job, next_t=offset)
    chat_data[alarm] = job
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=chat_id,
                    text=('Notification "{}" is set on {}\n '
                          'to unset notifications send /del_notify'
                          ).format(func, alarm),
                    reply_markup=reply_markup)
    return ConversationHandler.END


def notify_list(bot, update, chat_data):
    chat_id = update.message.chat_id
    if chat_data:
        res = ('Send a number of notification in list to delete it:\n')
        for num, job_t in enumerate(chat_data, 1):
            callback = chat_data[job_t].name
            res += '{num}. {time} — {func}\n'.format(num=num, time=job_t,
                                                     func=callback)
    else:
        bot.sendMessage(chat_id=chat_id,
                        text='You have no active notifications')
        return ConversationHandler.END
    num_keyboard = [['1', '2', '3'],
                    ['4', '5', '6'],
                    ['7', '8', '9'],
                    ['clear all', 'cancel']]
    reply_markup = ReplyKeyboardMarkup(num_keyboard)
    bot.sendMessage(chat_id=chat_id, text=res, reply_markup=reply_markup)
    return NOTIFY_NUMBER


def remove_notify(bot, update, chat_data):
    chat_id = update.message.chat_id
    answer = update.message.text
    reply_markup = ReplyKeyboardRemove()
    try:
        if answer == 'clear all':
            for job in chat_data:
                chat_data[job].schedule_removal()
            chat_data.clear()
            bot.sendMessage(chat_id=chat_id, text='All notifications cleared',
                            reply_markup=reply_markup)
            return ConversationHandler.END
        elif answer == 'cancel':
            return cancel(bot, update)
        pointer = int(answer)-1
        job = list(chat_data)[pointer]
        chat_data[job].schedule_removal()
        del chat_data[job]
        bot.sendMessage(chat_id=chat_id,
                        text=('{} notification deleted'.format(job)),
                        reply_markup=reply_markup)
    except (TypeError, IndexError, ValueError):
        bot.sendMessage(chat_id=chat_id,
                        text='There is no notifications with such number.',
                        reply_markup=reply_markup)
    return ConversationHandler.END


def unknown_user(bot, update):
    update.message.reply_text('I don`t know who you are.\n'
                              'Please introduce yourself by sending /start')


def cancel(bot, update):
    chat_id = update.message.chat_id
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=chat_id, text='Okay, maybe next time ¯\_(ツ)_/¯',
                    reply_markup=reply_markup)
    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update {} caused error "{}"'.format(update, error))


def main():
    updater = Updater(token=bot_token)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    set_not = ConversationHandler(
        entry_points=[CommandHandler('notify', notify, pass_args=True
                                     , pass_chat_data=True)],
        states={
            FUNC:
                [MessageHandler(Filters.text, set_notify, pass_chat_data=True,
                                pass_job_queue=True)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    loc_conv = ConversationHandler(
        entry_points=[CommandHandler('setlocation', ask_location)],
        states={
            LOCATION:
                [MessageHandler(Filters.text | Filters.location, store_location)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    del_not = ConversationHandler(
        entry_points=[CommandHandler('del_notify', notify_list,
                                     pass_chat_data=True)],
        states={
            NOTIFY_NUMBER:
                [MessageHandler(Filters.text, remove_notify,
                                pass_chat_data=True)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Adding handlers to dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(loc_conv)
    dp.add_handler(del_not)
    dp.add_handler(set_not)
    dp.add_handler(CommandHandler('r', restart))
    dp.add_handler(CommandHandler('today', today))
    dp.add_handler(CommandHandler('tomorrow', tomorrow))
    # dp.add_handler(CommandHandler('notify', notify,
    #                               pass_args=True, pass_job_queue=True,
    #                               pass_chat_data=True))
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
