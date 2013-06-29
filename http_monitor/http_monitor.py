import http_server
import socket_server
import Queue
import json

def start_http_servers(messages, static_port = 8080, monitor_port = 8888):
    #server to serve the tool
    http_server.Server(http_server.StaticHandler, static_port).start()
    #server to monitor requests
    http_server.MonitorServer(messages, monitor_port).start()


def start_socket_server(new_connections, port = 1234):
    socket_server.WebSocketServer(new_connections, port).start()


class HttpMonitor(object):
    def __init__(self):
        self.new_connections = Queue.Queue()
        self.messages = Queue.Queue()
        self.clients = []

    def run(self):
        start_http_servers(self.messages)
        start_socket_server(self.new_connections)
        while True:
            while not self.new_connections.empty():
                self.clients.append(self.new_connections.get())
            if not self.messages.empty() and self.clients:
                self.send_message(self.messages.get())

    def send_message(self, message):
        clients = self.clients[:]
        self.clients = []
        for client in clients:
            if client.send(json.dumps(message)):
                self.clients.append(client)

monitor = HttpMonitor()
monitor.run()


