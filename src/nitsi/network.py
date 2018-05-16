#!/usr/bin/python3

import logging
import os

logger = logging.getLogger("nitsi.network")

# # A class which define and undefine a virtual network based on an xml file
class network():
    def __init__(self, libvirt_con, network_xml_file):
        self.log = logger.getChild(os.path.basename(network_xml_file))
        self.con = libvirt_con
        try:
            with open(network_xml_file) as fobj:
                self.network_xml = fobj.read()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(network_xml_file))

    def define(self):
        self.network = self.con.networkDefineXML(self.network_xml)

        if network == None:
            self.log.error("Failed to define virtual network")

    def start(self):
        self.network.create()

    def undefine(self):
        self.network.destroy()