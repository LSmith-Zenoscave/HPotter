import re

from hpotter.env import logger, start_shell, get_shell_container, write_db
from hpotter import tables
from hpotter.tables import SHELL_COMMAND_LENGTH


def get_string(client_socket, limit=SHELL_COMMAND_LENGTH, telnet=False):
    character = client_socket.recv(1)
    if not telnet:
        client_socket.send(character)

    # while there are telnet commands
    while telnet and character == b'\xff':
        # skip the next two as they are part of the telnet command
        client_socket.recv(1)
        client_socket.recv(1)
        character = client_socket.recv(1)

    string = ''
    while character not in (b'\n', b'\r'):
        if character == b'\b':      # backspace
            string = string[:-1]
        elif character == '\x15':   # control-u
            string = ''
        elif ord(character) > 127:
            logger.debug('Meta character')
            raise UnicodeError('Meta character')
        elif len(string) > limit:
            logger.debug('Too many characters')
            raise IOError('Too many characters')
        else:
            string += character.decode('utf-8')

        character = client_socket.recv(1)
        if not telnet:
            client_socket.send(character)

    if not telnet:
        client_socket.send(b'\n')

    # read the newline
    if telnet and character == b'\r':
        character = client_socket.recv(1)

    logger.debug('get_string returning %s', string.strip())
    return string.strip()


def deal_with_dots(path, workdir):
    while path.startswith('.'):
        if path == '.':
            return '/' if workdir == '' else workdir
        if path.startswith('./'):
            path = path[2:]
            continue

        # strip out last element
        workdir = re.sub(r'/[^/]*/?$', '', workdir)

        # remove front part of path
        path = path[3:] if path.startswith('../') else path[2:]

    if path.endswith('/'):
        path = path[:-1]

    if workdir == '':
        return '/'
    elif path == '':
        return workdir
    else:
        return workdir + '/' + path


def change_directory(command, workdir):
    directory = command.split(' ')

    # a bare cd
    if len(directory) == 1:
        return workdir

    directory = directory[1]

    if directory.startswith('.'):
        return deal_with_dots(directory, workdir)

    if directory == '/':
        return '/'

    if workdir == '/':
        return workdir + directory

    return workdir + '/' + directory


def fake_shell(client_socket, connection, prompt, telnet=False):
    start_shell()

    command_count = 0
    workdir = '/'
    while command_count < 4:
        client_socket.sendall(prompt)

        try:
            command = get_string(client_socket, telnet=telnet)
            command_count += 1
        except Exception as exception:
            logger.debug(exception)
            client_socket.close()
            break

        if command == '':
            continue

        if command == 'exit':
            break

        if command.startswith('cd'):
            workdir = change_directory(command, workdir)

        logger.debug('Shell workdir %s', workdir)

        cmd = tables.ShellCommands(command=command, connection=connection)
        write_db(cmd)

        exit_code, output = get_shell_container().exec_run(command,
                                                           workdir=workdir)

        logger.debug('Shell exit_code %s', str(exit_code))
        logger.debug('Shell output %s', str(output))

        output = output.replace(b'\n', b'\r\n')

        if exit_code in (126, 127):
            client_socket.sendall(command.encode('utf-8') +
                                  b': command not found\r\n')
        else:
            client_socket.sendall(output)
