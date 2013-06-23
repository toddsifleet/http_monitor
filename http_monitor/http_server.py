import SimpleHTTPServer
import SocketServer
import socket
import os
import threading
from functools import partial
import urlparse
import cgi
import StringIO
from datetime import datetime
import Cookie

class StaticHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    '''A basic request TestHandler

        Two unique rules:
            routes '/' -> assets/index.html
            routes '/path/to/page' -> assets/path/to/page.html'


        This disables logging

    '''

    def do_GET(self):
        if self.path == '/':
            self.path = os.path.join('assets', 'index.html')
        else:
            self.path = 'assets%s' % self.path
        return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def log_message(*args):
        return

class MonitorHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, message_queue, *args, **kwargs):
        self.message_queue = message_queue
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(parsed_path.query)
        self.payload = {
            'params': dict_to_array(params, lambda x: x[0])
        }
        print params
        self.handle_request()
        
    def do_POST(self):
        length = int(self.headers.getheader('content-length'))
        body = self.rfile.read(length)
        fake_body = StringIO.StringIO()
        fake_body.write(body)
        fake_body.seek(0)
        field_storage = cgi.FieldStorage(
            fp = fake_body,
            headers = self.headers,
            environ = {
                'REQUEST_METHOD':'POST',
                'CONTENT_TYPE': self.headers.getheader('content-type'),
            }
        )
        
        params = []
        for key in field_storage.keys():
            params.append({
                'name': key,
                'value': field_storage[key].value
            })
        self.payload = {
            'content_length': length,
            'request_body': body,
            'params': params
        }
        self.handle_request()

    def handle_request(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.put_request()
        self.wfile.write(self.command)

    def get_cookies(self):
        cookie = Cookie.SimpleCookie()
        if self.headers.has_key('cookie'):
            cookie = Cookie.SimpleCookie(self.headers.getheader("cookie"))
        return dict_to_array(cookie, lambda x: x.value)

    def put_request(self):
        if 'cookie' in self.headers:
            self.payload['cookies'] = self.get_cookies()
            del self.headers['cookie']

        self.payload.update({
            'method': self.command,
            'headers': dict_to_array(self.headers),
            'path': self.path,
            'timestamp': datetime.now().strftime("%c")
        })
        self.message_queue.put(self.payload)
        print self.payload

    def log_message(*args):
        pass

class TestServer(SocketServer.TCPServer):
    '''A reusable test server

        Since this server may be stopped and restarted a lot
        we don't want to run into the "address already in use" error
        this resolves those problems
    '''
    allow_reuse_address = True


class Server(threading.Thread):
    notification_string = "Serving website at: %s:%d"
    def __init__(self, handler, port = 8080):
        '''A single threaded SimpleHTTPServer

            This creates a daemon thread that sits and listens for web requests
            the thread stays alive untill the parent thread dies.

            By default we listen at localhost:8080
        '''
        self.handler = handler
        self.host = 'localhost'
        self.port = port
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        '''Start the server

            Starts the server this function blocks this thread until
            the parent thread dies clossing this thread.
        '''
        self.server = TestServer(('', self.port), self.handler)
        print self.notification_string % (self.host, self.port)
        self.server.serve_forever()


class MonitorServer(Server):
    notification_string = "Monitoring traffic at: %s:%d"
    def __init__(self, messages, port = 8080):
        Server.__init__(self, partial(MonitorHandler, messages), port)


def dict_to_array(input, value_transform = lambda x: x):
    output = []
    for name, value in input.items():
        name, value = name.strip(), value_transform(value).strip()
        if not (name or value):
            continue 
        output.append({
            'name': name,
            'value': value
        })
    return output    
