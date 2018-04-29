#!/usr/bin/python3

from machine import machine

from network import network

import os
import configparser
import libvirt

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

        self.uri = self.config["DEFAULT"]["uri"]

        try:
            self.con = libvirt.open(self.uri)
        except BaseException as error:
            self.log.error("Could not connect to: {}".format(self.uri))

        self.log.debug("Connected to: {}".format(self.uri))

    def get_networks(self):
        networks = {}
        for _network in self.networks:
            self.log.debug(_network)
            networks.setdefault(_network, network(self.con, os.path.normpath(self.path + "/" + self.config[_network]["xml_file"])))
        return networks

    def get_machines(self):
        machines = {}
        for _machine in self.machines:
            self.log.debug(_machine)
            machines.setdefault(_machine, machine(
                self.con,
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