class StatusCodeError(Exception):
    """ Неверный код статуса """
    pass

class ApiNotFoundError(Exception):
    """ Нет доступа к API """
    pass
