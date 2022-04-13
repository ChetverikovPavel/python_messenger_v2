import argparse
import socket
import sys
import time
import json
import logging
import threading
import logs.configs.client_log_config
from common.variables import *
from common.utils import send_message, get_message
from decors import log
from descripts import Port
from metaclasses import ClientMainVerifier, ClientOtherVerifier

# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')


# Парсер аргументов коммандной строки
# @log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, nargs='?')
    parser.add_argument('-n', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_ip = namespace.a
    server_port = namespace.p
    client_name = namespace.n
    return server_ip, server_port, client_name


class Client(metaclass=ClientMainVerifier):
    server_port = Port()

    def __init__(self, server_ip, server_port, client_name):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_name = client_name

    # @log
    def init_socket(self):
        if not self.client_name:
            self.client_name = input('Введите имя пользователя: ')
        else:
            print(f'Клиентский модуль запущен с именем: {self.client_name}')

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
            message_to_server = self.create_presence()
            send_message(self.sock, message_to_server)
            response_from_server = get_message(self.sock)
            checked_response = self.check_presence_response(response_from_server)
            CLIENT_LOGGER.info(f'Установленно соединение с сервером. Ответ сервера: {checked_response}')
            print(f'Установленно соединение с сервером.')

        except ValueError:
            CLIENT_LOGGER.error(f'Получен некоректный ответ от сервера: {response_from_server}')
            sys.exit(1)

    # @log
    def main_loop(self):

        self.init_socket()

        module_sender = ClientSender(self.client_name, self.sock)
        module_sender.daemon = True
        module_sender.start()

        module_receiver = ClientReceiver(self.client_name, self.sock)
        module_receiver.daemon = True
        module_receiver.start()
        CLIENT_LOGGER.debug('Запущены процессы получения и отправки сообщений.')

        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break

    # @log
    def create_presence(self):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
            }
        }
        CLIENT_LOGGER.info(f'Сформировано {PRESENCE} сообщение: {out}')
        return out

    # @log
    def check_presence_response(self, response):
        CLIENT_LOGGER.debug(f'Разбор ответа от сервера: {response}')
        if STATUS_CODE in response and ERROR in response:
            return f'{response[STATUS_CODE]}: {response[STATUS]}, {response[ERROR]}'

        elif STATUS_CODE in response:
            return f'{response[STATUS_CODE]}: {response[STATUS]}'
        raise ValueError


class ClientSender(threading.Thread, metaclass=ClientOtherVerifier):
    def __init__(self, client_name, sock):
        self.client_name = client_name
        self.sock = sock
        super().__init__()

    # @log
    def create_message(self):
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение: ')
        message_dict = {
            ACTION: MESSAGE,
            TIME: time.time(),
            SENDER: self.client_name,
            DESTINATION: to_user,
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформировано сообщение для отправки: {message_dict}')
        send_message(self.sock, message_dict)
        return message_dict

    # @log
    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }

    # @log
    def print_help(self):
        print('Поддерживаемые команды:')
        print('message() - отправить сообщение. Кому отправить сообщение и текст сообщения будет запрошены отдельно.')
        print('help() - вывести подсказки по командам')
        print('exit() - выход из программы')

    # @log
    def run(self):
        print(f'Авторизация под именем: {self.client_name}')
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message()':
                self.create_message()
            elif command == 'help()':
                self.print_help()
            elif command == 'exit()':
                send_message(self.sock, self.create_exit_message())
                print('Завершение сеанса.')
                CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана. Для вывода доступных команд напишите help().')


class ClientReceiver(threading.Thread, metaclass=ClientOtherVerifier):
    def __init__(self, client_name, sock):
        self.client_name = client_name
        self.sock = sock
        super().__init__()

    # @log
    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message and \
                        MESSAGE_TEXT in message and message[DESTINATION] == self.client_name:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    CLIENT_LOGGER.info(f'Получено сообщение от пользователя '
                                       f'{message[SENDER]}: {message[MESSAGE_TEXT]}')
                else:
                    CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')

            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                break


def main():
    server_ip, server_port, client_name = arg_parser()
    client = Client(server_ip, server_port, client_name)
    client.main_loop()


if __name__ == '__main__':
    main()
