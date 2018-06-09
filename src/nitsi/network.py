#!/usr/bin/python3

import logging
import os

logger = logging.getLogger("nitsi.network")

# # A class which define and undefine a virtual network based on an xml file
class network():
    def __init__(self, libvirt_con, network_xml_file):
        self.log = logger.getChild(os.path.basename(os.path.dirname(network_xml_file)))
        self.con = libvirt_con
        self.network = None
        try:
            with open(network_xml_file) as fobj:
                self.log.info("Reading xml file for network")
                self.network_xml = fobj.read()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(network_xml_file))
            raise error

    def define(self):
        self.log.info("Going to define network")
        self.network = self.con.networkDefineXML(self.network_xml)

        if self.network == None:
            self.log.error("Failed to define virtual network")

    def start(self):
        self.log.info("Starting Network")
        self.network.create()

    def undefine(self):
        if self.network != None:
            if self.network.isActive() == 1:
                self.log.info("Shutting down network")
                self.network.destroy()

            self.log.info("Undefining network")
            self.network.undefine()