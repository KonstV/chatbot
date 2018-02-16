import sys
import requests
import argparse
from transitions import Machine

BOT_NAME = "StateMachineChattBot"
TOKEN = "516597529:AAGRqcgWkFNqXoGEEiJggV7A6vvH-naW-Vk"
QUESTIONS = {
    "size": 'Какую вы хотите пиццу?  Большую или маленькую?',
    "pay": 'Как вы будете платить?',
    "check": 'Вы хотите большую пиццу, оплата - наличкой?',
    "thanks": 'Спасибо за заказ'
}
VALID_ANSWERS = {
    "size": ['Большую', 'Большая'],
    "pay": ['Наличкой', 'Наличными'],
    "check": ['Да'],
}


class BotHandler():

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp


class ChatClient():
    pass


class ChatBotBrains(object):

    states = ['size', 'pay', 'check', 'thanks']

    def __init__(self):

        self.machine = Machine(model=None, states=ChatBotBrains.states, initial='size')

        self.machine.add_transition('next', 'size', 'pay')

        self.machine.add_transition('next', 'pay', 'check')

        self.machine.add_transition('next', 'check', 'thanks')

        self.machine.add_transition('next', 'thanks', 'size')

    def add_model(self, model):
        self.machine.add_model(model)


def test():
    print("Testing started")
    chat_bot_brains = ChatBotBrains()
    c0 = ChatClient()
    c1 = ChatClient()
    chat_bot_brains.add_model(c0)
    chat_bot_brains.add_model(c1)
    assert(c0.state == 'size')
    assert(c1.state == 'size')
    c0msg = 'Test'
    if c0msg in VALID_ANSWERS[c0.state]:
        c0.next()
    assert(c0.state == 'size')
    assert(c1.state == 'size')
    c0msg = 'Большую'
    if c0msg in VALID_ANSWERS[c0.state]:
        c0.next()
    assert(c0.state == 'pay')
    assert(c1.state == 'size')
    c0msg = 'Наличкой'
    if c0msg in VALID_ANSWERS[c0.state]:
        c0.next()
    assert(c0.state == 'check')
    assert(c1.state == 'size')
    c1msg = 'Наличкой'
    if c1msg in VALID_ANSWERS[c1.state]:
        c1.next()
    assert(c0.state == 'check')
    assert(c1.state == 'size')
    c1msg = 'Большую'
    if c1msg in VALID_ANSWERS[c1.state]:
        c1.next()
    assert(c0.state == 'check')
    assert(c1.state == 'pay')
    c0msg = 'Да'
    if c0msg in VALID_ANSWERS[c0.state]:
        c0.next()
    assert(c0.state == 'thanks')
    assert(c1.state == 'pay')
    c1msg = 'Наличкой'
    if c1msg in VALID_ANSWERS[c1.state]:
        c1.next()
    assert(c0.state == 'thanks')
    assert(c1.state == 'check')
    c1msg = 'Да'
    if c1msg in VALID_ANSWERS[c1.state]:
        c1.next()
    assert(c0.state == 'thanks')
    assert(c1.state == 'thanks')
    print("Testing finished successfully")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true')
    args = parser.parse_args()

    if args.test:
        test()
        return

    data_source = BotHandler(TOKEN)
    chat_bot_brains = ChatBotBrains()
    clients = {}

    new_offset = None

    while True:
        updates = data_source.get_updates(new_offset)

        for u in updates:
            update_id = u['update_id']
            chat_text = u['message']['text']
            chat_id = u['message']['chat']['id']
            if chat_id not in clients:
                clients[chat_id] = ChatClient()
                chat_bot_brains.add_model(clients[chat_id])
                data_source.send_message(chat_id, QUESTIONS[clients[chat_id].state])
            else:
                if chat_text in VALID_ANSWERS[clients[chat_id].state]:
                    clients[chat_id].next()
                data_source.send_message(chat_id, QUESTIONS[clients[chat_id].state])
                if clients[chat_id].state == 'thanks':
                    del clients[chat_id]

            new_offset = update_id + 1


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
