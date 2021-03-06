import logging
import os
import pickle
from threading import Thread

import pika
import sentry_sdk
import telegram
from sentry_sdk.integrations.logging import LoggingIntegration
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext import Updater

sentry_logging = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
)

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[sentry_logging]
)

MIN_POPULARITY_LEVEL = 4
MAX_POPULARITY_LEVEL = 10
DEFAULT_POPULARITY_LEVEL = 7
MIN_TEXT_TO_PARSE = 200
TG_BOT_PRIORITY = 2  # message priority inn queue higher is better


def start(bot, update):
    message = '''
Hi, I'm Muzender - music recommender.
Drop me a link to your vk.com account and I will suggest you some nice music.
    '''
    bot.sendMessage(chat_id=update.message.chat_id, text=message)


def request_recommendations(body):
    if 'user_music' in body:
        routing_key = 'reco_queue'
    else:
        routing_key = 'parser_queue'
    channel.basic_publish(exchange='',
                          routing_key=routing_key,
                          body=pickle.dumps(body),
                          properties=pika.BasicProperties(priority=TG_BOT_PRIORITY),
                          )
    logger.info(f'send recommendation request for user {body["chat_id"]} with popularity_level \
                {body.get("popularity_level", DEFAULT_POPULARITY_LEVEL)}')


def on_request(ch, method, props, body):
    body = pickle.loads(body)
    answer = body['recommendations']
    bot = body['bot']

    if answer == 'No such user or empty music collection.':
        bot.sendMessage(chat_id=body['chat_id'],
                        text=answer)
    else:
        if type(answer) is list:
            keyboard = []
            for artist in answer:
                artist = artist.lstrip()
                link = 'https://music.yandex.ru/search?text=' \
                       + artist.replace(' ', '%20') \
                       + '&type=artists'
                keyboard.append([telegram.InlineKeyboardButton(text=artist,
                                                               url=link)])

            markup = telegram.InlineKeyboardMarkup(keyboard)
            bot.sendMessage(chat_id=body['chat_id'],
                            text='Check this out:',
                            reply_markup=markup,
                            )

            keyboard = [[telegram.KeyboardButton('less popular'),
                         telegram.KeyboardButton('more popular')],
                        [telegram.KeyboardButton('good, I like it!')],
                        ]
            markup = telegram.ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            bot.sendMessage(chat_id=body['chat_id'],
                            text='Feedback is appreciated',
                            reply_markup=markup,
                            )
    ch.basic_ack(delivery_tag=method.delivery_tag)


def echo(bot, update):
    sent = update.message.text.strip().lower()

    body = {'bot': bot,
            'chat_id': update.message.chat_id
            }

    if 'vk.com/' in sent:
        vk_id = sent.split('/')[-1]
        logger.info('new user: {}'.format(vk_id))
        user_preferences[update.message.chat_id] = {'vk_page': vk_id}
        body.update(user_preferences[update.message.chat_id])
        request_recommendations(body)
    elif len(sent) > MIN_TEXT_TO_PARSE:
        body['user_music'] = sent.split('\n')
        request_recommendations(body)
    elif update.message.chat_id in user_preferences.keys():
        if sent == 'more popular':
            curr_popularity_level = user_preferences[update.message.chat_id].get('popularity_level',
                                                                                 DEFAULT_POPULARITY_LEVEL)
            user_preferences[update.message.chat_id]['popularity_level'] = min(curr_popularity_level + 1,
                                                                               MAX_POPULARITY_LEVEL)
            body.update(user_preferences[update.message.chat_id])
            request_recommendations(body)
        elif sent == 'less popular':
            curr_popularity_level = user_preferences[update.message.chat_id].get('popularity_level',
                                                                                 DEFAULT_POPULARITY_LEVEL)
            user_preferences[update.message.chat_id]['popularity_level'] = max(curr_popularity_level - 1,
                                                                               MIN_POPULARITY_LEVEL)
            body.update(user_preferences[update.message.chat_id])
            request_recommendations(body)
        elif sent == 'good, I like it!':
            logger.info('user likes recommendation, details: {}'.format(user_preferences[update.message.chat_id]))
            bot.sendMessage(chat_id=update.message.chat_id, text='Thanks!')
        else:
            message = 'Drop the link to your vk page and I will recommend you some music.'
            bot.sendMessage(chat_id=update.message.chat_id, text=message)
    else:
        message = 'Just drop the link to your vk.com page.'
        bot.sendMessage(chat_id=update.message.chat_id, text=message)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger('tg bot')
    logger.propagate = False
    logger.info('Initialize tg bot')

    with open('../data/token.pkl', 'rb') as f:
        token = pickle.load(f)

    user_preferences = {}
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(echo_handler)
    Thread(target=updater.start_polling())

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='queue'))
        channel = connection.channel()
        channel.queue_declare(queue='tg_bot_queue')

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(on_request, queue='tg_bot_queue')
        channel.start_consuming()
    except:
        # close all threads if connection is lost
        os._exit(1)
