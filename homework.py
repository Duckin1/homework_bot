import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from telegram.error import BadRequest

from exceptions import StatusCodeError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 60 * 10  # Нельзя менять, пайтест не проходит
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения.

    которые необходимы для работы программы.
    """
    if all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        return True

    enviroments = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for name, env in enviroments.items():
        if not env:
            logging.critical('Отсутствует обязательная переменная окружения:'
                             f'{name} Программа принудительно остановлена.')
    return False


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение успешно отправлено')
    except BadRequest as error:
        logging.error(f'Сбой при отправке сообщения: {error}', exc_info=True)
    except telegram.TelegramError as error:
        logging.error(
            f'При отправке сообщения в телеграмм произошла ошибка: {error}',
            exc_info=True
        )


def get_api_answer(timestamp):
    """Делает запрос к API сервису Яндекс.Практикума."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if not response.status_code == HTTPStatus.OK:
            raise StatusCodeError('Статус кода не 200')
        return response.json()
    except requests.RequestException:
        logging.error(f'Нет доступа к API яндекса: {ENDPOINT}', exc_info=True)


def check_response(response):
    """Проверяет корректность данных, запрошенных от API Практикум.Домашка."""
    try:
        homeworks_list = response['homeworks']
    except KeyError as key_error:
        message = f'Ошибка доступа по ключу homeworks: {key_error}'
        raise KeyError(message)
    if not homeworks_list:
        message = 'В запросе API нет list с домашками'
        logging.error(message)
        raise TypeError(message)
    if not homeworks_list:
        message = 'За последнее время нет домашек'
        logging.error(message)
        raise ValueError('Нет домашней работы')
    if not isinstance(response, dict):
        raise TypeError(
            f'при получении ответа от api {response} пришёл не словарь '
        )
    if not isinstance(homeworks_list, list):
        message = 'В ответе API домашки представлены не списком'
        logging.error(message)
        raise TypeError('Wrong Type baby!')
    return homeworks_list


def parse_status(homework):
    """Извлекает о конкретной домашней работе статус этой работы."""
    if 'status' not in homework:
        raise KeyError('Ошибка доступа по ключу homework_name')
    elif homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError('Ошибка доступа по ключу status')
    elif 'homework_name' not in homework:
        raise KeyError('homework_name нет в домашней работе')
    verdict = homework['status']
    homework_name = homework['homework_name']
    message = HOMEWORK_VERDICTS[verdict]

    return (
        f'Изменился статус проверки работы "'
        f'{homework_name}"'
        f'{verdict}'
        f'{message}'
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Ошибка доступности переменных окружения'
        sys.exit([message])
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    old_message = None
    old_response = None
    while True:
        try:
            if type(timestamp) is not int:
                raise SystemError('В функцию передана не дата')
            api_answer = get_api_answer(timestamp)
            response = check_response(api_answer)
            if response != old_response:
                homework_status = parse_status(response[0])
                if homework_status is not None:
                    send_message(bot, homework_status)
                    old_response = response
            else:
                logging.debug('нет новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            if message != old_message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                old_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )
    main()
