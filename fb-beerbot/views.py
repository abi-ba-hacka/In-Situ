# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from django.http.response import HttpResponse

import json, os, re, requests
from pprint import pprint
from random import choice
from wit import Wit


PAGE_ACCESS_TOKEN = \
    u'EAAZAgryR1MzwBAMDwZArm05snOdaWDsw5lsxm9IGIrrmjmFWel94mUEVbbBBZC1TYVYwk8d \
    kl9H1HuUE5DnQiXa0UQp0Sr36kOHtL4ZBvIKgmvgEXv5saMOwLCDbnK8JTcC7gZC7g59wBtqYt \
    oZBYZC1vX7jJRqa3Vb6VvOZACGosQZDZD'
VERIFY_TOKEN = u'782654920'
POSSIBLE_RESPONSES = {
    'go out': ["Where would you like to go tonight?"]
}


POSSIBLE_BARS = {
    'barrio norte': [{
        'name': 'Patagonia Facultad de Medicina',
        'address': 'Pasteur 706'
    }, {
        'name': 'Patagonia Paraguay y Uruguay',
        'address': 'Paraguay 1448'
    }, {
        'name': 'Patagonia Arenales',
        'address': 'Arenales 2707'
    }],
    'san telmo': [{
        'name': 'Patagonia San Telmo – Perú',
        'address': 'Perú 602'
    }, {
        'name': 'Patagonia San Telmo – Plaza Dorrego',
        'address': 'Don Anselmo Aieta 1081'
    }],
    'palermo': [{
        'name': 'Patagonia Córdoba y Mario Bravo',
        'address': 'Av. Córdoba 3573'
    }, {
        'name': 'Patagonia Distrito Arcos',
        'address': 'Paraguay 4979'
    }],
    'recoleta': [{
        'name': 'Patagonia Callao y Viamonte',
        'address': 'Callao 650'
    }],
    'chacarita': [{
        'name': 'Patagonia Paraguay y Riobamba',
        'address': 'Paraguay 1900'
    }],
    'cañitas': [{
        'name': 'Patagonia Cañitas',
        'address': 'Andres Arguibel 2831'
    }],
    'monsterrat': [{
        'name': 'Patagonia Av. de Mayo',
        'address': 'Av de Mayo 702'
    }],
}


USER_NAME = None


WIT_TOKEN = os.environ.get('WIT_TOKEN')


class BotView(generic.View):
    def get(self, request, *args, **kwargs):
        req_verify_token = self.request.GET['hub.verify_token']
        if req_verify_token == os.environ.get('VERIFY_TOKEN'):
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token.')

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))

        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:

                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events
                if 'message' in message:
                    # Print the message to the terminal
                    pprint(message)

                    fbid = message['sender']['id']
                    text = message['message']['text']

                    # Let's forward the message to the Wit.ai Bot Engine
                    # We handle the response in the function send()
                    client.run_actions(session_id=fbid, message=text)
        return HttpResponse()


def post_fb_message(fbid, text):
    """
    Function for returning response to messenger
    """
    data = {
        'recipient': {'id': fbid},
        'message': {'text': text}
    }
    # Setup the query string with your PAGE TOKEN
    qs = 'access_token=' + PAGE_ACCESS_TOKEN

    # Send POST request to messenger
    resp = requests.post('https://graph.facebook.com/me/messages?' + qs,
                         json=data)
    return resp.content


def send(request, response):
    """
    Sender function
    """
    # We use the fb_id as equal to session_id
    fbid = request['session_id']
    text = response['text']

    # send message
    post_fb_message(fbid, text)


def get_user_name(fbid):
    if not USER_NAME:
        user_details_url = "https://graph.facebook.com/v2.6/%s"%fbid
        user_details_params = {
            'fields': 'first_name,last_name,profile_pic',
            'access_token': os.environ.get('PAGE_ACCESS_TOKEN')
        }
        user_details = requests.get(user_details_url, user_details_params).json()

        USER_NAME = user_details['first_name']
    return USER_NAME


def first_entity_value(entities, entity):
    """
    Returns first entity value
    """
    if entity not in entities:
        return None
    val = entities[entity][0]['value']
    if not val:
        return None
    return val['value'] if isinstance(val, dict) else val


def find_bar(request):
    context = request['context']
    entities = request['entities']
    neighborhood = first_entity_value(entities, 'location')

    if neighborhood:
        # This is where we could use a weather service api to get the weather.
        random_bar = choice(POSSIBLE_BARS[neighborhood.lower()])
        context['bar_name'] = random_bar['name']
        context['bar_address'] = random_bar['address']
        # TODO: Put in Location response here (Google Maps or otherwise).
        # context['map_to_bar'] = None
        # context['user_name'] = get_user_name(fbid)

        if context.get('missing_location') is not None:
            del context['missing_location']
    else:
        context['missing_location'] = True
        if context.get('bar_name') is not None:
            del context['bar_name']
        if context.get('bar_address') is not None:
            del context['bar_address']
        # if context.get('map_to_bar') is not None:
        #     del context['map_to_bar']
    return context


# Set up Wit.ai client
actions = {
    'send': send,
    'findBar': find_bar,
}

client = Wit(access_token=WIT_TOKEN, actions=actions)
