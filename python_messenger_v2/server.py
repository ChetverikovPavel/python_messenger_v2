import socket
import sys
import logging
import select
import argparse
import threading
import logs.configs.server_log_config
from common.variables import *
from common.utils import get_message, send_message
from decors import log
from descripts import Port
from metaclasses import ServerVerifier
from server_database import ServerStorage

# Инициализация логирования сервера
SERVER_LOGGER = logging.getLogger('server')


# Парсер аргументов коммандной строки
# @log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_ip = namespace.a
    server_port = namespace.p
    return server_ip, server_port


# Основной класс сервера
class Server(threading.Thread, metaclass=ServerVerifier):
    server_port = Port()

    def __init__(self, server_ip, server_port, database):
        # Параметры подключения
        self.server_ip = server_ip
        self.server_port = server_port
        self.database = database

        # Список подключенных клиентов
        self.clients = []

        # Список сообщений на отправку
        self.messages = []

        # Словарь имен и соответствующие им сокеты
        self.names = dict()

        super().__init__()

    # @log
    def init_socket(self):
        SERVER_LOGGER.info(f'Запущен сервер, адрес сервера: {self.server_ip} '
                           f'порт для подключений: {self.server_port} ')
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.server_ip, self.server_port))
        server_sock.settimeout(0.5)
        self.sock = server_sock
        self.sock.listen()

    # @log
    def run(self):
        self.init_socket()

        while True:
            try:
                client_sock, client_addr = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Подключен клиент с адресом {client_addr}')
                self.clients.append(client_sock)

            recv_data_list = []
            send_data_list = []
            err_data_list = []

            try:
                if self.clients:
                    recv_data_list, send_data_list, err_list = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except Exception:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                           f'отключился от сервера.')
                        self.clients.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_list)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна.')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    # @log
    def process_client_message(self, message, client):
        SERVER_LOGGER.debug(f'Разбор сообщения от клиента: {message}')
        if ACTION in message and message[ACTION] == PRESENCE and \
                TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, {
                    STATUS_CODE: 200,
                    STATUS: 'OK'
                })
            else:
                send_message(client, {
                    STATUS_CODE: 400,
                    STATUS: 'Bad Request',
                    ERROR: 'Имя пользователя уже занято.'
                })
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE \
                and TIME in message and MESSAGE_TEXT in message \
                and DESTINATION in message and SENDER in message:
            self.messages.append(message)
            self.database.process_message(message[SENDER], message[DESTINATION])
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])

            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        else:
            send_message(client, {
                STATUS_CODE: 400,
                STATUS: 'Bad Request',
                ERROR: 'Некоректный запрос'
            })
            return

    # @log
    def process_message(self, message, socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in socks:
            send_message(self.names[message[DESTINATION]], message)
            SERVER_LOGGER.info(f'Отправленно сообщение пользователю {message[DESTINATION]} '
                               f'от пользователя {message[SENDER]}')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in socks:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')


def print_help():
    print('Поддерживаемые команды:')
    print('users() - список всех известных пользователей')
    print('connected() - список подключенных пользователей')
    print('login_history() - история входов пользователя')
    print('help() - вывод поддерживаемых команд')
    print('exit() - завершение работы сервера')


def main():
    server_ip, server_port = arg_parser()
    database = ServerStorage()
    server = Server(server_ip, server_port, database)
    server.daemon = True
    server.start()

    print_help()

    while True:
        command = input('Введите команду: \n')
        if command == 'help()':
            print_help()
        elif command == 'users()':
            for user in sorted(database.users_list()):
                print(f'Пользователь: {user[0]}, последний вход: {user[1]}')
        elif command == 'connected()':
            for user in sorted(database.active_users_list()):
                print(f'Пользователь: {user[0]}, подключен: {user[1]}:{user[2]},'
                      f' время установки подключения: {user[3]}')
        elif command == 'login_history()':
            name = input('Введите имя пользователя для просмотра истории. '
                         'Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        elif command == 'exit()':
            break
        else:
            print('Команда не распознана.')


if __name__ == "__main__":
    main()
