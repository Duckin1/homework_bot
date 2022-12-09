import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram.error import BadRequest

from exceptions import StatusCodeError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 60 * 10
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
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


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
    try:
        payload = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if not response.status_code == 200:
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
        logging.error(message)
    if homeworks_list is None:
        message = 'В ответе API нет словаря с домашками'
        logging.error(message)
        raise TypeError("В запросе API нет list с домашками")
    if not homeworks_list:
        message = 'За последнее время нет домашек'
        logging.error(message)
        raise ValueError("Нет домашней работы")
    if not isinstance(homeworks_list, list):
        message = 'В ответе API домашки представлены не списком'
        logging.error(message)
        raise TypeError("Wrong Type baby!")
    return homeworks_list


def parse_status(homework):
    """Извлекает о конкретной домашней работе статус этой работы."""
    if 'status' not in homework:
        raise KeyError('Ошибка доступа по ключу homework_name: {key_error}')
    elif homework.get('status') not in HOMEWORK_VERDICTS:
        raise KeyError('Ошибка доступа по ключу status: {key_error}')
    elif 'homework_name' not in homework:
        raise KeyError('homework_name нет в домашней работе {key_error}')
    verdict = homework.get('status')
    homework_name = homework.get('homework_name')
    message = HOMEWORK_VERDICTS[verdict]

    return (
        f'Изменился статус проверки работы "'
        f'{homework_name}"'
        f' {verdict}'
        f' {message}'
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Ошибка доступности переменных окружения'
        logging.critical(message)
        sys.exit([message])
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    old_message = None
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
                logging.debug('нет новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != old_message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                old_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )
    main()
