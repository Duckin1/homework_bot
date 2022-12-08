import logging
import os
import sys
import requests
import exceptions

import telegram
from datetime import time
from datetime.time import time
from telegram import ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Updater
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 60*10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

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
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except BadRequest as error:
        logging.error(f'Сбой при отправке сообщения: {error}', exc_info=True)
    except telegram.TelegramError as error:
        logging.error(
            f'При отправке сообщения в телеграмм произошла ошибка: {error}',
            exc_info=True
        )


def get_api_answer(timestamp):
    """Делает запрос к API сервису Яндекс.Практикума."""
    try:
        payload = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        return response.json()
    except requests.RequestException:
        logging.error(f'Нет доступа к API яндекса: {ENDPOINT}', exc_info=True)

def check_response(response):
    """Проверяет корректность данных, запрошенных от API Практикум.Домашка."""
    try:
        homeworks_list = response['homeworks']
    except KeyError as key_error:
        message = f'Ошибка доступа по ключу homeworks: {key_error}'
        logger.error(message)
    if homeworks_list is None:
        message = 'В ответе API нет словаря с домашками'
        logger.error(message)
        raise TypeError("В запросе API нет list с домашками")
    if not homeworks_list:
        message = 'За последнее время нет домашек'
        logger.error(message)
        raise ValueError("Нет домашней работы")
    if not isinstance(homeworks_list, list):
        message = 'В ответе API домашки представлены не списком'
        logger.error(message)
        raise TypeError("Wrong Type baby!")
    return homeworks_list


def parse_status(homework):
    """Извлекает о конкретной домашней работе статус этой работы"""
    try:
        homework_name = homework.get('homework_name')
    except KeyError as key_error:
        message = f'Ошибка доступа по ключу homework_name: {key_error}'
        logger.error(message)
    try:
        homework_status = homework.get('status')
    except KeyError as key_error:
        message = f'Ошибка доступа по ключу status: {key_error}'
        logger.error(message)

    verdict = HOMEWORK_VERDICTS[homework_status]
    if verdict is None:
        message = 'Неизвестный статус домашки'
        logger.error(message)
        raise exceptions.UnknownHostExceptionExample(message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    if not check_tokens():
        message = 'Ошибка доступности переменных окружения'
        logger.critical(message)
        raise exceptions.MissingTokenException(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    while True:
        try:
            if type(timestamp) is not int:
                raise SystemError('В функцию передана не дата')
            response = get_api_answer(timestamp)
            response = check_response(response)

            if len(response) > 0:
                homework_status = parse_status(response[0])
                if homework_status is not None:
                    send_message(bot, homework_status)
            else:
                logger.debug('нет новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != old_message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                old_message = message
        finally:
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)
    main()
    