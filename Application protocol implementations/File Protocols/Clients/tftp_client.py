#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TFTP Client, supports RRQ and WRQ and error correcting actions
# lailpimi

import socket

MAX_PACKET_LENGTH = 516

OPCODES = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
LAST_SENT_BLOCK = 1
LATEST_BLOCK = 1

LAST_SENT_REQUEST = ''
LAST_SENT_ACK_REQUEST = ''

LAST_RECEIVED_BLOCK = 0
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

server_address = ('127.0.0.1', 10069)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Creates and sends RRQ request packet
def send_rq(filename, mode):
    request = bytearray()
    request.append(0)
    request.append(1) # Opcode

    filename = bytearray(filename.encode('utf-8'))
    request += filename
    request.append(0)
    form = bytearray(bytes(mode, 'utf-8'))
    request += form
    request.append(0)
    
    sent = s.sendto(request, server_address)

# Creates and sends WRQ request packet
def send_wrq(filename, mode):
    request = bytearray()
    request.append(0)
    request.append(2) # Add opcode

    filename = bytearray(filename.encode('utf-8'))
    request += filename # Add filename

    request.append(0) # Add zero byte

    form = bytearray(bytes(mode, 'utf-8'))
    request += form # Add the mode

    request.append(0) # Add the last byte
    sent = s.sendto(request, server_address)

# Sends ACK based on received DATA
def send_ack(ack_data, server):
    global LAST_RECEIVED_BLOCK
    global LAST_SENT_ACK_REQUEST

    ack = bytearray(ack_data)
    
    # If received blocknum is not next compared to previous ack sent, resend ack
    if ((LAST_RECEIVED_BLOCK+1) is not ack[3]) or ack[1] is not 3:
        print('Received incorrect or broken block number, resending previous ack')
        s.sendto(LAST_SENT_ACK_REQUEST, server)
        return True
    
    LAST_RECEIVED_BLOCK = ack[3]
    ack[0] = 0
    ack[1] = OPCODES['ACK'] # 4
    s.sendto(ack, server)
    LAST_SENT_ACK_REQUEST = ack
    return False

# Check if server sent an error packet.    
def server_error(data):
    opcode = data[:2]
    return int.from_bytes(opcode, byteorder='big') == OPCODES['ERROR']

# Checks received ACK packet integrity and blocknum
def incorrect_blocknum(received):
    if received[3] is LAST_SENT_BLOCK and received[1] is 4:
        return False
    return True  

# Creates and sends a data packet based on received ACKs
def create_data_packet(data,blocknum, server):
    global LAST_SENT_BLOCK
    global LATEST_BLOCK
    global LAST_SENT_REQUEST
    global DONE
    
    request = bytearray()
    request.append(0)
    request.append(3) # 3 is opcode for data
    
    request.append(0)
    request.append(blocknum) # Add current blocknum
    
    if len(data) < 512: # If last data packet
        DONE = True
    request +=data
    sent = s.sendto(request, server)  
    LAST_SENT_REQUEST = request
    LAST_SENT_BLOCK = LATEST_BLOCK
    LATEST_BLOCK += 1
    s.settimeout(5)
    try:
        data, server = s.recvfrom(600)
    except:
        print('socket timed out while waiting for ack, resending data packet')
        while True:
            sent = s.sendto(LAST_SENT_REQUEST, server)
            data, server = s.recvfrom(600)
            if incorrect_blocknum(data):
                continue # IF still incorrect ack, keep resending
            print('ACK corrected, moving on')
            break # move on if fixed
        pass
    s.settimeout(None)
            
    if incorrect_blocknum(data): # IF ack blocknum didn't match or packet was corrupted
        print('ACK blocknum incorrect, resending')
        while True:
            sent = s.sendto(LAST_SENT_REQUEST, server) # Resend
            data, server = s.recvfrom(600) # Receive new ACK
            if incorrect_blocknum(data):
                print('ACK still incorrect, resending') 
                continue # IF still incorrect ack, keep resending
            print('ACK corrected, moving on')
            break # move on if fixed

def main():
    print('Please input RRQ filename or WRQ filename')
    command = input()
    filename = command.split(' ')[1]
    mode = "netascii"
    if command.upper().startswith('RRQ'):
        send_rq(filename, mode)
    if command.upper().startswith('WRQ'):
        send_wrq(filename, mode)    

    if command.upper().startswith('RRQ'):
        file = open(filename, "wb")
        while True:
            s.settimeout(5)
            try:
                data, server = s.recvfrom(600)
            except socket.timeout:
                print('timeout, resend previous ack')
                s.sendto(LAST_SENT_ACK_REQUEST, server)
                s.settimeout(None)
                continue # Can skip writing since wrong block
                
            if server_error(data):
                error_code = int.from_bytes(data[2:4], byteorder='big')
                print(SERVER_ERROR_MSG_LIST[error_code])
                break
            was_resent = send_ack(data[0:4], server)
            if was_resent:
                continue # Skip writing if resend was necessary
            content = data[4:]
            file.write(content)
            if len(data) < MAX_PACKET_LENGTH:
                file.close()
                print('File: ' + filename + ' received!')
                break
    
    if command.upper().startswith('WRQ'):
        file = open(filename, "rb")
        buf = 512
        data, server = s.recvfrom(600)
        if data[1] is 4 and data[3] is 0: # correct ack to begin write
            while True:
                if DONE:
                    file.close()
                    print('File: ' + filename + ' sent!')
                    break
                s_data = file.read(buf)
                while (s_data):
                    create_data_packet(s_data, LATEST_BLOCK, server)
                    s_data = file.read(buf)

if __name__ == '__main__':
    main()
