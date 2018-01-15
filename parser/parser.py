import collections
import pickle
import pika
import time
import bs4


import vk_api
from vk_api.audio import VkAudio


def connect_vk(login, password):
    vk_session = vk_api.VkApi(login, password)

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
    return vk_session


def get_users_audio(vk_session, vk_page):
    vkaudio = VkAudio(vk_session)

    all_audios = []
    offset = 0

    while True:
        audios = vkaudio.get(owner_id=vk_page, offset=offset)
        all_audios.append(audios)
        offset += len(audios)

        if not audios:
            break

    all_audios = [audio for audios in all_audios for audio in audios]
    return all_audios


def top_musicians(audios, top_n=15):
    artists = collections.Counter()

    for audio in audios:
        artists[audio['artist']] += 1

    # top 15 music bands
    print('\nTop {}:'.format(top_n))
    for artist, tracks in artists.most_common(top_n):
        print('{} - {} tracks'.format(artist, tracks))


def on_request(ch, method, props, body):

    user_id = int(body)
    response = get_users_audio(vk_session, user_id)
    print("parsed page of user", user_id)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id
                                                     =props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


with open('secret.pkl', mode='rb') as f:
    secret = (pickle.load(f))
login = secret['login']
password = secret['password']
vk_session = connect_vk(login, password)

time.sleep(15)
connection = pika.BlockingConnection(pika.ConnectionParameters(host='queue'))
channel = connection.channel()
channel.queue_declare(queue='rpc_user_music')

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='rpc_user_music')

print("parsing service ready")
channel.start_consuming()
