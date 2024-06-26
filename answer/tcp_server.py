import json
import atexit
import socket
import logging
import threading
from datetime import datetime, timedelta
import configparser

config = configparser.ConfigParser()
config.read('/home/mininet/Captive-Portal/config.ini')
TCP_server_ip = config['DEFAULT']['TCP_server_ip']
TCP_server_port = int(config['DEFAULT']['TCP_server_port'])
captive_portal_mac = config['DEFAULT']['captive_portal_mac']
internet_mac = config['DEFAULT']['internet_mac']
server_log = config['DEFAULT']['server_log']

# Setup logging
logging.basicConfig(filename=server_log, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

valid_time = timedelta(days=1)

class MACSet:
    def __init__(self):
        self.approved_macs = {}

    def add_mac(self, mac):
        self.approved_macs[mac] = datetime.now()
        return True

    def remove_mac(self, mac):
        if mac in self.approved_macs:
            del self.approved_macs[mac]
            logging.info(f"Mac {mac} removed.")
            return True
        else:
            logging.info(f"Mac {mac} not found.")
            return False

    def check_mac(self, mac):
        if mac in self.approved_macs:
            logging.info(f"Mac {mac} is approved, added on {self.approved_macs[mac]}. {datetime.now()-self.approved_macs[mac] < valid_time}")
            return True
        else:
            logging.info(f"Mac {mac} is not approved.")
            return False

class Server:
    def __init__(self, hMAC=captive_portal_mac, iMAC=internet_mac, host=TCP_server_ip, port=TCP_server_port):
        self.host = host
        self.port = port
        self.hMAC = hMAC
        self.iMAC = iMAC
        self.MACSet = MACSet()
        self.server_socket = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
    
    def handle_client(self, conn, addr):
        logging.info(f'Connected by: {addr}')
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                try:
                    request = json.loads(data)
                    logging.info(f"Received message: {request}")
                    response = self.handle_request(request)
                    conn.sendall(json.dumps(response).encode())
                except json.JSONDecodeError:
                    response = {'error': 'Invalid JSON'}
                    conn.sendall(json.dumps(response).encode())
        finally:
            conn.close()

    def run_tcp_server(self):
        """Runs a TCP server that stays open even if the client disconnects."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.server_socket = s
            s.bind((self.host, self.port))
            s.listen()
            logging.info(f"Server listening on {self.host}:{self.port}")
            while not self.stop_event.is_set():  # Stay open forever
                conn, addr = s.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
    
    def get_host(self):
        with self.lock:
          return {'result': self.hMAC}
    
    def set_host(self, value):
        with self.lock:
          self.hMAC = value
          return {'result': True}
    
    def get_internet(self):
        with self.lock:
          return {'result': self.iMAC}
    
    def set_internet(self, value):
        with self.lock:
          self.iMAC = value
          return {'result': True}
    
    def add_mac(self, value):
        with self.lock:
          return {'result': self.MACSet.add_mac(value)}
    
    def check_mac(self, value):
        with self.lock:
          return {'result': self.MACSet.check_mac(value)}

    def handle_request(self, request):
        """Handle incoming requests and return a response."""
        command = request.get('command')
        response = {'error': 'Invalid command'}
        if command == 'getHost':
            response = self.get_host()
        elif command == 'setHost':
            response = self.set_host(request.get('value'))
        elif command == 'getInternet':
            response = self.get_internet()
        elif command == 'setInternet':
            response = self.set_internet(request.get('value'))
        elif command == 'add':
            response = self.add_mac(request.get('value'))
        elif command == 'check':
            response = self.check_mac(request.get('value'))
        return response

    def stop_server(self):
        """Stops the TCP server."""
        logging.info("Stopping server...")
        self.stop_event.set()
        if self.server_socket:
            self.server_socket.close()

if __name__ == '__main__':
    server = Server()
    server.run_tcp_server()
    atexit.register(server.stop_server())
