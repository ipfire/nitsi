#!/usr/bin/python3

import serial

import re
from time import sleep
import sys

import libvirt

import xml.etree.ElementTree as ET

import inspect
import os

import configparser

class log():
    def __init__(self, log_level):
        self.log_level = log_level

    def debug(self, string):
        if self.log_level >= 4:
            print("DEBUG: {}".format(string))

    def error(self, string):
        print("ERROR: {}".format(string))

class libvirt_con():
    def __init__(self, uri):
        self.log = log(4)
        self.uri = uri
        self.connection = None

    def get_domain_from_name(self, name):
        dom = self.con.lookupByName(name)

        if dom == None:
            raise BaseException
        return dom

    @property
    def con(self):
        if self.connection == None:
            try:
                self.connection = libvirt.open(self.uri)
            except BaseException as error:
                self.log.error("Could not connect to: {}".format(self.uri))

            self.log.debug("Connected to: {}".format(self.uri))
            return self.connection

        return self.connection


class vm():
    def __init__(self, vm_xml_file, snapshot_xml_file, image, root_uid):
        self.log = log(4)
        self.con = libvirt_con("qemu:///system")
        try:
            with open(vm_xml_file) as fobj:
                self.vm_xml = fobj.read()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(vm_xml_file))

        try:
            with open(snapshot_xml_file) as fobj:
                self.snapshot_xml = fobj.read()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(snapshot_xml_file))

        self.image = image

        if not os.path.isfile(self.image):
            self.log.error("No such file: {}".format(self.image))

        self.root_uid = root_uid

    def define(self):
        self.dom = self.con.con.defineXML(self.vm_xml)
        if self.dom == None:
            self.log.error("Could not define VM")
            raise BaseException

    def start(self):
        if self.dom.create() < 0:
            self.log.error("Could not start VM")
            raise BaseException

    def shutdown(self):
        if self.is_running():
            if self.dom.shutdown() < 0:
                self.log.error("Could not shutdown VM")
                raise BaseException
        else:
            self.log.error("Domain is not running")

    def undefine(self):
        self.dom.undefine()

    def create_snapshot(self):

        self.snapshot = self.dom.snapshotCreateXML(self.snapshot_xml)

        if not self.snapshot:
            self.log.error("Could not create snapshot")
            raise BaseException

    def revert_snapshot(self):
        print(inspect.getmembers(self.dom, predicate=inspect.ismethod))
        self.dom.revertToSnapshot(self.snapshot)
        self.snapshot.delete()

    def is_running(self):

        state, reason = self.dom.state()

        if state == libvirt.VIR_DOMAIN_RUNNING:
            return True
        else:
            return False

    def get_serial_device(self):

        if not self.is_running():
            raise BaseException

        xml_root = ET.fromstring(self.dom.XMLDesc(0))

        elem = xml_root.find("./devices/serial/source")
        return elem.get("path")

    def check_is_booted_up(self):
        serial_con = connection(self.get_serial_device())

        serial_con.write("\n")
        # This will block till the domain is booted up
        serial_con.read(1)

        #serial_con.close()

    def login(self, username, password):
        try:
            self.serial_con = connection(self.get_serial_device(), username="root")
            self.serial_con.login("25814@root")
        except BaseException as e:
            self.log.error("Could not connect to the domain via serial console")

    def cmd(self, cmd):
        return self.serial_con.command(cmd)


class connection():
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


# A class which define and undefine a virtual network based on an xml file
class network():
    def __init__(self, network_xml_file):
        self.log = log(4)
        self.con = libvirt_con("qemu:///system")
        try:
            with open(network_xml_file) as fobj:
                self.network_xml = fobj.read()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(vm_xml_file))

    def define(self):
        self.network = self.con.con.networkDefineXML(self.network_xml)

        if network == None:
            self.log.error("Failed to define virtual network")

    def start(self):
        self.network.create()

    def undefine(self):
        self.network.destroy()



class RecipeExeption(Exception):
    pass



# Should read the test, check if the syntax are valid
# and return tuples with the ( host, command ) structure
class recipe():
    def __init__(self, path):
        self.log = log(4)
        self.recipe_file = path
        self._recipe = None

        if not os.path.isfile(self.recipe_file):
            self.log.error("No such file: {}".format(self.recipe_file))

        try:
            with open(self.recipe_file) as fobj:
                self.raw_recipe = fobj.readlines()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(vm_xml_file))

    @property
    def recipe(self):
        if not self._recipe:
            self.parse()

        return self._recipe

    def parse(self):
        self._recipe = []
        i = 1
        for line in self.raw_recipe:
            raw_line = line.split(":")
            if len(raw_line) < 2:
                self.log.error("Error parsing the recipe in line {}".format(i))
                raise RecipeExeption
            cmd = raw_line[1]
            raw_line = raw_line[0].strip().split(" ")
            if len(raw_line) == 0:
                self.log.error("Failed to parse the recipe in line {}".format(i))
                raise RecipeExeption
            elif len(raw_line) == 1:
                if raw_line[0] == "":
                    self.log.error("Failed to parse the recipe in line {}".format(i))
                    raise RecipeExeption
                machine = raw_line[0]
                extra = ""
            elif len(raw_line) == 2:
                machine = raw_line[0]
                extra = raw_line[1]

            self._recipe.append((machine.strip(), extra.strip(), cmd.strip()))
            i = i + 1


class test():
    def __init__(self, path):
        self.log = log(4)
        try:
            self.path = os.path.abspath(path)
        except BaseException as e:
            self.log.error("Could not get absolute path")

        self.log.debug(self.path)

        self.settings_file = "{}/settings".format(self.path)
        if not os.path.isfile(self.settings_file):
            self.log.error("No such file: {}".format(self.settings_file))

        self.recipe_file = "{}/recipe".format(self.path)
        if not os.path.isfile(self.recipe_file):
            self.log.error("No such file: {}".format(self.recipe_file))

    def read_settings(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.settings_file)
        self.name = self.config["DEFAULT"]["Name"]
        self.description = self.config["DEFAULT"]["Description"]

        self.virtual_environ_name = self.config["VIRTUAL_ENVIRONMENT"]["Name"]
        self.virtual_environ_path = self.config["VIRTUAL_ENVIRONMENT"]["Path"]
        self.virtual_environ_path = os.path.normpath(self.path + "/" + self.virtual_environ_path)

    def virtual_environ_setup(self):
        self.virtual_environ = virtual_environ(self.virtual_environ_path)

        self.virtual_networks = self.virtual_environ.get_networks()

        self.virtual_machines = self.virtual_environ.get_machines()

    def virtual_environ_start(self):
        pass

    def load_recipe(self):
        pass

    def run_recipe():
        pass

    def virtual_environ_stop():
        pass


# Should return all vms and networks in a list
# and should provide the path to the necessary xml files
class virtual_environ():
    def __init__(self, path):
        self.log = log(4)
        try:
            self.path = os.path.abspath(path)
        except BaseException as e:
            self.log.error("Could not get absolute path")

        self.log.debug(self.path)

        self.settings_file = "{}/settings".format(self.path)
        if not os.path.isfile(self.settings_file):
            self.log.error("No such file: {}".format(self.settings_file))

        self.log.debug(self.settings_file)
        self.config = configparser.ConfigParser()
        self.config.read(self.settings_file)
        self.name = self.config["DEFAULT"]["name"]
        self.machines_string = self.config["DEFAULT"]["machines"]
        self.networks_string = self.config["DEFAULT"]["networks"]

        self.machines = []
        for machine in self.machines_string.split(","):
            self.machines.append(machine.strip())

        self.networks = []
        for network in self.networks_string.split(","):
            self.networks.append(network.strip())

        self.log.debug(self.machines)
        self.log.debug(self.networks)

    def get_networks(self):
        networks = {}
        for _network in self.networks:
            self.log.debug(_network)
            networks.setdefault(_network, network(os.path.normpath(self.path + "/" + self.config[_network]["xml_file"])))
        return networks

    def get_machines(self):
        machines = {}
        for _machine in self.machines:
            self.log.debug(_machine)
            machines.setdefault(_machine, vm(
                os.path.normpath(self.path + "/" + self.config[_machine]["xml_file"]),
                os.path.normpath(self.path + "/" + self.config[_machine]["snapshot_xml_file"])))

        return machines


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", dest="dir")

    args = parser.parse_args()

    _recipe = recipe("/home/jonatan/python-testing-kvm/test/recipe")
    currenttest = test(args.dir)
    currenttest.read_settings()
    currenttest.virtual_environ_setup()