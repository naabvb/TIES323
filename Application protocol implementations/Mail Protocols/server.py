#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Runs SMTP, POP3, POP3 SSL and IMAP4 servers
# lailpimi

import socket
from socket import AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, SHUT_RDWR
import ssl
import time

HOST_ADDRESS = '127.0.0.1'
SMTP_PORT = 5080
POP3_PORT = 6080
POP3_PORT_SSL = 6443
IMAP4_PORT = 7080
IMAP4_PORT_SSL = 7443

SERVER_CERT = 'server.crt'
SERVER_KEY = 'server.key'
CLIENT_CERTS = 'client.crt'

CRLF = '\r\n'
SENT_MSGS = []  # Used for POP3 and "sent" SMTP messages
MAIL_BOXES = [] # Mail boxes listing for IMAP4

# Array for user objects, very insecure
USERS = [{'user': 'lailpimi', 'pass': 'testi123',
          'mail': 'lailpimi@student.jyu.fi'}]

# Create some random emails for pop3 client and add flags for imap4.
SENT_MSGS.append({'sender': 'eilauri@tiest.fi', 'data': 'heippa\r\nblaabalalablablalb\r\nja sitten nii\r\n',
                  'recipients': ['lailpimi@student.jyu.fi'], 'octets': 82, 'flags': ['\Seen']})
SENT_MSGS.append({'sender': 'sefeissari@telia.fi', 'data': 'HOI\r\nONKOS LIITTYMÄT KUNNOSSA!!!!\r\n',
                  'recipients': ['lailpimi@student.jyu.fi', 'tokalauri@jyu.fi'], 'octets': 93, 'flags': ['\Answered', '\Seen']})

# Add sent messages to IMAP4 mailbox with some flags
MAIL_BOXES.append({'name': 'INBOX', 'contents': SENT_MSGS, 'flags': ['\Answered', '\Seen', '\Recent'], 'root_dir': '~/EMAILDIR', 'folders': ['Sent', 'Trash']})

# Create fake directory listing for IMAP
DIRECTORY = '~/EMAILDIR/INBOX' 

s = socket.socket()  # SMTP socket
s.bind((HOST_ADDRESS, SMTP_PORT))
s.settimeout(1)
s.listen()

s2 = socket.socket()  # POP3 socket
s2.bind((HOST_ADDRESS, POP3_PORT))
s2.settimeout(1)
s2.listen()

s3 = socket.socket() # POP3 SSL socket
s3.bind((HOST_ADDRESS, POP3_PORT_SSL))
s3.settimeout(1)
s3.listen()

s4 = socket.socket()  # IMAP4 socket
s4.bind((HOST_ADDRESS, IMAP4_PORT))
s4.settimeout(1)
s4.listen()

# Load secure context for SSL connections
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
context.load_verify_locations(cafile=CLIENT_CERTS)

# Get octets for single mail
def calculateOctets(message):
    msg_octets = len((message['sender']).encode(
        'utf-8')) + len((message['data']).encode('utf-8'))
    for r in message['recipients']:
        msg_octets += len(r.encode('utf-8'))
    return msg_octets

# Get all mails for certain user
def getMails(user_mail):
    total_octets = 0
    mails = []
    for msg in SENT_MSGS:
        if user_mail in msg['recipients']:
            total_octets += msg['octets']
            mails.append(msg)
    return {'mails': mails, 'total_octets': '(' + str(total_octets) + ' octets)', 'total_octets_raw': total_octets}

# Count mail flags
def getFlags(messages):
    RECENT = 0
    ANSWERED = 0
    SEEN = 0
    for message in messages:
        for flag in message['flags']:
            if flag == '\Answered': ANSWERED +=1
            if flag == '\Recent': RECENT +=1
            if flag == '\Seen': SEEN +=1
    UNSEEN = len(messages) - SEEN        
    return {'recent': str(RECENT), 'seen': str(SEEN), 'answered': str(ANSWERED), 'unseen': str(UNSEEN)}        

# Terrible and overly complicated function to check matches against wildcards. 
# Proper implementation would require actual directory system.
def compileMB(mailbox, mb):
    start = True
    stillmatch = True
    matches = {'main': [], 'nochild': [], 'subf': []}
    if mb == '%/%':
        for folder in mailbox['folders']:
            matches['subf'].append(folder) 
        return matches        
    
    if '%' in mb:
        try:
            sections = mb.split('%')
            for section in sections[:-1]:
                if start:
                    start = False
                    if mailbox['name'].startswith(section):
                        stillmatch = True
                        continue
                    else:
                        stillmatch = False
                        break
                if section in mailbox['name'] and stillmatch:
                    stillmatch = True
                
                else:
                    stillmatch = False      
            if stillmatch:
                if mailbox['name'].endswith(sections[-1]):
                    matches['main'].append(mailbox['name'])
                else:
                    stillmatch = False
        except:
            pass
                    
    if '*' in mb and not '%' in mb:    
        try:
            sections = mb.split('*')
            for section in sections[:-1]:
                if start:
                    start = False
                    if mailbox['name'].startswith(section):
                        stillmatch = True
                        continue
                    else:
                        stillmatch = False
                        break
                if section in mailbox['name'] and stillmatch:
                    stillmatch = True
                
                else:
                    stillmatch = False       
            if stillmatch:
                if mailbox['name'].endswith(sections[-1]):
                    matches['main'].append(mailbox['name'])
                else:
                    stillmatch = False
                    
            start = True
            for folder in mailbox['folders']:
                stillmatch = True
                for section in sections[:-1]:
                    if start:
                        start = False
                        if folder.startswith(section):
                            stillmatch = True
                            continue
                        else:
                            stillmatch = False
                            break
                    if section in folder and stillmatch:
                        stillmatch = True
                if stillmatch:
                    if folder.endswith(sections[-1]):
                        matches['subf'].append(folder)
                else:
                    stillmatch = False
                start = True    
        except:
            pass
    return matches
                                    

print("Sockets set, waiting for connection")
started = True

# Here is where the actual server loop starts
while (started):
    # SMTP SERVER
    try:
        conn, remote_address = s.accept()
        print(conn)
        print(remote_address)
        conn.send(('220 TIES323.SMTP.SERVICE READY' + CRLF).encode())
        STATE = 'HELO'
        message = {'sender': '', 'data': [], 'recipients': [], 'octets': 0, 'flags': []}
        first = True
        try:
            while (True):
                data = conn.recv(4096).decode('UTF-8')
                if data:
                    if data.upper().startswith('HELO') and STATE is 'HELO':
                        STATE = 'MAIL'
                        conn.send(('250 OK' + CRLF).encode())
                    if data.upper().startswith('NOOP'):
                        conn.send(('250 OK' + CRLF).encode())
                    if STATE is 'MAIL':
                        if data.upper().startswith('RSET'):
                            message = {'sender': '',
                                       'data': [], 'recipients': []}
                            conn.send(('250 OK' + CRLF).encode())
                            continue

                        if data.upper().startswith('MAIL FROM:'):
                            try:
                                sender = data.split(':')[1].strip()
                                if len(sender) is 0 or sender is ' ':
                                    throw
                            except:
                                conn.send(
                                    ('501 Syntax error in parameters or arguments:' + CRLF).encode())
                                continue
                            message['sender'] = sender
                            conn.send(
                                ('250 OK SENDER: ' + sender + CRLF).encode())
                            STATE = 'RCPT'
                            first = True

                        if data.upper().startswith('QUIT'):
                            conn.send(
                                ('221 SERVICE CLOSING SOCKET' + CRLF).encode())
                            break

                        else:
                            if (first or data.upper().startswith('MAIL FROM:')) and STATE is not 'RCPT':
                                first = False
                            else:
                                if data.upper().startswith('DATA') or data.upper().startswith('RCPT TO:'):
                                    conn.send(
                                        ('503 Bad sequence of commands, use MAIL FROM, RSET, QUIT or NOOP' + CRLF).encode())
                                else:
                                    if STATE is not 'RCPT' and data.upper().startswith('NOOP') is False:
                                        conn.send(
                                            ('500 Syntax error, command unrecognized' + CRLF).encode())

                    if STATE is 'DATA':
                        if (CRLF + '.' + CRLF) in data:
                            conn.send(('250 MESSAGE SENT' + CRLF).encode())
                            message['data'] = "".join(message['data'])
                            STATE = 'MAIL'
                            octets = calculateOctets(message)
                            message['octets'] = octets
                            SENT_MSGS.append(message)
                            message = {'sender': '', 'data': [],
                                       'recipients': [], 'octets': 0, 'flags': []}
                        else:
                            message['data'].append(data + '\r\n')

                    if STATE is 'RCPT':  # TYPO FIX AND MULTIPLE RCPT

                        if data.upper().startswith('RSET'):
                            message = {'sender': '',
                                       'data': [], 'recipients': []}
                            conn.send(('250 OK' + CRLF).encode())
                            STATE = 'MAIL'
                            continue

                        if data.upper().startswith('RCPT TO:'):
                            try:
                                recipient = data.split(':')[1].strip()
                                if len(recipient) is 0 or recipient is ' ':
                                    throw
                            except:
                                conn.send(
                                    ('501 Syntax error in parameters or arguments:' + CRLF).encode())
                                continue

                            message['recipients'].append(recipient)
                            conn.send(
                                ('250 OK RCPT: ' + recipient + CRLF).encode())
                            STATE = 'RCPT'

                        if data.upper().startswith('DATA'):
                            if len(message['recipients']) > 0:
                                STATE = 'DATA'
                                conn.send(
                                    ('354 READY TO RECEIVE DATA, END WITH <CRLF>.<CRLF>;' + CRLF).encode())
                            else:
                                conn.send(
                                    ('503 Bad sequence of commands, use RCPT TO, RSET, QUIT or NOOP' + CRLF).encode())

                        if data.upper().startswith('QUIT'):
                            conn.send(
                                ('221 SERVICE CLOSING SOCKET' + CRLF).encode())
                            break

                        else:
                            if first or data.upper().startswith('RCPT TO:') or data.upper().startswith('DATA'):
                                first = False
                            else:
                                if data.upper().startswith('MAIL FROM:'):
                                    conn.send(
                                        ('503 Bad sequence of commands, use RCPT TO, DATA, RSET, QUIT or NOOP' + CRLF).encode())
                                else:
                                    if data.upper().startswith('NOOP') is False:
                                        conn.send(
                                            ('500 Syntax error, command unrecognized' + CRLF).encode())

                    if data.upper().startswith('QUIT'):
                        conn.send(
                            ('221 SERVICE CLOSING SOCKET' + CRLF).encode())
                        break

                    if STATE == 'HELO' and data.upper().startswith('NOOP') is False:
                        conn.send(
                            ('500 Syntax error, command unrecognized' + CRLF).encode())

                else:
                    print("Client dropped without warning")
                    break
        finally:
            print("Closing connection")
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()

    except socket.timeout:
        print("Listening 6080 (POP3)")

    # POP3 SERVER
    try:
        conn, remote_address = s2.accept()
        print(conn)
        print(remote_address)
        conn.send(('+OK POP3 server ready' + CRLF).encode())
        STATE = 'AUTHORIZATION'
        USER_NAME = ''
        PASSWORD = ''
        USER_MAIL = ''
        user_found = False
        pass_found = False
        try:
            while (True):
                data = conn.recv(4096).decode('UTF-8')
                if data:
                    if data.upper().startswith('USER'):
                        if len(data.split(' ')) > 1:
                            USER_NAME = data.split(' ')[1]
                            for user in USERS:
                                if USER_NAME == user['user']:
                                    conn.send(
                                        ('+OK ' + USER_NAME + ' is a real user, enter password' + CRLF).encode())
                                    user_found = True
                                    break
                        else:
                             conn.send(
                                        ('-ERR Invalid user' + CRLF).encode())            
                        if (user_found):
                            while (True):
                                data = conn.recv(4096).decode('UTF-8')
                                if data.upper().startswith('QUIT'):
                                    break
                                if data.upper().startswith('USER'):
                                    conn.send(('-ERR invalid password' + CRLF).encode())
                                    
                                if data.upper().startswith('PASS'):
                                    if len(data.split(' ')) > 1:
                                        PASSWORD = data.split(' ')[1]
                                        for user in USERS:
                                            if (USER_NAME == user['user']) and (PASSWORD == user['pass']):
                                                mails = getMails(user['mail'])
                                                USER_MAIL = user['mail']
                                                conn.send(
                                                    ('+OK ' + USER_NAME + "'s maildrop has " + str(len(mails['mails'])) + ' messages ' + mails['total_octets'] + CRLF).encode())
                                                STATE = 'TRANSACTION'
                                                pass_found = True
                                                break
                                        if (pass_found):
                                            break
                                        else:
                                            conn.send(
                                                ('-ERR invalid password' + CRLF).encode())
                                    else:
                                        conn.send(
                                                ('-ERR invalid password' + CRLF).encode())            
                        else:
                            if (len(USER_NAME) > 0):
                                conn.send(('-ERR sorry, no mailbox for ' +
                                        USER_NAME + ' here' + CRLF).encode())

                    if STATE is 'TRANSACTION':
                        if data.upper().startswith('LIST'):
                            index = 1
                            mails = getMails(USER_MAIL)
                            if len(data.split(' ')) is 2: # If argument is provided
                                arg = data.split(' ')[1]
                                try:
                                    if int(arg) is 0:
                                        throw
                                    arg_int = (int(arg)-1)
                                    selected = mails['mails'][arg_int]
                                    conn.send(('+OK ' + arg + ' ' + str(selected['octets']) + CRLF).encode())
                                except:
                                    conn.send(('-ERR no such message, only ' + str(len(mails['mails'])) + ' messages in maildrop' + CRLF).encode())        
                            else:
                                conn.send(('+OK ' + str(len(mails['mails'])) + ' messages ' + mails['total_octets'] + CRLF).encode())
                                
                                for mail in mails['mails']:
                                    conn.send((str(index) + ' ' + str(mail['octets']) + CRLF).encode())
                                    index += 1
                                conn.send(('.' + CRLF).encode())
                                index = 1            

                    if data.upper().startswith('QUIT'):
                        if STATE is 'TRANSACTION':
                            STATE = 'UPDATE' # If quit is called during TRANSACTION, STATE changes to UPDATE and all messages marked as deleted
                                             # from the maildrop and replies as to the status of this operation should be removed. 
                                             # Does not matter in this case, as we aren't implementing any commands that are affected.
                        conn.send(
                            ('+OK POP3 server signing off' + CRLF).encode())
                        break
                else:
                    print("Client dropped without warning")
                    break    

        finally:
            print("Closing connection")
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()

    except socket.timeout:
        print("Listening 6443 (POP3 SSL)")

    # POP3 SSL SERVER (basically a repeat of the normal pop3 server with extra SSL stuff)
    try:
        conn, remote_address = s3.accept()
        print(conn)
        print(remote_address)
        # Wrap socket with ssl
        conn = context.wrap_socket(conn, server_side=True)
        conn.send(('+OK POP3 SSL server ready' + CRLF).encode())
        STATE = 'AUTHORIZATION'
        USER_NAME = ''
        PASSWORD = ''
        USER_MAIL = ''
        user_found = False
        pass_found = False
        try:
            while (True):
                data = conn.recv(4096).decode('UTF-8')
                if data:
                    if data.upper().startswith('USER'):
                        if len(data.split(' ')) > 1:
                            USER_NAME = data.split(' ')[1]
                            for user in USERS:
                                if USER_NAME == user['user']:
                                    conn.send(
                                        ('+OK ' + USER_NAME + ' is a real user, enter password' + CRLF).encode())
                                    user_found = True
                                    break
                        else:
                             conn.send(
                                        ('-ERR Invalid user' + CRLF).encode())            
                        if (user_found):
                            while (True):
                                data = conn.recv(4096).decode('UTF-8')
                                if data.upper().startswith('QUIT'):
                                    break
                                if data.upper().startswith('USER'):
                                    conn.send(('-ERR invalid password' + CRLF).encode())
                                    
                                if data.upper().startswith('PASS'):
                                    if len(data.split(' ')) > 1:
                                        PASSWORD = data.split(' ')[1]
                                        for user in USERS:
                                            if (USER_NAME == user['user']) and (PASSWORD == user['pass']):
                                                mails = getMails(user['mail'])
                                                USER_MAIL = user['mail']
                                                conn.send(
                                                    ('+OK ' + USER_NAME + "'s maildrop has " + str(len(mails['mails'])) + ' messages ' + mails['total_octets'] + CRLF).encode())
                                                STATE = 'TRANSACTION'
                                                pass_found = True
                                                break
                                        if (pass_found):
                                            break
                                        else:
                                            conn.send(
                                                ('-ERR invalid password' + CRLF).encode())
                                    else:
                                        conn.send(
                                                ('-ERR invalid password' + CRLF).encode())            
                        else:
                            if (len(USER_NAME) > 0):
                                conn.send(('-ERR sorry, no mailbox for ' +
                                        USER_NAME + ' here' + CRLF).encode())

                    if STATE is 'TRANSACTION':
                        if data.upper().startswith('LIST'):
                            index = 1
                            mails = getMails(USER_MAIL)
                            if len(data.split(' ')) is 2: # If argument is provided
                                arg = data.split(' ')[1]
                                try:
                                    if int(arg) is 0:
                                        throw
                                    arg_int = (int(arg)-1)
                                    selected = mails['mails'][arg_int]
                                    conn.send(('+OK ' + arg + ' ' + str(selected['octets']) + CRLF).encode())
                                except:
                                    conn.send(('-ERR no such message, only ' + str(len(mails['mails'])) + ' messages in maildrop' + CRLF).encode())        
                            else:
                                conn.send(('+OK ' + str(len(mails['mails'])) + ' messages ' + mails['total_octets'] + CRLF).encode())
                                
                                for mail in mails['mails']:
                                    conn.send((str(index) + ' ' + str(mail['octets']) + CRLF).encode())
                                    index += 1
                                conn.send(('.' + CRLF).encode())
                                index = 1            

                    if data.upper().startswith('QUIT'):
                        if STATE is 'TRANSACTION':
                            STATE = 'UPDATE' # If quit is called during TRANSACTION, STATE changes to UPDATE and all messages marked as deleted
                                             # from the maildrop and replies as to the status of this operation should be removed. 
                                             # Does not matter in this case, as we aren't implementing any commands that are affected.
                        conn.send(
                            ('+OK POP3 SSL server signing off' + CRLF).encode())
                        break
                else:
                    print("Client dropped without warning")
                    break    

        finally:
            print("Closing connection")
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
    
    except socket.timeout:
        print("Listening 7080 (IMAP4)")
        
        
    # IMAP4 SERVER
    try:
        conn, remote_address = s4.accept()
        print(conn)
        print(remote_address)
        conn.send(('IMAP4 server ready' + CRLF).encode())
        STATE = 'NOT_AUTHORIZED'
        USER_NAME = ''
        PASSWORD = ''
        USER_MAIL = ''
        TAG = ''
        SELECTED = ''
        found_mailbox = ''

        user_found = False
        mailbox_found = False
        try:
            while True:
                data = conn.recv(4096).decode('UTF-8')
                try:
                    TAG = data.split(' ')[0]
                except:
                    conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())    
                if data:
                    if 'LOGIN' in data.upper():
                        if len(data.split(' ')) > 3 and data.upper().split(' ')[1] == 'LOGIN': # tag command user pass
                            TAG = data.split(' ')[0]
                            USER_NAME = data.split(' ')[2]
                            PASSWORD = data.split(' ')[3]
                            for user in USERS:
                                if USER_NAME == user['user'] and PASSWORD == user['pass']:
                                    user_found = True
                                    conn.send((TAG +' OK - login completed, now in authenticated state' + CRLF).encode())
                                    STATE = 'AUTHENTICATED'
                                    break
                                else:
                                    conn.send(
                                        (TAG +' NO - login failure: user name or password rejected' + CRLF).encode())
                        else:
                            conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())
                            
                    if 'NOOP' in data.upper() and STATE is not 'SELECTED':
                            if len(data.split(' ')) > 1:
                                TAG = data.split(' ')[0]
                                conn.send((TAG +' OK NOOP completed' + CRLF).encode())
                            else:
                                conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())  
                                                        
                    if STATE is 'AUTHENTICATED' or STATE is 'SELECTED':
                        if 'SELECT' in data.upper():
                            if len(data.split(' ')) > 2: # TAG command mailboxname
                                TAG = data.split(' ')[0]
                                SELECTED = data.upper().split(' ')[2]
                                mailbox_found = False
                                for mailbox in MAIL_BOXES:
                                    if mailbox['name'] == SELECTED:
                                        mailbox_found = True
                                        found_mailbox = mailbox
                                        all_flags = getFlags(mailbox['contents'])
                                        conn.send(('* FLAGS (' + ' '.join(mailbox['flags']) + ')' +CRLF).encode())
                                        conn.send(('* ' + str(len(mailbox['contents'])) + ' EXISTS' + CRLF).encode())
                                        conn.send(('* ' + all_flags['recent'] + ' RECENT' + CRLF).encode())
                                        conn.send(('* OK [UNSEEN ' + all_flags['unseen'] + ']' + CRLF).encode())
                                        conn.send(('* OK [SEEN ' + all_flags['seen'] + ']' + CRLF).encode())
                                        conn.send(('* OK [ANSWERED ' + all_flags['answered'] + ']' + CRLF).encode())
                                        # Could print UIDs here, but since we already have just one user, I didn't see it as a necessary step
                                        conn.send((TAG +' OK - [READ-WRITE] SELECT completed' + CRLF).encode())
                                        STATE = 'SELECTED'
                                        break
                                if mailbox_found is False:
                                    SELECTED = ''
                                    STATE = 'AUTHENTICATED' # If Selected again and mailbox not found, old selected will be reset
                                    conn.send((TAG +' NO - no such mailbox' + CRLF).encode())     
                            else:
                                conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())    
                    
                    if STATE is 'AUTHENTICATED' or STATE is 'SELECTED':
                        if 'LIST' in data.upper():
                            if len(data.split(' ')) > 3: # tag komento reference mailboxname
                                TAG = data.split(' ')[0]
                                REF = data.split(' ')[2]
                                MB = data.split(' ')[3]
                                list_box_found = False
                                if REF == "\"\"" and MB == "\"\"": # If getting empty listing
                                    string = r'* LIST (\Noselect) "/" ""'
                                    conn.send((string + CRLF).encode())
                                    conn.send((TAG +' OK LIST Completed' + CRLF).encode())
                                    continue
                                
                                mMB = MB[1:-1]
                                if REF == "\"\"" and MB == "\"*\"": # If listing all mailboxes and their children without ref
                                    for mailbox in MAIL_BOXES:
                                        conn.send(('* LIST (HasChildren) "/" ' + mailbox['root_dir'] + CRLF).encode())
                                        if len(mailbox['folders']) > 0:
                                            conn.send(('* LIST (HasChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + CRLF).encode())
                                            for folder in mailbox['folders']:
                                                conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['name'] + '/' + folder + CRLF).encode())
                                        else:
                                            conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + CRLF).encode())             
                                        conn.send((TAG +' OK LIST Completed' + CRLF).encode())
                                    continue
                                
                                if REF == "\"\"" and MB == "\"%\"": # If listing only TOP level folders
                                    for mailbox in MAIL_BOXES:
                                        conn.send(('* LIST (HasChildren) "/" ' + mailbox['root_dir'] + CRLF).encode())
                                        if len(mailbox['folders']) > 0:
                                            conn.send(('* LIST (HasChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + CRLF).encode())
                                        else:
                                            conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + CRLF).encode())   
                                        conn.send((TAG +' OK LIST Completed' + CRLF).encode())
                                    continue
                                              
                                if REF == "\"\"" and MB == "\"%/%\"": # If listing only TOP level folders
                                    for mailbox in MAIL_BOXES:
                                        if len(mailbox['folders']) > 0:
                                            for folder in mailbox['folders']:
                                                conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['name'] + '/' + folder + CRLF).encode())
                                        conn.send((TAG +' OK LIST Completed' + CRLF).encode())
                                    continue
                                
                                mREF = REF[1:-1]
                                mMB = MB[1:-1]
                             
                                if REF == "\"\"" and MB != "\"*\"" and '*' in mMB: # If checking with wildcard on all directorys
                                    for mailbox in MAIL_BOXES:
                                        
                                        search = compileMB(mailbox, mMB)
                                        for main in search['main']:
                                                conn.send(('* LIST (HasChildren) "/" ' + mailbox['root_dir'] + '/' + main + CRLF).encode())
                                        for folder in search['subf']:
                                            conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + '/' + folder + CRLF).encode())
                                    conn.send((TAG +' OK LIST Completed' + CRLF).encode())        
                                    continue 
                               
                                for mailbox in MAIL_BOXES:
                                    if mREF == (mailbox['root_dir'])[2:]: # If ref matches a 'DIRECTORY' folder, in our case only "EMAILDIR" is matchable
                                        if mMB == '*': # if just wildcard print all subfolders
                                            if len(mailbox['folders']) > 0:
                                                conn.send(('* LIST (HasChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + CRLF).encode())
                                                for folder in mailbox['folders']:
                                                    conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + '/' + folder + CRLF).encode())                  
                                            else:
                                                conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + CRLF).encode())
                                        
                                        else:
                                            search = compileMB(mailbox, mMB)
                                            for main in search['main']:
                                                conn.send(('* LIST (HasChildren) "/" ' + mailbox['root_dir'] + '/' + main + CRLF).encode())
                                            for folder in search['subf']:
                                                conn.send(('* LIST (HasNoChildren) "/" ' + mailbox['root_dir'] + '/' + mailbox['name'] + '/' + folder + CRLF).encode()) 
                                conn.send((TAG +' OK LIST Completed' + CRLF).encode())
                                continue                         
                            else:
                                conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())
                            
                    if STATE is 'SELECTED':
                        if 'NOOP' in data.upper():
                            if len(data.split(' ')) > 1:
                                TAG = data.split(' ')[0]
                                all_flags = getFlags(found_mailbox['contents'])
                                conn.send(('* ' + str(len(found_mailbox['contents'])) + ' EXISTS' + CRLF).encode())
                                conn.send(('* ' + all_flags['recent'] + ' RECENT' + CRLF).encode())
                                conn.send((TAG +' OK NOOP completed' + CRLF).encode())
                            else:
                                conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())    
                                
                    if 'LOGOUT' in data.upper():
                        if len(data.split(' ')) > 1:
                            TAG = data.split(' ')[0]
                            conn.send(('* BYE IMAP4 Server logging out' + CRLF).encode()) 
                            conn.send((TAG +' OK LOGOUT completed' + CRLF).encode())
                            time.sleep(0.5) # Give time to client to receive all commands
                            break
                        else:
                            conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())
                        
                    else:
                        if 'LOGOUT' not in data.upper() and 'NOOP' not in data.upper() and 'SELECT' not in data.upper() and 'LOGIN' not in data.upper() and 'LIST' not in data.upper():
                            conn.send((TAG +' BAD - command unknown or arguments invalid' + CRLF).encode())
                else:
                    print("Client dropped without warning")
                    break                                
        finally:
            print("Closing connection")
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()    
            
        
    except socket.timeout:
        print("Listening 5080 (SMTP)")        
