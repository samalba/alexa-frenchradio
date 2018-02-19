#!/usr/bin/env python3

import logging
import os

import yaml
from flask import Flask
from flask_ask import Ask, question, audio


app = Flask(__name__)
ask = Ask(app, '/')
logger = logging.getLogger()
logging.getLogger('flask_ask').setLevel(logging.INFO)
radio_playlist = None


@ask.launch
def launch():
    card_title = 'French Radio'
    text = 'Tell me the name of a French Radio that you want to listen to.'
    prompt = 'You can tell me the name of the Radio.'
    return question(text).reprompt(prompt).simple_card(card_title, text)


def find_radio(utterance):
    utterance = utterance.lower()
    for radio, info in radio_playlist.items():
        for u in info['uterrances']:
            if u == utterance:
                return (radio, info)


@ask.intent('PlayRadioIntent')
def play_radio(radioname):
    if not radioname:
        logger.info('PlayRadioIntent: Empty intent slot')
        return audio('Sorry, I do not understand the name of this Radio.')
    radio = find_radio(radioname)
    if not radio:
        logger.info('PlayRadioIntent: Cannot find radio {}'.format(radioname))
        return audio('Sorry, I cannot find the radio {}'.format(radioname))
    (radio, info) = radio
    speech = 'Playing the radio {}'.format(radio)
    return audio(speech).play(info['url'])


@ask.intent('AMAZON.PauseIntent')
def pause():
    return audio('Paused the stream.').stop()


@ask.intent('AMAZON.ResumeIntent')
def resume():
    return audio().resume()


@ask.intent('AMAZON.StopIntent')
def stop():
    return audio().clear_queue(stop=True)


@ask.session_ended
def session_ended():
    return "{}", 200


def load_radio_list():
    global radio_playlist
    dir_path = os.path.dirname(os.path.realpath(__file__))
    radio_list = os.path.join(dir_path, 'radio_list.yml')
    with open(radio_list) as f:
        radio_playlist = yaml.load(f)
        logger.info('Loaded radio list from {}'.format(radio_list))


def lambda_handler(event, _context):
    """AWS Lambda entrypoint"""
    load_radio_list()
    return ask.run_aws_lambda(event)


if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    load_radio_list()
    app.run(host='0.0.0.0', port=1080)
