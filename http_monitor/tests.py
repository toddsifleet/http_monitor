import http_monitor
import http_server
import socket_server
import unittest
import functools

def dummy_func(*args, **kwargs):
    return args, kwargs

class DummyClient:
    def send(self, *args):
        self.called = True
        return True

class Test_HttpMonitor(unittest.TestCase):
    def setUp(self):
        self.old_start_http_servers = http_monitor.start_http_servers
        self.old_start_socket_server = http_monitor.start_socket_server
        http_monitor.start_http_servers = dummy_func
        http_monitor.start_socket_server = dummy_func

    def tearDown(self):
        http_monitor.start_http_servers = self.old_start_http_servers
        http_monitor.start_socket_server = self.old_start_socket_server

    def test_process_clients(self):
        monitor = http_monitor.HttpMonitor()
        for i in range(5):
            monitor.new_connections.put(i)

        monitor.process_clients()
        self.assertEqual(monitor.clients, range(5))

    def test_process_messages(self):
        monitor = http_monitor.HttpMonitor()
        monitor.clients = True
        for i in range(5):
            monitor.messages.put(i)

        results = []
        monitor.send_message = lambda x: results.append(x)
        monitor.process_messages()
        self.assertEqual(results, range(5))   

    def test_send_message(self):
        monitor = http_monitor.HttpMonitor()
        clients = [DummyClient() for i in range(3)]
        monitor.clients = clients
        monitor.send_message(10)

        for c in monitor.clients:
            self.assertTrue(c.called)

        self.assertEqual(monitor.clients, clients)
if __name__ == '__main__':
    unittest.main()
