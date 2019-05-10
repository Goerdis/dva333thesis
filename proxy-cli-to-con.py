#!/usr/bin/python3
# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over IDC(I Don't Care) license
import socket
import select
import time
import sys
import threading

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
buffer_size = 4096
delay = 0.0001
#forward_to = ('192.168.7.7', 9999)

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as e:
            print(e)
            return False

class TheServer:
    input_list = []
    channel = {}
    #forward_to = ('192.168.7.7', 9999)

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def main_loop(self):
        print("Entering main_loop")
        self.input_list.append(self.server)
        while 1:
            time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                #self.data = self.s.recv(buffer_size)
                if self.s == self.server:
                    self.on_accept()
                    break
                print("Collecting data")
                self.data = self.s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()

    def on_accept(self):
        print("Entering on_accept")
        clientsock, clientaddr = self.server.accept()
        print("before break")
        self.forwData = clientsock.recv(buffer_size)
        print("decode+split")
        self.forwData = self.forwData.decode().split()
        #ACK = bytes("ACK", "utf-8")
        #clientsock.send(ACK)
        print("after break")
        print(self.forwData)
        forward = Forward().start(self.forwData[0], int(self.forwData[1]))
        #clientsock, clientaddr = self.server.accept()
        if forward:
            print(clientaddr, "has connected")
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            print("Can't establish connection with remote server.",)
            print("Closing connection with client side", clientaddr)
            clientsock.close()

    def on_close(self):
        print("Entering on_close")
        print(self.s.getpeername(), "has disconnected")
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        print("Entering on_recv")
        data = self.data
        # here we can parse and/or modify the data before send forward
        #data.decode(); data=data.split()
        #forward_to[0] = data[0]; del data[0]
        #forward_to[1] = int(data[0]); del data[0]
        #data = bytes(" ".join(data) ,"utf-8")
        print(data)
        self.channel[self.s].send(data)

################################################################################

# socket thread for Client -> Controller
def socketThread1():
    try:
        server = TheServer('192.168.3.1', 9090)
        server.main_loop()
    except:
        pass

#--------------------------------------------------------------------------------
# socket thread for Controller -> Client
def socketThread2():
    try:
        server = TheServer('10.0.0.3', 9090)
        server.main_loop()
    except:
        pass

################################################################################

def main():
    try:
        socketT1 = threading.Thread(target = socketThread1)
        socketT2 = threading.Thread(target = socketThread2)
        socketT1.daemon = True
        socketT2.daemon = True
        #socketT1.start()
        socketT2.start()
        while True:
            pass
    except:
        sys.exit()

if __name__ == "__main__":
    main()

