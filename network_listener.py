import asyncore
import socket
import threading


class NetworkListener(threading.Thread):
    def __init__(self, callback):
        self.host = ''
        self.port = 20098
        self.callback = callback
        super(NetworkListener, self).__init__()
        self.server = None

    def run(self):
        self.server = SimpleServer(self.host, self.port, self.callback)
        asyncore.loop(timeout=1)

    def join(self, timeout=None):
        asyncore.close_all()
        super(NetworkListener, self).join(timeout)


class SimpleServer(asyncore.dispatcher):

    def __init__(self, host, port, callback):
        self.callback = callback
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            handler = SimpleHandler(sock)
            handler.callback = self.callback
            handler.buffer = ''


class SimpleHandler(asyncore.dispatcher_with_send):
    
    def handle_read(self):
        self.buffer += self.recv(4096)
        l = self.buffer.split('\n')
        if len(l) > 1:
            self.buffer = l[len(l)-1]
            [self.callback(a) for a in l[0:len(l)-1]]