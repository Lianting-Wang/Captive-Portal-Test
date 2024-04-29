from scapy.all import *
import socket
import configparser
import logging

config = configparser.ConfigParser()
config.read('/home/mininet/Captive-Portal/config.ini')
DNS_Server = config['DEFAULT']['DNS_Server']
DNS_Server_port = config['DEFAULT']['DNS_Server_port']
internet_ip = config['DEFAULT']['internet_ip']
captive_portal_ip = config['DEFAULT']['captive_portal_ip']
dns_server_log = config['DEFAULT']['dns_server_log']

# Setup logging
logging.basicConfig(filename=dns_server_log, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def forward_dns_query(data, server=DNS_Server, port=int(DNS_Server_port)):
    """Forward DNS query to a specified DNS server and return the response."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(2)  # Set a timeout
        sock.sendto(data, (server, port))
        try:
            response, _ = sock.recvfrom(1024)  # Adjusting size for larger responses
        except socket.timeout:
            logging.warning(f"Timeout occurred while forwarding query to DNS server {server}:{port}")
            return None
    return response

def dns_interceptor(packet):
    """Intercept DNS requests and forward them to a specified DNS server."""
    # Only intercept DNS queries from the client
    if packet.haslayer(DNSQR) and packet[IP].src != captive_portal_ip and packet[IP].src != DNS_Server:
        query_name = packet[DNSQR].qname.decode('utf-8').strip('.')
        logging.info(f"Received DNS query for {query_name} from {packet[IP].src} to {packet[IP].dst}")
        original_data = bytes(packet[UDP].payload)
        response_data = forward_dns_query(original_data)
        
        if response_data:
            response_packet = DNS(response_data)
            # Send the response back to the client
            spoofed_pkt = IP(dst=packet[IP].src, src=packet[IP].dst) /\
                          UDP(dport=packet[UDP].sport, sport=packet[UDP].dport) /\
                          DNS(id=packet[DNS].id, qr=1, aa=packet[DNS].aa, qd=packet[DNS].qd,
                              an=response_packet.an, ns=response_packet.ns, ar=response_packet.ar)
            send(spoofed_pkt, verbose=0)
            logging.info(f"Forwarded DNS response to {packet[IP].src}")
        else:
            logging.error(f"Failed to receive DNS response from server for query {query_name}")

# Start the DNS interceptor
logging.info("DNS Interceptor setup complete. Starting packet sniffing...")
sniff(filter="udp port 53", prn=dns_interceptor)
