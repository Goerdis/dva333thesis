#!/usr/bin/python3

import socket
import socketserver
import time
import threading
import os
import re
import sys

################################################################################

# Gloabl variables
MAXBANDWIDTH = 20000
USEDBANDWIDTH = 0
lock = threading.Lock()
# lock.acquire()
# lock.release()
CLIENTLIST = []
REGCHANGES = 0
PROXY = ('10.0.0.5', 9090)

################################################################################

# class for adding clients
class sdnClient:
    clientCount = 0

    def __init__(self, devName, devPriority, devRequestBW, devOfferedBW, devIPaddr):
        self.devName = devName
        self.devPriority = devPriority
        self.devRequestBW = devRequestBW
        self.devOfferedBW = devOfferedBW
        self.devIPaddr = devIPaddr
        sdnClient.clientCount += 1
   
    def displayCount(self):
        print ("Total Client count: %d" % sdnClient.clientCount)

    def displayDevice(self):
        print("Devicename: ", self.devName,
              "\nPriority: ", self.devPriority,
              "\nRequestedBW: ", self.devRequestBW,
              "\nOfferedBW: ", self.devOfferedBW,
              "\nDev IP: ", self.devIPaddr)

#--------------------------------------------------------------------------------
# class for handling tcp-connections from clients
class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            # Change the int in settimeout to desired value for time-in-seconds until
            # TCP-session timeouts
            client.settimeout(10)
            threading.Thread(target = self.listenToClient,args = (client,address)).start()

# Here new thread starts for every client connecting.
# Not really any reason to mod anything else than 'listenToClient'
    def listenToClient(self, client, address):
        global CLIENTLIST
        global REGCHANGES
        size = 1024
        while True:
            try:
                # Recieving data and spliting into a list
                data = client.recv(size)
                data = data.decode()
                data = data.split()
                # First index of list is what type of message, 1:registering, 2:hello
                # Index saved to check variable and deleted from list
                checkVar = int(data[0])
                del data[0]
                if data:
                    if checkVar == 1:
                        # The user that asks to register is saved to variable to keep track
                        # on which user is alive on current TCP-session
                        currUser = data[0]
                        # boo variable used in checking if duplicate client exists, if boo
                        # remain true after for loop then client will be registered
                        boo = True
                        lock.acquire()
                        # Forloop to check if current user is alredy registered or not
                        # if uniquie, the user is added to list och client objects
                        for name in CLIENTLIST:
                            if name.devName == data[0]:
                                boo = False
                                break
                            else:
                                boo = True
                        if boo == True:
                            CLIENTLIST.append(sdnClient(data[0], data[1], data[2], data[3], data[4]))
                            if REGCHANGES != 1:
                                REGCHANGES = 1
                        lock.release()
                        # Set the response to send back ACK 
                        response = bytes("ACK", "utf-8")
                        client.send(response)
                    elif checkVar == 2:
                        print("Hello msg from: ", currUser)
                        # Set the response to send back ACK
                        response = bytes("ACK", "utf-8")
                        client.send(response)
                else:
                    raise error('Client disconnected')
            except:
                print("\n***** Client disconnected *****")
                print(currUser, "\n")
                client.close()
                # After client disconnect, de-register client from list of client objects
                # Here currUser variable is used to make sure correct user that started the
                # TCP-session is the one that gets deleted and then decrement total number of clients
                lock.acquire()
                for i, client in enumerate(CLIENTLIST):
                    if client.devName == currUser:
                        del CLIENTLIST[i]
                        sdnClient.clientCount -= 1
                        break
                if REGCHANGES != 1:
                    REGCHANGES = 1
                lock.release()
                return False

################################################################################

# socket thread for recieving client registration, hello's and de-registration
def socketThread1():
    port = 12345
    host = "10.0.0.1"
    ThreadedServer(host,port).listen()

#--------------------------------------------------------------------------------
# socket thread for recieving hellos***NOT IN USE ATM***
#def socketThread2():
    #port = 23456
    #host = "127.0.0.1"
    #ThreadedServer(host,port).listen()

#--------------------------------------------------------------------------------
# list thread, now only used to print list every 10 seconds to keep track of changes
# and current connections (MAX/USED BW, clients etc.)
# thread could be commented out without breaking anything
# as it's only funcationality is for printing information
def listThread():
    global CLIENTLIST
    global MAXBANDWIDTH
    global USEDBANDWIDTH
    while True:
        print(40 * "-")
        lock.acquire()
        print("Max Bandwidth: ", MAXBANDWIDTH, "\nUsed Bandwidth: ", USEDBANDWIDTH)
        print(40 * "-")
        for client in CLIENTLIST:
            client.displayCount()
            client.displayDevice()
            print(40 * "-")
        lock.release()
        time.sleep(10)

#--------------------------------------------------------------------------------
# thread for running bandwidth algoritm
def algThread():
    global CLIENTLIST
    global REGCHANGES
    global MAXBANDWIDTH
    global USEDBANDWIDTH
    global VAR1
    global VAR2
    clientPort = 55555
    while True:
        if REGCHANGES == 1:
            lock.acquire()
            totalPrio = 0
            USEDBANDWIDTH = 0
            bwAmount = 0
            # First for loop to calculate the total requested BW and
            # total priority levels
            for client in CLIENTLIST:
                totalPrio += int(client.devPriority)
                bwAmount += int(client.devRequestBW)
            # If the total amount of requested BW doesn't exceed
            # the max BW then requested amount will be allocated.
            # Else the algorithm will be run to calculate allocation.
            if bwAmount <= MAXBANDWIDTH:
                for client in CLIENTLIST:
                    client.devOfferedBW = client.devRequestBW
                    USEDBANDWIDTH += int(client.devOfferedBW)
            else:
                for client in CLIENTLIST:
                    client.devOfferedBW = str(int(client.devPriority) * int(MAXBANDWIDTH / totalPrio))
                    USEDBANDWIDTH += int(client.devOfferedBW)
            # After algorithm is run the amount of allocated BW will be
            # sent to all clients to readjust.
            for client in CLIENTLIST:
                try:
                    print("Trying Send")
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((PROXY[0], PROXY[1]))
                    cliConn = str(client.devIPaddr+" 55555")
                    s.send(bytes(cliConn, "utf-8"))
                    time.sleep(0.5)
                    s.send(bytes(client.devOfferedBW, "utf-8"))
                    s.close()
                    print("Finnished Send")
                except:
                    pass
            REGCHANGES = 2
            lock.release()

################################################################################

def main():
    try:
        socketT1 = threading.Thread(target = socketThread1)
        #socketT2 = threading.Thread(target = socketThread2)
        listT = threading.Thread(target = listThread)
        algT = threading.Thread(target = algThread)
        socketT1.daemon = True
        #socketT2.daemon = True
        listT.daemon = True
        algT.daemon = True
        socketT1.start()
        #socketT2.start()
        listT.start()
        algT.start()
        while True:
            pass
    except:
        sys.exit()

if __name__ == "__main__":
    main()


