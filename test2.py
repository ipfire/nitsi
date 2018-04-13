#!/usr/bin/python3

import serial

import re
from time import sleep
import sys

import libvirt

import xml.etree.ElementTree as ET

class test():
    def __init__(self, name):
        pass

    def read_settings(self):
        pass

class log():
    def __init__(self, log_level):
        self.log_level = log_level

    def debug(self, string):
        if self.log_level >= 4:
            print("DEBUG: {}".format(string))

    def error(self, string):
        print("ERROR: {}".format(string))

class vm():
    def __init__(self, uri):
        self.log = log(4)
        try:
            self.con = libvirt.open(uri)
        except BaseException as error:
            self.log.error("Could not connect to: {}".format(uri))

        self.log.debug("Connected to: {}".format(uri))

    def get_domain_from_name(self, name):
        dom = self.con.lookupByName(name)

        if dom == None:
            raise BaseException

        return dom

    def domain_is_running(self, dom):
        if dom == None:
            return False

        state, reason = dom.state()

        if state == libvirt.VIR_DOMAIN_RUNNING:
            return True
        else:
            return False

    def domain_get_serial_device(self, dom):
        if dom == None:
            raise BaseException

        if not self.domain_is_running(dom):
            raise BaseException

        xml_root = ET.fromstring(dom.XMLDesc(0))

        elem = xml_root.find("./devices/serial/source")
        return elem.get("path")

    def domain_start_from_xml(self, xml):
        dom = self.con.createXML(xml, 0)
        if dom == None:
            self.log.error("Failed to create the VM")
            raise BaseException

        return dom

    def domain_start_from_xml_file(self, file):
        try:
            fobj = open(file)
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(file))

        return self.domain_start_from_xml(fobj.read())

    def check_domain_is_booted_up(self, dom):
        serial_con = connection(self.domain_get_serial_device(dom))

        serial_con.write("\n")
        # This will block till the domain is booted up
        serial_con.read(1)





# try:
#     dom = conn.lookupByUUIDString(uuid)
# except:
#     flash(u"Failed to get the domain object", 'alert-danger')
#     print('Failed to get the domain object', file=sys.stderr)
#     conn.close()
#     return redirect("/vm")

# domname = dom.name()
# if action == "start":
#     try:
#         dom.create()
#     except:
#         flash(u"Can not boot guest domain.", 'alert-danger')
#         print('Can not boot guest domain.', file=sys.stderr)
#         conn.close()
#         return redirect("/vm")

#     flash(u"Sucessfully started Domain \"{}\"".format(domname), 'alert-info')
#     conn.close()
#     return redirect("/vm")

# elif action == "shutdown":
#     try:
#         dom.shutdown()
#     except:
#         flash(u"Can not shutdown guest domain.", 'alert-danger')
#         print('Can not shutdown guest domain.', file=sys.stderr)
#         conn.close()
#         return redirect("/vm")

#     flash(u"Sucessfully shutdowned Domain \"{}\"".format(domname), 'alert-info')
#     conn.close()
#     return redirect("/vm")

# elif action == "destroy":
#     try:
#         dom.destroy()
#     except:
#         flash(u"Can not destroy guest domain.", 'alert-danger')
#         print('Can not destroy guest domain.', file=sys.stderr)
#         conn.close()
#         return redirect("/vm")

#     flash(u"Sucessfully destroyed Domain \"{}\"".format(domname), 'alert-info')
#     conn.close()
#     return redirect("/vm")

# elif action == "pause":
#     try:
#         dom.suspend()
#     except:
#         flash(u"Can not pause guest domain.", 'alert-danger')
#         print('Can not pause guest domain.', file=sys.stderr)
#         conn.close()
#         return redirect("/vm")

#     flash(u"Sucessfully paused Domain \"{}\"".format(domname), 'alert-info')
#     conn.close()
#     return redirect("/vm")

# elif action == "resume":
#     try:
#         dom.resume()
#     except:
#         flash(u"Can not eesume guest domain.:", 'alert-danger')
#         print('Can not resume guest domain.', file=sys.stderr)
#         conn.close()
#         return redirect("/vm")

#     flash(u"Sucessfully resumed Domain \"{}\"".format(domname), 'alert-info')
#     conn.close()
#     return redirect("/vm")

# else:
#     flash(u"No such action: \"{}\"".format(action), 'alert-warning')
#     conn.close()
#     return redirect("/vm")


# @vms.route('/vm')
# @login_required
# def vm_overview():
#     import sys
#     import libvirt
#     conn = libvirt.open('qemu:///system')
#     doms = conn.listAllDomains(0)
#     domains = []

#     if len(doms) != 0:
#         for dom in doms:
#             domain = {}
#             domain.setdefault("name", dom.name())
#             domain.setdefault("uuid", dom.UUIDString())
#             state, reason = dom.state()
#             domain.setdefault("state", dom_state(state))
#             domains.append(domain)

#     conn.close()

#     return render_template("virtberry_vm_basic-vm.html", domains=domains)



class connection():
    def __init__(self, device, username=None):
        self.buffer = b""
        self.back_at_prompt_pattern =  None
        self.username = username
        self.log = log(1)
        self.con = serial.Serial(device)
        # # Just press enter one time to see what we get
        # self.con.write(b'\n')
        # # We get two new lines \r\n ?
        # data = self.readline()
        # self.log_console_line(data.decode())


        # if not self.back_at_prompt():
        #     self.log.debug("We need to login")
        #     if not self.login(password):
        #         self.log.error("Login failed")
        #         return False
        # else:
        #     self.log.debug("We are logged in")


        '''      in_waiting_before = 0
        sleep(1)

        while in_waiting_before != self.con.in_waiting:
            in_waiting_before = self.con.in_waiting
            sleep(0.5)

        print(self.con.in_waiting)
        data = self.con.read(self.con.in_waiting)
        print(data)
        print(data.decode(),end='')

        string = 'root\n'
        self.con.write(string.encode())
        self.con.flush() '''

        ''' in_waiting_before = 0
        sleep(1)

        while in_waiting_before != self.con.in_waiting:
            in_waiting_before = self.con.in_waiting
            sleep(0.5)

        print(self.con.in_waiting)
        data = self.con.read(self.con.in_waiting)
        print(data)
        print(data.decode(), end='')

        string = '25814@root\n'
        self.con.write(string.encode())
        self.con.flush()

        in_waiting_before = 0
        sleep(1)

        while in_waiting_before != self.con.in_waiting:
            in_waiting_before = self.con.in_waiting
            sleep(0.5)

        print(self.con.in_waiting)
        data = self.con.read(self.con.in_waiting)
        print(data)
        print(data.decode(), end='') '''

        # check if we already logged in
        # If we we get something like [root@localhost ~]#
        #self.readline()

       # if not self.check_logged_in(username):
            #print("Try to login")
            #if self.login(username, password):
            #    print("Could not login")
            #    return False

        #pattern = "^\[" + username + "@.+\]#"
        #print(pattern)
        #data = self.readline(pattern=pattern)
        #if data["return-code"] == 1:
       #         print("We are logged in")
       # else:
         #      print("We are  not logged in")
               # login

        #while 1:
            #data = self.readline("^.*login:")
           # if data["return-code"] == 1:
             #   break

        # string = 'cd / && ls \n'
        # self.con.write(string.encode())
        # self.con.flush()
        # #print(self.con.read(5))

        # data = self.readline()
        # self.log_console_line(data.decode())

        # while not self.back_at_prompt():
        #     data = self.readline()
        #     self.log_console_line(data.decode())

        ''' in_waiting_before = 0
        sleep(1)

        while in_waiting_before != self.con.in_waiting:
            in_waiting_before = self.con.in_waiting
            sleep(0.5)

        print(self.con.in_waiting)
        data = self.con.read(self.con.in_waiting)
        data = data.decode()

        pattern = "^\[" + username + "@.+\]# $"
        pattern = re.compile(pattern, re.MULTILINE)
        if pattern.match(data, re.MULTILINE):
            print("It works")

        print(data, end='') '''


    #@property
    #def con(self):
    #    return self.con


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


    def readline2(self, pattern=None):
        string = ""
        string2 = b""
        if pattern:
            pattern = re.compile(pattern)

        while 1:
            char = self.con.read(1)
            string = string + char.decode("utf-8")
            string2 = string2 + char
            #print(char)
            print(char.decode("utf-8"), end="")

            #print(string2)
            if pattern and pattern.match(string):
               #print("get here1")
               #print(string2)
               return {"string" : string, "return-code" : 1}

            if char == b"\n":
                #print(char)
                #print(string2)
                #print("get here2")
                return {"return-code" : 0}

    def check_logged_in(self, username):
        pattern = "^\[" + username + "@.+\]#"
        data = self.readline(pattern=pattern)
        if data["return-code"] == 1:
                print("We are logged in")
                return True
        else:
            print("We are  not logged in")
            return False

    def login(self, password):
        if self.username == None:
            self.log.error("Username cannot be blank")
            return False

        # Hit enter to see what we get
        self.con.write(b'\n')
        # We get two new lines \r\n ?
        data = self.readline()
        self.log_console_line(data.decode())


        if self.back_at_prompt():
            self.log.debug("We are already logged in.")
            return True

        # Read all line till we get login:
        while 1:
            data = self.peek()
            if not data.decode() == "l":
                self.log.debug("We get no l at the start")
                self.log_console_line(self.readline().decode())

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
        self.write("{}\n".format(command))

        # We need to read out the prompt for this command first
        # If we do not do this we will break the loop immediately
        # because the prompt for this command is still in the buffer
        data = self.readline()
        self.log_console_line(data.decode())

        while not self.back_at_prompt():
            data = self.readline()
            self.log_console_line(data.decode())


#    while True:

#        line = self.readline()

#        print (line)

#        print("Hello")

#        print("World")

#        Hello
#        World

#        Hello World

#        # Peek for prompt?
#        if self.back_at_prompt():
#            break

# def back_at_prompt():
#     data = self.peek()

#     if not char == "[":
#         return False

#     data = self.peek(in_waiting)
#     m = re.search(..., data)
#     if m:
#         return True





# pattern = r"^\[root@.+\]#"

# pattern = re.compile(pattern, re.MULTILINE)

# data = """cd / && ls
# bin   dev  home  lib64	     media  opt   root	sbin  sys  usr
# boot  etc  lib	 lost+found  mnt    proc  run	srv   tmp  var
# [root@localhost /]# """

# #data = "[root@localhost /]# "
# data2 = pattern.search(data)

# #if pattern.search(data):
#    # print("get here")

# #print(data2.group())



vm = vm("qemu:///system")

dom = vm.domain_start_from_xml_file("/home/jonatan/python-testing-kvm/centos2.xml")

# This block till the vm is booted
print("Waiting till the domain is booted up")
vm.check_domain_is_booted_up(dom)
print("Domain is booted up")
#vm.domain_get_serial_device(dom)
#vm.domain_get_serial_device(dom)

versuch1 = connection(vm.domain_get_serial_device(dom), username="root")
versuch1.login("25814@root")
versuch1.command("cd / && ls")


# def command(self, command):
#     self._send_command(command)

#    while True:
#        line = self.readline()

#        print (line)

#        print("Hello")

#        print("World")

#        Hello
#        World

#        Hello World

#        # Peek for prompt?
#        if self.back_at_prompt():
#            break

# def back_at_prompt():
#     data = self.peek()

#     if not char == "[":
#         return False

#     data = self.peek(in_waiting)
#     m = re.search(..., data)
#     if m:
#         return True





# class connection()
#     buffer = b""

#     def read(self, size=1):
#         if len(buffer) >= size:
#             # throw away first size bytes in buffer
#             data, buffer = buffer[:size], buffer[size:]
#             return data

#         return self.serial.read(size)

#     def peek(self, size=1):
#         if len(buffer) <= size:
#             buffer += self.serial.read(size=size - len(buffer))

#         return buffer[:size]


#     def readline(self):
#         buffer = buffer + self.serial.read(in_wating)
#         if "\n" in buffer:
#             return alle zeichen bis zum \n

#         return buffer + self.serial.readline()
