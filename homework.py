import logging
import os

import requests

import telegram
from datetime import time
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = 'y0_AgAAAABI78NEAAYckQAAAADV5LaO1Ay2TPtIQxm2HzNBdCXnPK14P48'
TELEGRAM_TOKEN = '5553314893:AAGml8iWXCeja37cjdvWjChn5jAPOBM0ELs'
TELEGRAM_CHAT_ID = 561180852

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
timestamp = {'from_date': 1664917200}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения,
    которые необходимы для работы программы."""

    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))

def send_message(bot, message):
    return bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
    response = requests.get(ENDPOINT).json()


def check_response(response):
    response = requests.get('https://api.github.com')



def parse_status(homework):
    pass

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...

    
if __name__ == '__main__':
    main()
    