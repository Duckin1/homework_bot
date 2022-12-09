

class UnknownHostExceptionExample(Exception):
    ''' Неизвестный статус домашки '''
    pass


class MissingTokenException(Exception):
    ''' Ошибка токена или телеграм чата '''
    pass


class StatusCodeError(Exception):
    ''' Неверный код статуса '''
    pass
