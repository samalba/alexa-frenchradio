#!/usr/bin/env python3

import logging
import time
import pprint
import json

from flask import Flask, request
from flask_ask import Ask, question, audio, session, statement, \
        current_stream, logger

import radio_list


app = Flask(__name__)
ask = Ask(app, '/')
logger.setLevel(logging.INFO)


@ask.default_intent
@ask.launch
def launch():
    if 'radio_name' in session:
        speech = 'Resuming {}'.format(session['radio_name'])
        return audio(speech).play(session['radio_url'])
    card_title = 'French Radio'
    text = 'Tell me the name of a French Radio that you want to listen to.'
    prompt = 'I did not get that, can you repeat the name of the Radio?.'
    return question(text).reprompt(prompt).simple_card(card_title, text)


def find_radio(utterance):
    utterance = utterance.lower()
    for radio, info in radio_list.data.items():
        for u in info['uterrances']:
            if u == utterance:
                return (radio, info)


@ask.intent('PlayRadioIntent', mapping={'radioname': 'RadioName'})
def play_radio(radioname):
    if not radioname:
        logger.info('PlayRadioIntent: Empty intent slot')
        return statement('Sorry, I do not understand the name of this Radio.')
    radio = find_radio(radioname)
    if not radio:
        logger.info('PlayRadioIntent: Cannot find radio {}'.format(radioname))
        return statement('Sorry, I cannot find the radio {}'.format(radioname))
    (radio, info) = radio
    msg = 'Playing {}'.format(radio)
    resp = audio(msg).play(info['url']).simple_card(msg)
    return resp


@ask.intent('AMAZON.PauseIntent')
def pause():
    return audio().stop()


@ask.intent('AMAZON.ResumeIntent')
def resume():
    return audio('Resuming.').play(current_stream.url)


@ask.intent('AMAZON.StopIntent')
def stop():
    return audio().clear_queue(stop=True)


@ask.intent('AMAZON.StartOverIntent')
def startover():
    return audio('Resuming.').play(current_stream.url)


@ask.on_playback_started()
def started(offset, token, url):
    logger.info('Started to play {}; offset: {}'.format(url, offset))
    return "{}", 200


@ask.on_playback_nearly_finished()
def nearly_finished():
    return "{}", 200


@ask.on_playback_stopped()
def stopped(offset, token):
    return "{}", 200


@ask.on_playback_finished()
def finished():
    return statement('Radio stream ended.')


@ask.on_playback_failed()
def failed(*args):
    logger.error('Playback failed on url: {}; {}'.format(current_stream.url,
                                                         args))


@ask.session_ended
def session_ended():
    return "{}", 200


@app.after_request
def after_request(response):
    if response.status_code == 200:
        return response
    ts = time.strftime('[%Y-%b-%d %H:%M]')
    data = json.loads(request.data)
    logger.error('###########\nREQUEST {} {} {} {} {} {} \nBODY: {}'.format(
                  ts,
                  request.remote_addr,
                  request.method,
                  request.scheme,
                  request.full_path,
                  response.status,
                  pprint.pformat(data)))
    logger.error('###\nRESPONSE {} \nBODY: {} \n###########'.format(
                 response.status,
                 response.data))
    return response


def lambda_handler(event, _context):
    """AWS Lambda entrypoint
    arn:aws:lambda:us-west-2:201736817473:function:alexa-frenchradio_playradio
    """
    return ask.run_aws_lambda(event)


if __name__ == '__main__':
    # Used for debug only
    app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(host='0.0.0.0', port=1080)
