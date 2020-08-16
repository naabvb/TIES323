#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# POP3 client with GUI and SSL/TLS support
# lailpimi

import socket
import ssl
import time
from tkinter import *

HOST_ADDR = '127.0.0.1'
SERVER_SNI_HOSTNAME = 'lailpimi.jyu.fi'  # Validated from certificate
server_cert = 'server.crt'
client_cert = 'client.crt'
client_key = 'client.key'

CRLF = '\r\n'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Modify port based on checkbox
def enable_ssl():
    SSL_on = checkVar.get()
    if (SSL_on == 1):
        port_string.set(6443)
    else:
        port_string.set(6080)

# When connect button is clicked
def connect_host():
    host_a = host_field.get()
    host_p = int(port_field.get())
    SSL_on = checkVar.get()
    global s
    if (SSL_on == 0):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host_a, host_p))
    if (SSL_on == 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Load certificates
        context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH, cafile=server_cert)
        context.load_cert_chain(certfile=client_cert, keyfile=client_key)
        # Create a SSL wrapped socket and verify server side certificates
        s = context.wrap_socket(s, server_side=False,
                                server_hostname=SERVER_SNI_HOSTNAME)
        s.connect((host_a, host_p))
    data = s.recv(4096).decode('UTF-8')
    if data:
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, data)
        if data.upper().startswith('+OK'):
            connect_button.config(state=DISABLED)
            login_button.config(state=NORMAL)

# When Send USER button is clicked
def send_user():
    user = user_field.get()
    if len(user) > 0:
        s.send(('USER ' + user).encode())
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, '>>USER ' + user + CRLF)
        while (True):
            data = s.recv(4096).decode('UTF-8')
            if data:
                output_input_box.config(state=NORMAL)
                output_input_box.insert(END, data)
                if data.upper().startswith('+OK'):
                    login_button.config(state=DISABLED)
                    login_button2.config(state=NORMAL)
                break

# When Send PASS button is clicked
def send_pass():
    password = pass_field.get()
    if len(password) > 0:
        s.send(('PASS ' + password).encode())
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, '>>PASS ' + password + CRLF)
        while (True):
            data = s.recv(4096).decode('UTF-8')
            if data:
                output_input_box.config(state=NORMAL)
                output_input_box.insert(END, data)
                if data.upper().startswith('+OK'):
                    login_button2.config(state=DISABLED)
                    list_button.config(state=NORMAL)
                break

# When Clear box button is clicked
def clear_box():
    output_input_box.delete('1.0', END)

# When LIST button is clicked
def get_list():
    global s
    if list_input_field.get():
        output_input_box.config(state=NORMAL)
        output_input_box.insert(
            END, '>>LIST ' + str(list_input_field.get()) + CRLF)
        s.send(('LIST ' + str(list_input_field.get())).encode())
    else:
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, '>>LIST' + CRLF)
        s.send(('LIST').encode())
    # Sometimes data gets sent after expected, though weirdly this behavior seems to only happen here
    s.settimeout(0.2)
    while True:
        try:
            data = s.recv(4096).decode('UTF-8')
            output_input_box.config(state=NORMAL)
            output_input_box.insert(END, data)
        except:
            break
    s.settimeout(None)

# When QUIT button is clicked
def process_quit():
    connect_button.config(state=NORMAL)
    login_button.config(state=DISABLED)
    list_button.config(state=DISABLED)
    try:
        output_input_box.config(state=NORMAL)
        output_input_box.insert(END, '>>QUIT' + CRLF)
        s.send(('QUIT' + CRLF).encode())
        data = s.recv(4096).decode('UTF-8')
        if data:
            output_input_box.config(state=NORMAL)
            output_input_box.insert(END, data)
        s.close()
    except:
        pass

# All GUI elements are created here + mainloop for tkinter
if __name__ == "__main__":
    gui = Tk()
    gui.configure(background="dark grey")
    gui.title("POP3 Client")
    gui.geometry("800x540")

    label1 = Label(gui, text="Host: ",
                   fg='black', bg='dark grey')
    label2 = Label(gui, text="Port: ",
                   fg='black', bg='dark grey')

    label3 = Label(gui, text="User: ",
                   fg='black', bg='dark grey')
    label4 = Label(gui, text="Pass: ",
                   fg='black', bg='dark grey')

    label1.grid(row=1, column=0, sticky="E", ipadx="20", ipady="5")
    label2.grid(row=2, column=0, sticky="E", ipadx="20")
    label3.grid(row=4, column=0, sticky="E", ipadx="20", ipady="5")
    label4.grid(row=5, column=0, sticky="E", ipadx="20")

    host_string = StringVar()
    host_string.set('127.0.0.1')
    port_string = StringVar()
    port_string.set('6080')
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

    checkVar = IntVar()
    Checkbutton(gui, text="SSL", variable=checkVar, bg="dark grey",
                command=enable_ssl).grid(row=1, column=4)

    quit_button = Button(gui, text="QUIT", bg="whitesmoke",
                         fg="black", command=process_quit, width=10)
    quit_button.grid(row=1, column=5, sticky=E)

    clear_button = Button(gui, text="Clear box", bg="whitesmoke",
                          fg="black", command=clear_box, width=10)
    clear_button.grid(row=2, column=5, sticky=E)

    connect_button = Button(gui, text="Connect", bg="whitesmoke",
                            fg="black", command=connect_host, width=10)
    connect_button.grid(row=3, column=1, ipady="5")

    login_button = Button(gui, text="Send USER", bg="whitesmoke",
                          fg="black", command=send_user, width=10, state=DISABLED)
    login_button.grid(row=6, column=1)

    login_button2 = Button(gui, text="Send PASS", bg="whitesmoke",
                           fg="black", command=send_pass, width=10)
    login_button2.grid(row=7, column=1)
    login_button2.config(state=DISABLED)

    list_input = StringVar()
    list_input_field = Entry(gui, textvariable=list_input, width=5)
    list_input_field.grid(row=8, column=1, ipadx="10", sticky=E)

    list_button = Button(gui, text="LIST", bg="whitesmoke",
                         fg="black", command=get_list, width=20, state=DISABLED)
    list_button.grid(row=8, column=1, sticky=W)

    output_input_box = Text(gui, height=23, width=72, font=("Helvetica", 8))
    output_input_box.grid(row=8, column=5)

    output_input_box.config(state=DISABLED)
    gui.mainloop()
