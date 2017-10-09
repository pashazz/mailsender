import socket
import ssl

import select
import colorama
import configparser
import base64
import pathlib
import mimetypes

def print_return(method):
    def decorator(*args, **kwargs):
        ret = method(*args, **kwargs)
        print(ret,end='')
        return ret

    return decorator



class MySocket:
    """demonstration class only
      - coded for clarity, not efficiency
    """
    msgsize = 4096
    def __init__(self, sock=None):
        if sock is None:
            self.sock = ssl.wrap_socket(socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM))

        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))
        self.sock.setblocking(False)


    def send(self, message, printit=True):
        if type(message) is str:
            if not message[-2:] == '\r\n':
                if message[-1] == '\n':
                    message = message[:-1]
                message = message + '\r\n'
            msg = message.encode()
        else:
            msg = message
        totalsent = 0
        while totalsent < len(msg):
            try:
                sent = self.sock.send(msg[totalsent:])
            except ssl.SSLWantWriteError as e:
                self.wait_for_write()
                continue

            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

        if printit:
            if type(message) is str:
                print(colorama.Fore.YELLOW + message + colorama.Style.RESET_ALL,end='')
            elif len(message) <= self.msgsize:
                print(colorama.Fore.YELLOW + message.decode() + colorama.Style.RESET_ALL,end='')

            else:
                print(colorama.Fore.YELLOW + "{0} bytes sent".format(totalsent) + colorama.Style.RESET_ALL,end='')


    def wait_for_read(self):
        r, w, x = select.select([self.sock], [], [], 5)
        if self.sock not in r:
            self.wait_for_read()

    def wait_for_write(self):
        r, w, x = select.select([], [self.sock], [], 5)
        if self.sock not in w:
            self.wait_for_read()

    @print_return
    def receive(self):
        chunks = []
        bytes_recd = 0
        while True:
            try:
                chunk = self.sock.recv(self.msgsize)
            except ssl.SSLWantReadError as e:
                if not chunks:
                    self.wait_for_read()
                    continue
                else:
                    break
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks).decode()

    def close(self):
        self.sock.close()

def print_red_base64(base64_string_with_code):
    [code, s] = base64_string_with_code.split()
    print(code + " " + colorama.Fore.RED + base64.decodebytes(s.encode()).decode() + colorama.Style.RESET_ALL)


def sendmail(s : MySocket, mail_from, to, fakefrom, faketo, subject, contents):
    mimetypes.init()
    bound = 'ololo'
    s.send("mail from: <{0}>".format(mail_from))
    s.receive()
    s.send("rcpt to: <{0}>".format(to))
    s.receive()
    s.send("data")
    s.receive()
    s.send("From: {0}".format(fakefrom))
    s.send("To: {0}".format(faketo))
    s.send("Subject: {0}".format(subject))
    if type(contents) is str:
        s.send("Content-Type: text/plain")
        s.send(b'\r\n')
        s.send(contents)
    elif type(contents) is list:
        s.send("Content-Type: multipart/mixed;boundary={0}".format(bound))
        s.send("\r\n")
        for part in contents:
            if isinstance(part, pathlib.Path)and part.exists():
                data = base64.encodebytes(part.read_bytes())
                part = part.absolute()
                mimetype, enc = mimetypes.guess_type(part.as_uri())
                header='Content-Type: {0};name="{1}"\r\nContent-Transfer-Encoding:base64'.format(
                    mimetype, part.name)
            elif isinstance(part, str):
                if not part.endswith('\n'):
                    part = part + '\n'
                data = part.encode()
                header='Content-Type: text/plain;charset=us-ascii\r\nContent-Transfer-Encoding: 7bit'

            s.send("--{0}".format(bound))
            s.send(header)
            s.send(b'\r\n')
            s.send(data)
            s.send(b'\r\n')

        s.send('--{0}'.format(bound))
        s.send(b'Boobooo')

    s.send(b'\r\n.\r\n')

if __name__ == '__main__':
    s = MySocket()
    print("our inputs in yellow")
    print('base64 answers in red')
    s.connect('smtp.yandex.ru', 465)
    s.receive()
    s.send('ehlo smtp.yandex.ru')
    s.receive()
    s.send("auth login")
    recv = s.receive()
    print_red_base64(recv)

    config = configparser.ConfigParser()
    config.read("secret.ini")
    user = config._sections['secret']['user']
    password = config._sections['secret']['password']

    s.send(base64.encodebytes(user.encode()))
    recv = s.receive()
    print_red_base64(recv)

    s.send(base64.encodebytes(password.encode()))
    s.receive()
    sendmail(s,'hl3.0@yandex.ru', 'borisov@ispras.ru', 'ololo@ololo.net', 'you', 'want some hw',
                                    ['hello, homework there', pathlib.Path('/home/pasha/sign.png')])

    s.receive()
    s.close()
