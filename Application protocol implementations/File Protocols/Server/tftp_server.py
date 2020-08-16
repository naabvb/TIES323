#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TFTP Server, supports RRQ and WRQ + error correcting
# lailpimi

import random
import socket
import os

OPCODES = {1: 'RRQ', 2: 'WRQ', 3: 'DATA', 4: 'ACK', 5: 'ERROR'}
LAST_SENT_BLOCK = 1
LATEST_BLOCK = 1

LATEST_SENT_REQUEST = ''
LAST_SENT_ACK_REQUEST = ''
LAST_RECEIVED_BLOCK = 0

MAX_PACKET_LENGTH = 516
IP = '127.0.0.1'
PORT = 10069
DONE = False

# List of different server error messages from RCF 1350. Only 'file not found' is currently implemented
SERVER_ERROR_MSG_LIST = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((IP, PORT))
started = True
STATE = 'READY'
TID = random.randint(35500,55000) # Get random port number for second socket

s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # THE SEND SOCKET
s2.bind((IP,TID))

SEND_ADDR = ('127.0.0.1', TID) # Gets updated to client address on rrq
RECV_ADDR = ('127.0.0.1', TID) # Gets updated to client address on wrq

print('TFTP Server running on port ' + str(PORT))

# Gets opcode meaning from the code eg. 4 -> 'ACK'
def getOP(code):
    try:
        op = OPCODES[code]
        return op
    except:
        return 0

# Creates and sends the basic empty ACK packet
def send_default_ack_packet():
    request = bytearray()
    request.append(0)
    request.append(4) # opcode
    
    request.append(0)
    request.append(0) # default blocknum 0  
    sent = s2.sendto(request, SEND_ADDR)

# Creates and sends ACK packet based on incoming DATA packets
def send_ack_packet(ack_data, server):
    global LAST_RECEIVED_BLOCK
    global LAST_SENT_ACK_REQUEST
    ack = bytearray(ack_data)
    
    # If received blocknum is not next compared to previous ack sent, resend ack
    if ((LAST_RECEIVED_BLOCK+1) is not ack[3]) or ack[1] is not 3:
        print('Received incorrect or broken block number')
        s2.sendto(LAST_SENT_ACK_REQUEST, server)
        return True
    
    LAST_RECEIVED_BLOCK = ack[3]
    ack[0] = 0
    ack[1] = 4
    s2.sendto(ack, server)
    LAST_SENT_ACK_REQUEST = ack
    return False

# Creates and sends a possible error packet
def send_error_packet(error_code):
    request = bytearray()
    request.append(0)
    request.append(5) # 5 is opcode for error
    
    request.append(0)
    request.append(error_code) # 1 == file not found error code
    
    error_msg = bytearray(SERVER_ERROR_MSG_LIST[error_code].encode('utf-8'))
    request += error_msg # Add error msg string

    request.append(0) # Add zero byte
    sent = s2.sendto(request, SEND_ADDR)
    
# Checks received ACK packet integrity and blocknum
def incorrect_blocknum(received):
    if received[3] is LAST_SENT_BLOCK and received[1] is 4:
        return False
    return True  

# Creates and sends a DATA packet based on incoming ACKs
def create_data_packet(data,blocknum, server):
    global LAST_SENT_BLOCK
    global LATEST_BLOCK
    global LATEST_SENT_REQUEST

    request = bytearray()
    request.append(0)
    request.append(3)
    
    request.append(0)
    request.append(blocknum) # Current blocknum
    
    if len(data) < 512: # NORMAL
        global DONE
        DONE = True
    request +=data
    
    sent = s2.sendto(request, server)
    LATEST_SENT_REQUEST = request
    LAST_SENT_BLOCK = LATEST_BLOCK
    LATEST_BLOCK += 1
    s2.settimeout(5)
    try:
        data, server = s2.recvfrom(600)
    except:
        print('socket timed out while waiting for ack, resending data packet')
        while True:
            sent = s2.sendto(LATEST_SENT_REQUEST, server)
            data, server = s2.recvfrom(600)
            if incorrect_blocknum(data):
                continue # IF still incorrect ack, keep resending
            print('ACK corrected, moving on')
            break # move on if fixed
        pass
    s2.settimeout(None)
    
    if incorrect_blocknum(data): # IF ack blocknum didn't match or packet was corrupted
        print('ACK blocknum incorrect, resending')
        while True:
            sent = s2.sendto(LATEST_SENT_REQUEST, server) # Resend
            data, server = s2.recvfrom(600) # Receive new ACK
            if incorrect_blocknum(data):
                print('ACK still incorrect, resending') 
                continue # IF still incorrect ack, keep resending
            print('ACK corrected, moving on')
            break # move on if fixed
         
# Main loop
while True:
    try:
        data, addr = s.recvfrom(600)
        SEND_ADDR = addr
        STATE = getOP(data[1])
        if STATE is 0:
            print('Could not start requested operation')
            break
        i = 2
        while(data[i] != 0): # Run until 1 zero byte for full filename
            i += 1
        filename = (data[2:i]).decode('utf-8')
        
        # If client requests RRQ
        if STATE is 'RRQ':
            if os.path.exists(filename): # Check if file exists
                file = open(filename, "rb")
                buf = 512
                while True:
                    if DONE:
                        print('File: ' + filename + ' sent!')
                        file.close()
                            
                        # Reset values
                        DONE = False
                        STATE = 'READY'
                        LAST_SENT_BLOCK = 1
                        LATEST_BLOCK = 1
                        LATEST_SENT_REQUEST = ''
                        break
                    
                    s_data = file.read(buf)
                    while (s_data):
                        create_data_packet(s_data, LATEST_BLOCK, SEND_ADDR)
                        s_data = file.read(buf)      
            else:
                send_error_packet(1)
                print('File not found')
                STATE = 'READY'
        
        # If client requests WRQ             
        if STATE is 'WRQ':
            file = open(filename, "wb")
            send_default_ack_packet()
            while True:
                s2.settimeout(5)
                try:
                    data, server = s2.recvfrom(600)
                except socket.timeout:
                    print('timeout, resend previous ack')
                    s2.sendto(LAST_SENT_ACK_REQUEST, server)
                    s2.settimeout(None)
                    continue # Can skip writing since wrong block
                    
                was_resent = send_ack_packet(data[0:4], server)
                if was_resent:
                    continue # Skip writing if resend was necessary
                content = data[4:]
                file.write(content)
                if len(data) < MAX_PACKET_LENGTH:
                     print('File: ' + filename + ' received!')
                     LAST_SENT_ACK_REQUEST = ''
                     LAST_RECEIVED_BLOCK = 0
                     STATE = 'READY'
                     file.close()
                     break
        
    except socket.timeout:
        print('waiting for connections')    
