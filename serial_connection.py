#!/usr/bin/python3
import serial

import re

from time import sleep
import sys

class serial_connection():
    def __init__(self, device, username=None):
        self.buffer = b""
        self.back_at_prompt_pattern =  None
        self.username = username
        self.log = log(1)
        self.con = serial.Serial(device)

    def read(self, size=1):
        if len(self.buffer) >= size:
            # throw away first size bytes in buffer
            data =  self.buffer[:size]
            # Set the buffer to the non used bytes
            self.buffer = self.buffer[size:]
            return data
        else:
            data = self.buffer
            # Set the size to the value we have to read now
            size = size - len(self.buffer)
            # Set the buffer empty
            self.buffer = b""
            return data + self.con.read(size)

    def peek(self, size=1):
        if len(self.buffer) <= size:
            self.buffer += self.con.read(size=size - len(self.buffer))

        return self.buffer[:size]

    def readline(self):
        self.log.debug(self.buffer)
        self.buffer = self.buffer + self.con.read(self.con.in_waiting)
        if b"\n" in self.buffer:
            size = self.buffer.index(b"\n") + 1
            self.log.debug("We have a whole line in the buffer")
            self.log.debug(self.buffer)
            self.log.debug("We split at {}".format(size))
            data = self.buffer[:size]
            self.buffer = self.buffer[size:]
            self.log.debug(data)
            self.log.debug(self.buffer)
            return data

        data = self.buffer
        self.buffer = b""
        return data + self.con.readline()

    def back_at_prompt(self):
        data = self.peek()
        if not data == b"[":
            return False

        # We need to use self.in_waiting because with self.con.in_waiting we get
        # not the complete string
        size = len(self.buffer) + self.in_waiting
        data = self.peek(size)


        if self.back_at_prompt_pattern == None:
            #self.back_at_prompt_pattern = r"^\[{}@.+\]#".format(self.username)
            self.back_at_prompt_pattern = re.compile(r"^\[{}@.+\]#".format(self.username), re.MULTILINE)

        if self.back_at_prompt_pattern.search(data.decode()):
            return True
        else:
            return False

    def log_console_line(self, line):
        self.log.debug("Get in function log_console_line()")
        sys.stdout.write(line)

    @property
    def in_waiting(self):
        in_waiting_before = 0
        sleep(0.5)

        while in_waiting_before != self.con.in_waiting:
            in_waiting_before = self.con.in_waiting
            sleep(0.5)

        return self.con.in_waiting

    def line_in_buffer(self):
        if b"\n" in self.buffer:
            return True

        return False

    def print_lines_in_buffer(self):
        while True:
            self.log.debug("Fill buffer ...")
            self.peek(len(self.buffer) + self.in_waiting)
            self.log.debug("Current buffer length: {}".format(len(self.buffer)))
            if self.line_in_buffer() == True:
                while self.line_in_buffer() == True:
                    data = self.readline()
                    self.log_console_line(data.decode())
            else:
                self.log.debug("We have printed all lines in the buffer")
                break

    def login(self, password):
        if self.username == None:
            self.log.error("Username cannot be blank")
            return False

        self.print_lines_in_buffer()

        # Hit enter to see what we get
        self.con.write(b'\n')
        # We get two new lines \r\n ?
        data = self.readline()
        self.log_console_line(data.decode())

        self.print_lines_in_buffer()

        if self.back_at_prompt():
            self.log.debug("We are already logged in.")
            return True

        # Read all line till we get login:
        while 1:
            # We need to use self.in_waiting because with self.con.in_waiting we get
            # not the complete string
            size = len(self.buffer) + self.in_waiting
            data = self.peek(size)

            pattern = r"^.*login: "
            pattern = re.compile(pattern)

            if pattern.search(data.decode()):
                break
            else:
                self.log.debug("The pattern does not match")
                self.log.debug(self.peek(len(self.buffer) + self.in_waiting))
                self.log_console_line(self.readline().decode())

        # We can login
        string = "{}\n".format(self.username)
        self.con.write(string.encode())
        self.con.flush()
        # read the login out of the buffer
        data = self.readline()
        self.log.debug("This is the login:{}".format(data))
        self.log_console_line(data.decode())

        # We need to wait her till we get the full string "Password:"
        #This is useless but self.in_waiting will wait the correct amount of time
        size = self.in_waiting

        string = "{}\n".format(password)
        self.con.write(string.encode())
        self.con.flush()
        # Print the 'Password:' line
        data = self.readline()
        self.log_console_line(data.decode())

        while not self.back_at_prompt():
            # This will fail if the login failed so we need to look for the failed keyword
            data = self.readline()
            self.log_console_line(data.decode())

        return True

    def write(self, string):
        self.log.debug(string)
        self.con.write(string.encode())
        self.con.flush()

    def command(self, command):
        self.write("{}; echo \"END: $?\"\n".format(command))

        # We need to read out the prompt for this command first
        # If we do not do this we will break the loop immediately
        # because the prompt for this command is still in the buffer
        data = self.readline()
        self.log_console_line(data.decode())

        while not self.back_at_prompt():
            data = self.readline()
            self.log_console_line(data.decode())

        # We saved our exit code in data (the last line)
        self.log.debug(data.decode())
        data = data.decode().replace("END: ", "")
        self.log.debug(data)
        self.log.debug(data.strip())
        return data.strip()