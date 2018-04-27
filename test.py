#!/usr/bin/python3


import libvirt

import xml.etree.ElementTree as ET

import os

import configparser

from disk import disk

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


class machine():
    def __init__(self, vm_xml_file, snapshot_xml_file, image, root_uid, username, password):
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
        self.disk = disk(image)

        self.username = username
        self.password = password

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
        serial_con = serial_connection(self.get_serial_device())

        serial_con.write("\n")
        # This will block till the domain is booted up
        serial_con.read(1)

        #serial_con.close()

    def login(self):
        try:
            self.serial_con = serial_connection(self.get_serial_device(), username=self.username)
            self.serial_con.login(self.password)
        except BaseException as e:
            self.log.error("Could not connect to the domain via serial console")

    def cmd(self, cmd):
        return self.serial_con.command(cmd)

    def copy_in(self, fr, to):
        try:
            self.disk.mount(self.root_uid, "/")
            self.disk.copy_in(fr, to)
        except BaseException as e:
            self.log.error(e)
        finally:
            self.disk.umount("/")
            self.disk.close()



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
    def __init__(self, path, circle=[]):
        self.log = log(4)
        self.recipe_file = path
        self.path = os.path.dirname(self.recipe_file)
        self.log.debug("Path of recipe is: {}".format(self.recipe_file))
        self._recipe = None
        self._machines = None

        self.in_recursion = True
        if len(circle) == 0:
            self.in_recursion = False

        self.circle = circle
        self.log.debug(circle)
        self.log.debug(self.circle)

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

    @property
    def machines(self):
        if not self._machines:
            self._machines = []
            for line in self._recipe:
                if line[0] != "all" and line[0] not in self._machines:
                    self._machines.append(line[0])

        return self._machines

    def parse(self):
        self._recipe = []
        i = 1
        for line in self.raw_recipe:
            raw_line = line.split(":")
            if len(raw_line) < 2:
                self.log.error("Error parsing the recipe in line {}".format(i))
                raise RecipeExeption
            cmd = raw_line[1].strip()
            raw_line = raw_line[0].strip().split(" ")
            if len(raw_line) == 0:
                self.log.error("Failed to parse the recipe in line {}".format(i))
                raise RecipeExeption

            if raw_line[0].strip() == "":
                    self.log.error("Failed to parse the recipe in line {}".format(i))
                    raise RecipeExeption

            machine = raw_line[0].strip()

            if len(raw_line) == 2:
                extra = raw_line[1].strip()
            else:
                extra = ""

            # We could get a machine here or a include statement
            if machine == "include":
                path = cmd.strip()
                path = os.path.normpath(self.path + "/" + path)
                path = path + "/recipe"
                if path in self.circle:
                    self.log.error("Detect import loop!")
                    raise RecipeExeption
                self.circle.append(path)
                recipe_to_include = recipe(path, circle=self.circle)

            if machine == "include":
                self._recipe.extend(recipe_to_include.recipe)
            else:
                # Support also something like 'alice,bob: echo'
                machines = machine.split(",")
                for machine in machines:
                    self._recipe.append((machine.strip(), extra.strip(), cmd.strip()))
            i = i + 1

            if not self.in_recursion:
                tmp_recipe = []
                for line in self._recipe:
                    if line[0] != "all":
                        tmp_recipe.append(line)
                    else:
                        for machine in self.machines:
                            tmp_recipe.append((machine.strip(), line[1], line[2]))

                self._recipe = tmp_recipe



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
        self.copy_to = self.config["DEFAULT"]["Copy_to"]
        self.copy_from = self.config["DEFAULT"]["Copy_from"]
        self.copy_from = self.copy_from.split(",")

        tmp = []
        for file in self.copy_from:
            file = file.strip()
            file = os.path.normpath(self.path + "/" + file)
            tmp.append(file)

        self.copy_from = tmp

        self.virtual_environ_name = self.config["VIRTUAL_ENVIRONMENT"]["Name"]
        self.virtual_environ_path = self.config["VIRTUAL_ENVIRONMENT"]["Path"]
        self.virtual_environ_path = os.path.normpath(self.path + "/" + self.virtual_environ_path)

    def virtual_environ_setup(self):
        self.virtual_environ = virtual_environ(self.virtual_environ_path)

        self.virtual_networks = self.virtual_environ.get_networks()

        self.virtual_machines = self.virtual_environ.get_machines()

    def virtual_environ_start(self):
        for name in self.virtual_environ.network_names:
            self.virtual_networks[name].define()
            self.virtual_networks[name].start()

        for name in self.virtual_environ.machine_names:
            self.virtual_machines[name].define()
            self.virtual_machines[name].create_snapshot()
            self.virtual_machines[name].copy_in(self.copy_from, self.copy_to)
            self.virtual_machines[name].start()

        self.log.debug("Try to login on all machines")
        for name in self.virtual_environ.machine_names:
            self.virtual_machines[name].login()

    def load_recipe(self):
        try:
            self.recipe = recipe(self.recipe_file)
        except BaseException:
            self.log.error("Failed to load recipe")
            exit(1)

    def run_recipe(self):
        for line in self.recipe.recipe:
            return_value = self.virtual_machines[line[0]].cmd(line[2])
            self.log.debug("Return value is: {}".format(return_value))
            if return_value != "0" and line[1] == "":
                self.log.error("Failed to execute command '{}' on {}, return code: {}".format(line[2],line[0], return_value))
                return False
            elif return_value == "0" and line[1] == "!":
                self.log.error("Succeded to execute command '{}' on {}, return code: {}".format(line[2],line[0],return_value))
                return False
            else:
                self.log.debug("Command '{}' on {} returned with: {}".format(line[2],line[0],return_value))

    def virtual_environ_stop(self):
        for name in self.virtual_environ.machine_names:
            self.virtual_machines[name].shutdown()
            self.virtual_machines[name].revert_snapshot()
            self.virtual_machines[name].undefine()

        for name in self.virtual_environ.network_names:
            self.virtual_networks[name].undefine()


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
            machines.setdefault(_machine, machine(
                os.path.normpath(self.path + "/" + self.config[_machine]["xml_file"]),
                os.path.normpath(self.path + "/" + self.config[_machine]["snapshot_xml_file"]),
                self.config[_machine]["image"],
                self.config[_machine]["root_uid"],
                self.config[_machine]["username"],
                self.config[_machine]["password"]))

        return machines

    @property
    def machine_names(self):
        return self.machines

    @property
    def network_names(self):
        return self.networks


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", dest="dir")

    args = parser.parse_args()

    currenttest = test(args.dir)
    currenttest.read_settings()
    currenttest.virtual_environ_setup()
    currenttest.load_recipe()
    try:
        currenttest.virtual_environ_start()
        currenttest.run_recipe()
    except BaseException as e:
        print(e)
    finally:
        currenttest.virtual_environ_stop()

