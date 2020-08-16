#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FTP Client that supports commands USER, PASS, QUIT, EPSV, PASV, RETR and LIST.
# lailpimi

import socket
import re
HOST_NAME = ''
CRLF = '\r\n'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Sets up a EPSV or PASV depending on server support
def setup_EPSV_or_PASV():
    global s
    global s2
    s.send(('EPSV' + CRLF).encode())
    print('>> EPSV')
    data = s.recv(4096).decode('UTF-8')
    print(data)
    if data.startswith('500'): # Need to use PASV
        print('EPSV unsupported on this server, setting up PASV')
        s.send(('PASV' + CRLF).encode())
        print('>> PASV')
        data = s.recv(4096).decode('UTF-8')
        if data.startswith('227'):
            print(data)
            m = re.search('\(([^)]+)', data).group(1)
            s2_ip = '.'.join(m.split(',')[:4])
            port_keys = m.split(',')[-2:]
            port = (int(port_keys[0])*256) + int(port_keys[1])
            try:
                s2.close()
                s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except:
                pass    
            s2.connect((s2_ip, port)) # Create passive socket
            print('Connecting passive to '+ s2_ip + ':' + str(port))
            return True
    else:
        m = re.search('\(([^)]+)', data).group(1)
        ep_port = (m.split('|||')[1])[:-1]
        try:
            s2.close()
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            pass
        s2.connect((HOST_NAME,int(ep_port)))
        print('Connecting passive to '+ HOST_NAME + ':' + str(ep_port))
        return True    
        
# Auto sends credentials on start         
def handle_login(user, passw):
    s.send(('USER ' + user + CRLF).encode())
    print('>> USER ' + user)
    data = s.recv(4096).decode('UTF-8')
    if data.startswith('331'):
        print(data)
        s.send(('PASS ' + passw + CRLF).encode())
        print('>> PASS ' + passw)
        data = s.recv(4096).decode('UTF-8')
        if data.startswith('230'):
            print(data)
            return True
            
        else: # If autologin fails, user can still enter new creds manually
            print(data)
            print('User or password was wrong')
            return True     
    else:
        print(data)
        print('USER failed')
        return False        

# Connects the communications socket    
def handle_connect(host, port):
    global HOST_NAME
    global s
    try:
        s.connect((host, port))
        data = s.recv(4096).decode('UTF-8')
        if data:
            print(data)
            HOST_NAME = host
            return True
    except:
        print('Connect failed')
        return False    

# Retrieves data using the PESV or PASV socket
def retrieve(command):
    global s
    global s2
    s.send((command + CRLF).encode())
    data = s.recv(4096).decode('UTF-8')
    if data.startswith('150'):
        data2 = s2.recv(16384).decode('UTF-8')
        file_name = command.split(' ')[1]
        with open(file_name,'w') as f:
            f.write(data2)
            f.close()
        s2.close()
        data = s.recv(4096).decode('UTF-8')
        print(data)
        print('File download complete!')
    else:
        print(data)        

def start_drive_loop():
    global s
    global s2
    while True:
        print('Enter a command')
        command = str(input())
        if command.upper().startswith('LIST') or command.upper().startswith('QUIT') or command.upper().startswith('RETR') or command.upper().startswith('EPSV') or command.upper().startswith('PASV') or command.upper().startswith('USER') or command.upper().startswith('PASS'):
            
            if command.upper().startswith('EPSV') or command.upper().startswith('PASV'):
                setup_EPSV_or_PASV()
                
            if command.upper().startswith('RETR'):
                setup_EPSV_or_PASV()
                retrieve(command)    
            
            if command.upper().startswith('USER'):
                s.send((command + CRLF).encode())
                data = s.recv(4096).decode('UTF-8')
                print(data)
            
            if command.upper().startswith('PASS'):
                s.send((command + CRLF).encode())
                data = s.recv(4096).decode('UTF-8')
                print(data)    
            
            if command.upper().startswith('QUIT'):
                s.send(('QUIT'+ CRLF).encode())
                data = s.recv(4096).decode('UTF-8')
                print(data)
                exit()
            
            if command.upper().startswith('LIST'):
                setup_EPSV_or_PASV()
                s.send((command + CRLF).encode())
                #print('>> LIST')
                data = s.recv(4096).decode('UTF-8')
                print(data)
                data2 = s2.recv(4096).decode('UTF-8')
                print(data2)
                data = s.recv(4096).decode('UTF-8')
                print(data)
 
        else:
            print('Unsupported command!')
            print('Supported commands: LIST, RETR, QUIT, USER, PASS, EPSV, PASV')    

def main():
    global s
    global s2
    print('Please input FTP server address')
    HOST_ADDR = str(input())
    print('Please input FTP server port')
    FTP_PORT = int(input())
    
    print('Please input your username (leave empty for anonymous)')
    USERNAME = str(input())
    if len(USERNAME) is 0:
        USERNAME = 'anonymous'
        PASSWORD = 'anonymous'
    else:
        print('Please input your password')
        PASSWORD = str(input())        
    
    connected = handle_connect(HOST_ADDR, FTP_PORT)
    if connected:
        logged_in = handle_login(USERNAME, PASSWORD)
        if logged_in:
            start_drive_loop()

if __name__ == "__main__":
    main()