#!/usr/bin/python3

import xml.etree.ElementTree as ET

from nitsi.disk import disk

from nitsi.serial_connection import serial_connection

import os
import libvirt

import logging

logger = logging.getLogger("nitsi.machine")

class machine():
    def __init__(self, libvirt_con, vm_xml_file, snapshot_xml_file, image, root_uid, username, password):
        self.log = logger.getChild(os.path.basename(vm_xml_file))
        self.con = libvirt_con
        try:
            with open(vm_xml_file) as fobj:
                self.vm_xml = fobj.read()
        except FileNotFoundError as error:
            logger.error("No such file: {}".format(vm_xml_file))

        try:
            self.name = self.get_name()
        except BaseException as error:
            logger.error("Could not get name of the machine: {}".format(vm_xml_file))
            raise error

        self.log = logger.getChild(self.name)
        self.log.debug("Name of this machine is {}".format(self.name))

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
        self.dom = self.con.defineXML(self.vm_xml)
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

    def get_name(self):
        xml_root = ET.fromstring(self.vm_xml)

        elem = xml_root.find("./name")
        return elem.text

    def check_is_booted_up(self):
        serial_con = serial_connection(self.get_serial_device())

        serial_con.write("\n")
        # This will block till the domain is booted up
        serial_con.read(1)

        #serial_con.close()

    def login(self, log_file, log_start_time=None, longest_machine_name=10):
        try:
            self.serial_con = serial_connection(self.get_serial_device(),
                                username=self.username,
                                log_file=log_file,
                                log_start_time=log_start_time,
                                name=self.name,
                                longest_machine_name=longest_machine_name)
            self.serial_con.login(self.password)
        except BaseException as e:
            self.log.error("Could not connect to the domain via serial console")
            self.log.exception(e)
            raise e

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