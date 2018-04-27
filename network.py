#!/usr/bin/python3

# # A class which define and undefine a virtual network based on an xml file
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