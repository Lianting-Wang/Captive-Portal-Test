import json
import socket
import configparser

config = configparser.ConfigParser()
config.read('/home/mininet/Captive-Portal/config.ini')
TCP_server_ip = config['DEFAULT']['TCP_server_pox_ip']
TCP_server_port = int(config['DEFAULT']['TCP_server_port'])

class TCPClient:
  def __init__(self, host=TCP_server_ip, port=TCP_server_port):
    """Create a TCP client that can send and receive messages from a persistent connection."""
    self.host = host
    self.port = port
    self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.connection.connect((host, port))

  def send_request(self, request):
    """Send a JSON request to the server and return the JSON response."""
    self.connection.sendall(json.dumps(request).encode())
    return json.loads(self.connection.recv(1024).decode())

  def get_host(self):
      """Request the MAC address from the server."""
      return self.send_request({'command': 'getHost'})

  def set_host(self, value):
    """Request the MAC address from the server."""
    return self.send_request({'command': 'setHost', 'value': value})
  
  def get_internet(self):
      """Request the MAC address from the server."""
      return self.send_request({'command': 'getInternet'})

  def set_internet(self, value):
    """Request the MAC address from the server."""
    return self.send_request({'command': 'setInternet', 'value': value})

  def check_valid(self, value):
    """Request wether the MAC address is valid or not."""
    return self.send_request({'command': 'check', 'value': value})

  def close_connection(self):
    """Close the connection to the server."""
    self.connection.close()
