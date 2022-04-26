import logging
import sys
import inspect
import logs.configs.server_log_config
import logs.configs.client_log_config

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func_to_log):
    def log_saver(*args, **kwargs):
        rtrn = func_to_log(*args, **kwargs)
        LOGGER.debug(f'Вызвана функция: {func_to_log.__name__} с параметрами: {args}, {kwargs}. '
                     f'Результат работы функции: {rtrn}. '
                     f'Вызов из функции: {inspect.stack()[1][3]} ', stacklevel=2)
        return rtrn

    return log_saver
