# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from django.http.response import HttpResponse

import json, os, re, requests
from pprint import pprint


PAGE_ACCESS_TOKEN = \
    u'EAAZAgryR1MzwBAMDwZArm05snOdaWDsw5lsxm9IGIrrmjmFWel94mUEVbbBBZC1TYVYwk8d \
    kl9H1HuUE5DnQiXa0UQp0Sr36kOHtL4ZBvIKgmvgEXv5saMOwLCDbnK8JTcC7gZC7g59wBtqYt \
    oZBYZC1vX7jJRqa3Vb6VvOZACGosQZDZD'
VERIFY_TOKEN = u'782654920'
POSSIBLE_RESPONSES = {
    'go out': ["Where would you like to go tonight?"]
}


class BotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == os.environ.get('VERIFY_TOKEN'):
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

                    # Assuming the sender only sends text
                    # Non-text messages like stickers, audio, pictures
                    # are sent as attachments and must be handled accordingly.
                    post_facebook_message(
                        message['sender']['id'],
                        message['message']['text']
                    )
        return HttpResponse()


def post_facebook_message(fbid, recieved_message):
    tokens = re.sub(r"[^a-zA-Z0-9\s]",' ',recieved_message).lower().split()
    response_text = ''

    for token in tokens:
        if token in POSSIBLE_RESPONSES:
            # Personalization
            user_details_url = "https://graph.facebook.com/v2.6/%s"%fbid
            user_details_params = {
                'fields': 'first_name,last_name,profile_pic',
                'access_token': os.environ.get('PAGE_ACCESS_TOKEN')
            }
            user_details = requests.get(user_details_url, user_details_params).json()

            # Insert decision tree response here
            response_text = POSSIBLE_RESPONSES[token]
            if token == 'go out':
                response_text = "Hi {}! ".format(user_details['first_name']) \
                    + response_text
            break

    if not response_text:
        response_text = "I don't understand what you're saying.\n\
Type 'go out' for nightlife suggestions!"

    post_message_url = \
        'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            os.environ.get('PAGE_ACCESS_TOKEN')
        )
    response_msg = json.dumps({
        "recipient": {"id": fbid},
        "message": {"text": response_text}
    })
    status = requests.post(
        post_message_url,
        headers={"Content-Type": "application/json"},
        data=response_msg
    )
    pprint(status.json())
