#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# IMAP4 client with GUI and SSL/TLS support
# lailpimi

import socket
import ssl
import time
from tkinter import *

HOST_ADDR = '127.0.0.1'

CRLF = '\r\n'

cmd_tag = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# When connect button is clicked
def connect_host():
    host_a = host_field.get()
    host_p = int(port_field.get())
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host_a, host_p))
    data = s.recv(4096).decode('UTF-8')
    if data:
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, data)
        if data.upper().startswith('IMAP4'):
            connect_button.config(state=DISABLED)
            login_button.config(state=NORMAL)
            noop_button.config(state=NORMAL)
            quit_button.config(state=NORMAL)

# When login button is clicked
def login():
    global cmd_tag
    user = user_field.get()
    password = pass_field.get()
    if len(user) > 0 and len(password) > 0:
        s.send(('A' + str(cmd_tag) + ' LOGIN ' + user + ' ' + password).encode())
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, '>>A' + str(cmd_tag) + ' ' + user + ' ' + password  +CRLF)
        cmd_tag += 1
        data = s.recv(4096).decode('UTF-8')
        if data:
            output_input_box.config(state=NORMAL)
            output_input_box.insert(END, data)
        if 'OK' in data.upper():
            login_button.config(state=DISABLED)
            list_button.config(state=NORMAL)
            select_button.config(state=NORMAL)
            fetch_button.config(state=NORMAL)

# When LIST button is clicked
def send_list():
    global s
    global cmd_tag
    arg1 = list1_input_field.get()
    arg2 = list2_input_field.get()
    p1 = '\"' + arg1 +'\"'
    p2 = '\"' + arg2 +'\"'
    s.send(('A' + str(cmd_tag) + ' LIST ' + p1 + ' ' + p2).encode())
    output_input_box.config(state=NORMAL)
    output_input_box.insert(END, '>>A'+ str(cmd_tag) + ' LIST '+ p1 + ' ' + p2 + CRLF)
    cmd_tag += 1
    s.settimeout(0.2)
    while True:
        try:
            data = s.recv(4096).decode('UTF-8')
            output_input_box.config(state=NORMAL)
            output_input_box.insert(END, data)
        except:
            break
    s.settimeout(None)

# When NOOP button is clicked
def send_noop():
    global s
    global cmd_tag
    output_input_box.config(state=NORMAL)
    output_input_box.insert(END, '>>A'+ str(cmd_tag) + ' NOOP' + CRLF)
    s.send(('A' + str(cmd_tag) + ' NOOP').encode())
    cmd_tag += 1
    s.settimeout(0.2)
    while True:
        try:
            data = s.recv(4096).decode('UTF-8')
            output_input_box.config(state=NORMAL)
            output_input_box.insert(END, data)
        except:
            break
    s.settimeout(None)
    
# When Clear box button is clicked
def clear_box():
    output_input_box.delete('1.0', END)

# When SELECT button is clicked
def send_select():
    global s
    global cmd_tag
    arg = select_input_field.get()
    if len(arg) > 0:
        s.send(('A' + str(cmd_tag) + ' SELECT ' + arg).encode())
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, '>>A'+ str(cmd_tag) + ' SELECT '+ arg + CRLF)
        cmd_tag += 1
        s.settimeout(0.2)
        while True:
            try:
                data = s.recv(4096).decode('UTF-8')
                output_input_box.config(state=NORMAL)
                output_input_box.insert(END, data)
            except:
                break
        s.settimeout(None)
        
# When FETCH button is clicked
def send_fetch():
    global s
    global cmd_tag
    arg = fetch_input_field.get()
    if len(arg) > 0:
        s.send(('A' + str(cmd_tag) + ' FETCH ' + arg).encode())
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, '>>A'+ str(cmd_tag) + ' FETCH '+ arg + CRLF)
        cmd_tag += 1
        s.settimeout(0.2)
        while True:
            try:
                data = s.recv(4096).decode('UTF-8')
                output_input_box.config(state=NORMAL)
                output_input_box.insert(END, data)
            except:
                break
        s.settimeout(None)        
        
# When LOGOUT button is clicked
def process_quit():
    global cmd_tag
    global s
    connect_button.config(state=NORMAL)
    login_button.config(state=DISABLED)
    list_button.config(state=DISABLED)
    noop_button.config(state=DISABLED)
    quit_button.config(state=DISABLED)
    list_button.config(state=DISABLED)
    select_button.config(state=DISABLED)
    fetch_button.config(state=DISABLED)
    try:
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END,'>>A'+str(cmd_tag)+ ' LOGOUT' + CRLF)
        s.send(('A'+str(cmd_tag)+ ' LOGOUT' + CRLF).encode())
        
        s.settimeout(0.2)
        while True:
            try:
                data = s.recv(4096).decode('UTF-8')
                output_input_box.config(state=NORMAL)
                output_input_box.insert(END, data)
            except:
                break
        cmd_tag = 0        
        s.close()
    except:
        pass

# All GUI elements are created here + mainloop for tkinter
if __name__ == "__main__":
    gui = Tk()
    gui.configure(background="dark grey")
    gui.title("IMAP4 Client")
    gui.geometry("590x670")

    label1 = Label(gui, text="Host: ",
                   fg='black', bg='dark grey')
    label2 = Label(gui, text="Port: ",
                   fg='black', bg='dark grey')

    label3 = Label(gui, text="User: ",
                   fg='black', bg='dark grey')
    label4 = Label(gui, text="Pass: ",
                   fg='black', bg='dark grey')
    
    label5 = Label(gui, text="SELECT",
                   fg='black', bg='dark grey')
    
    label6 = Label(gui, text="LIST",
                   fg='black', bg='dark grey')
    
    label7 = Label(gui, text="FETCH",
                   fg='black', bg='dark grey')

    label1.grid(row=1, column=0, sticky="E", ipadx="10", ipady="5")
    label2.grid(row=2, column=0, sticky="E", ipadx="10")
    label3.grid(row=4, column=0, sticky="E", ipadx="10", ipady="5")
    label4.grid(row=5, column=0, sticky="E", ipadx="10")
    label5.grid(row=7, column=0, sticky="E", ipadx="10")
    label6.grid(row=9, column=0, sticky="E", ipadx="10")
    label7.grid(row=12, column=0, sticky="E", ipadx="10")
    
    host_string = StringVar()
    host_string.set('127.0.0.1')
    port_string = StringVar()
    port_string.set('7080')
    host_field = Entry(gui, textvariable=host_string)
    port_field = Entry(gui, textvariable=port_string)
    host_field.grid(row=1, column=1, ipadx="50")
    port_field.grid(row=2, column=1, ipadx="50")

    username = StringVar()
    username.set('lailpimi')
    password = StringVar()
    password.set('testi123')
    user_field = Entry(gui, textvariable=username)
    pass_field = Entry(gui, textvariable=password)
    user_field.grid(row=4, column=1, ipadx="50")
    pass_field.grid(row=5, column=1, ipadx="50")

    quit_button = Button(gui, text="LOGOUT", bg="whitesmoke",
                         fg="black", command=process_quit, width=10, state=DISABLED)
    quit_button.grid(row=1, column=5, sticky=E)

    clear_button = Button(gui, text="Clear box", bg="whitesmoke",
                          fg="black", command=clear_box, width=10)
    clear_button.grid(row=3, column=5, sticky=E)
    
    noop_button = Button(gui, text="NOOP", bg="whitesmoke",
                          fg="black", command=send_noop, width=10, state=DISABLED)
    noop_button.grid(row=2, column=5, sticky=E)

    connect_button = Button(gui, text="Connect", bg="whitesmoke",
                            fg="black", command=connect_host, width=10)
    connect_button.grid(row=3, column=1, ipady="5")

    login_button = Button(gui, text="LOGIN", bg="whitesmoke",
                          fg="black", command=login, width=10, state=DISABLED)
    login_button.grid(row=6, column=1)

    select_input = StringVar()
    select_input.set('INBOX')
    select_input_field = Entry(gui, textvariable=select_input)
    select_input_field.grid(row=7, column=1, ipadx="50")

    select_button = Button(gui, text="SELECT", bg="whitesmoke",
                        fg="black", command=send_select, state=DISABLED, width=10)
    select_button.grid(row=8, column=1)

    list1_input = StringVar()
    list1_input.set("EMAILDIR")
    list2_input = StringVar()
    list2_input.set("*")
    
    list1_input_field = Entry(gui, textvariable=list1_input)
    list1_input_field.grid(row=9, column=1, ipadx="15")
    
    list2_input_field = Entry(gui, textvariable=list2_input)
    list2_input_field.grid(row=10, column=1, ipadx="15")
    
    list_button = Button(gui, text="LIST", bg="whitesmoke",
                        fg="black", command=send_list, state=DISABLED, width=10)
    list_button.grid(row=11, column=1)
    
    fetch_input = StringVar()
    fetch_input.set("Not implemented on server per requirements")
    
    fetch_input_field = Entry(gui, textvariable=fetch_input)
    fetch_input_field.grid(row=12, column=1, ipadx="50")
    fetch_button = Button(gui, text="FETCH", bg="whitesmoke",
                        fg="black", command=send_fetch, state=DISABLED, width=10)
    fetch_button.grid(row=13, column=1)
    

    output_input_box = Text(gui, height=23, width=72, font=("Helvetica", 8))
    output_input_box.grid(row=14, column=1)
    
    output_input_box.config(state=DISABLED)
    gui.mainloop()
