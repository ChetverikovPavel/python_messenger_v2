import logging
import sys
import logs.configs.server_log_config
import logs.configs.client_log_config

if sys.argv[0].find('server') == -1:
    LOGGER = logging.getLogger('client')
else:
    LOGGER = logging.getLogger('server')


class Port:
    def __set__(self, instance, value):
        if str(value).isnumeric():
            if int(value) < 1024 or int(value) > 65535:
                if sys.argv[0].find('client') == -1:
                    LOGGER.critical(f'Попытка запуска сервера с недопустимым портом: {value}. '
                                    f'Порт сервера должен быть в диапазоне от "1024" до "65535"', stacklevel=2)
                    exit(1)
                else:
                    LOGGER.critical(f'Попытка подключения к серверу с недопустимым портом: {value}. '
                                    f'Порт сервера должен быть в диапазоне от "1024" до "65535"', stacklevel=2)
                    exit(1)
            instance.__dict__[self.name] = value
        else:
            LOGGER.critical(f'Введён недопустимый порт: {value}. '
                            f'Порт должен быть числом в диапазоне от "1024" до "65535"', stacklevel=2)
            exit(1)

    def __set_name__(self, owner, name):
        self.name = name
