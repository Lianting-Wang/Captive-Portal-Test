import os
import time
import configparser
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, Node
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Intf

config = configparser.ConfigParser()
config.read('/home/mininet/Captive-Portal/config.ini')
internet_ip = config['DEFAULT']['internet_ip']
internet_mac = config['DEFAULT']['internet_mac']
captive_portal_ip = config['DEFAULT']['captive_portal_ip']
captive_portal_mac = config['DEFAULT']['captive_portal_mac']

bash_script = f'''#!/bin/bash

# IP of the primary gateway
PRIMARY_GW="{internet_ip}"
# IP of the secondary gateway
SECONDARY_GW="{captive_portal_ip}"
# The gateway currently being used, initially set to the primary gateway
CURRENT_GW="$PRIMARY_GW"

while true; do
    # Attempt to ping the primary gateway
    if ping -c 1 $PRIMARY_GW &> /dev/null; then
        # If the primary gateway is reachable and the current gateway is not the primary,
        # switch back to the primary gateway
        if [ "$CURRENT_GW" != "$PRIMARY_GW" ]; then
            echo "Switching back to primary gateway $PRIMARY_GW..."
            sudo ip route replace default via $PRIMARY_GW
            CURRENT_GW="$PRIMARY_GW"
        fi
    else
        # If the primary gateway is not reachable and the current gateway is not the secondary,
        # switch to the secondary gateway
        if [ "$CURRENT_GW" != "$SECONDARY_GW" ]; then
            echo "Primary gateway not reachable. Switching to secondary gateway $SECONDARY_GW..."
            sudo ip route replace default via $SECONDARY_GW
            CURRENT_GW="$SECONDARY_GW"
        fi
    fi
    # Check every second
    sleep 1
done
'''

bash_script_name = 'gateway_switch.sh'

def configure_network(host):
    host.cmd('sudo systemctl disable --now systemd-resolved.service')
    host.cmd(f'echo -e "nameserver 127.0.0.53\nnameserver 8.8.8.8" > /etc/resolv.conf')
    host.cmd(f'sudo ./{bash_script_name} &> /dev/null &')
    host.cmd('export XAUTHORITY=/root/.Xauthority')

def configure_host_network(host):
    host.cmd('iptables -t nat -A PREROUTING -p tcp --dport 53 -j REDIRECT --to-port 53')
    host.cmd('iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 80')
    host.cmd('iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 443')

def customTree(test_all):
    "Create a network and add NAT to provide Internet access."

    net = Mininet(controller=RemoteController, switch=OVSSwitch)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')

    info('*** Adding host\n')
    host = net.addHost('host', mac=captive_portal_mac, ip=captive_portal_ip, defaultRoute=f'via {internet_ip}')

    info('*** Adding internet connectivity\n')
    internet = net.addNAT(name='internet', mac=internet_mac)
    internet.configDefault()

    info('*** Adding users\n')
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')

    info('*** Creating links\n')
    net.addLink(s1, host)
    net.addLink(s1, internet)
    net.addLink(s1, s2)
    net.addLink(s2, h1)
    net.addLink(s2, h2)

    info('*** Starting network\n')
    net.start()

    info('*** Configure NAT setting\n')
    internet.cmd(f'ifconfig internet-eth0 {internet_ip} netmask 255.0.0.0')

    info('*** Configure user network\n')
    configure_network(h1)
    configure_network(h2)
    configure_host_network(host)

    info('*** Start host service\n')
    host.cmd('python dns_server.py 1>/dev/null 2>&1 &')
    host.cmd('python web_server.py 1>/dev/null 2>&1 &')

    info('Waiting for initialization...\n')
    time.sleep(1)

    info('*** Start testing\n')
    test_all(host, internet, h1, h2)

    # info('*** Running CLI\n')
    # CLI(net)

    info('*** Stopping network\n')
    net.stop()

def test_mininet_helper(test_all):
    # Create a bash script to switch gateways
    with open(bash_script_name, "w") as file:
        file.write(bash_script)
    # Change file permissions, add execute permissions
    os.chmod(bash_script_name, 0o755)

    setLogLevel('info')
    customTree(test_all)
