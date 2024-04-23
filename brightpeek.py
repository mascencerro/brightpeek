#!/usr/bin/env python3
import sys
import requests

REQ_ENDPOINT = 'speedtest?url='
IP_LINE = '<b>Current IP:</b> '
#NET_LINE = '<b>Netmask:</b> '
TEST_PORTS = {80}

def print_help():
    print("Syntax:\nbrightpeek.py IP_ADDRESS:PORT_NUMBER\n")
    exit(0)

if (len(sys.argv) > 2):
    print("Too many arguments")
    print_help()

if (len(sys.argv) < 2):
    print("URL missing")
    print_help()

if (len(sys.argv[1].split(':')) != 2):
    print("Incorrect syntax")
    print_help()

EXT_IP = sys.argv[1].split(':')[0]
EXT_PORT = 0

try:
    EXT_PORT = int(sys.argv[1].split(':')[1])
except:
    print("Port needs to be a number")
    print_help()

req_base = f"http://{EXT_IP}:{EXT_PORT}"
req_headers = {'User-Agent': 'Netscape Navigator 2.0'}

# Get internal IP address of BrightSign device
info_req = requests.get(f"{req_base}/netconfig.html?ref=diagnostics.html", headers=req_headers)
info_split = info_req.content.split(b'\n')
INT_IP = ''

for line in info_split:
    if IP_LINE in line.decode('utf-8'):
        INT_IP = line.decode('utf-8').strip(IP_LINE)

INT_NET = INT_IP[0:INT_IP.rfind('.')]

print(f"External: {EXT_IP}:{EXT_PORT}")
print(f"Internal IP: {INT_IP}")
print(f"Network: {INT_NET}/24")
print("Scanning (this may take a while)...")

#Iterate through IP range
for ip in range(1,255):
    for port in TEST_PORTS:
        print(f"Host: {ip}", end='\r')
        req_string = f"http://{EXT_IP}:{EXT_PORT}/{REQ_ENDPOINT}{INT_NET}.{ip}:{port}"
        req_headers = {'User-Agent': 'Netscape Navigator 2.0'}
        response = requests.get(req_string, headers = req_headers)
        if b'No route to host' not in response.content:
            print("\r", end='')
            print(f"{INT_NET}.{ip}:{port} <-> {response.content}")

print("Done.")
