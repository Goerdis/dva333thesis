#!/usr/bin/python3
# Best Application Ever

import socket
import socketserver
import time
import threading
import os
import re
import sys
import netifaces as ni

################################################################################

OFFEREDBW = 1
IP = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
LOCALPORT = 55555
LOCALHOST = "localhost"
DATA = "1 Uberuser 3 20000 1337 "+IP
HELLO = "2 Hello"
HOST = "192.168.3.1"
PORT = 12345
OFFEREDBW = 10

PROXY = ('10.0.0.3', 9090)
CONTROLLER = "10.0.0.1 12345"

################################################################################

def socketThread1():
    print("Starting server")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP, LOCALPORT))
    s.listen()
    print("Listening")
    while True:
        try:
            conn, addr = s.accept()
            data = conn.recv(1024)
            if data:
                print("Reading BWdata")
                bandWidth = int(data.decode())
                print(bandWidth)
                os.system("sudo wondershaper wlan0 %s %s" % (bandWidth, bandWidth))
        except:
            time.sleep(0.1)

################################################################################

def main():
    try:
        socketT1 = threading.Thread(target = socketThread1)
        socketT1.daemon = True
        socketT1.start()
        time.sleep(0.1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((PROXY[0], PROXY[1]))
        sock.sendall(bytes(CONTROLLER, "utf-8"))
        time.sleep(0.1)
        sock.sendall(bytes(DATA + "\n", "utf-8"))
        received = str(sock.recv(1024), "utf-8")
        print("Sent:     {}".format(DATA))
        print("Received: {}".format(received))
        time.sleep(0.4)
        while True:
            try:
                sock.sendall(bytes(HELLO, "utf-8"))
                received = str(sock.recv(1024), "utf-8")
                print("Sent:     {}".format(HELLO))
                print("Received: {}".format(received))
                time.sleep(5)
            except:
                sys.exit()
    except:
        os.system("sudo wondershaper clear wlan0")
        sys.exit()

if __name__ == "__main__":
    main()
