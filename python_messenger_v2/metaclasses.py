import dis


class ServerVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        attrs = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        if 'connect' in methods:
            raise TypeError('Использование метода "connect" недопустимо на стороне сервера.')
        if not ('AF_INET' in attrs and 'SOCK_STREAM' in attrs):
            raise TypeError('Недопустимые параметры сокета сервера.')

        super().__init__(clsname, bases, clsdict)


class ClientMainVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        attrs = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        for command in ['accept', 'listen']:
            if command in methods:
                raise TypeError('Недопустимые методы сокета клиента.')
        if not ('AF_INET' in attrs and 'SOCK_STREAM' in attrs):
            raise TypeError('Недопустимые параметры сокета клиента.')

        super().__init__(clsname, bases, clsdict)


class ClientOtherVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
        if 'socket' in methods:
            raise TypeError('Недопустимо создание сокета в потоках.')

        super().__init__(clsname, bases, clsdict)
