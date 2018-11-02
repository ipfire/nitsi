#!/usr/bin/python3

import collections
import guestfs
import logging
import os
import tarfile
import tempfile

logger = logging.getLogger("nitsi.disk")

class DiskExeption(Exception):
    def __init__(self, message):
        self.message = message

class Disk():
    def __init__(self, disk):
        self.log = logger.getChild(os.path.basename(disk))
        self.log.debug("Initiated a disk class for {}".format(disk))
        self.con = guestfs.GuestFS(python_return_dict=True)
        self.con.add_drive_opts(disk, format="qcow2")

    def mount(self):
        self.log.info("Trying to mount all partions of the found operating system")
        for mountpoint, partition in self.mountpoints.items():
            self.log.info("Trying to mount the partion {} under {}".format(partition, mountpoint))
            self.con.mount(partition, mountpoint)

    def inspect(self):
        self.con.launch()

        # This inspects the given Disk and
        # returns all root filesystems of the operating systems on this disk
        root_filesystem = self.con.inspect_os()

        # If we found more the one rootfile system we throw an error
        # because we do not support multi boot systems
        if len(root_filesystem) > 1:
            raise DiskExeption("Found more then one operating system on the given disk.")

        # We cannot go on if we found no operating system
        if len(root_filesystem) == 0:
            raise DiskExeption("Found no operating system on the given disk.")

        root_filesystem = root_filesystem.pop()

        # Get mountpoints of all filesystems accociated with this operationg system
        tmp = self.con.inspect_get_mountpoints(root_filesystem)

        # Sort mountpoints by length to mount / before /usr
        # We are using an ordered dict here to keep the order of the keys
        self.mountpoints = collections.OrderedDict(sorted(tmp.items(), key=lambda t: len(t[0])))

        self.log.debug(self.mountpoints)

        # Print some nice information about the found operationg system
        self.log.info("Arch of the installed operating system: {}".format(
            self.con.inspect_get_arch(root_filesystem)))
        self.log.info("Distribution of the installed operating system: {}".format(
            self.con.inspect_get_distro(root_filesystem)))


    def copy_in(self, fr, to):
        self.log.info("Going to copy some files into the image.")
        tmp = tempfile.mkstemp()
        tmp = tmp[1] + ".tar"
        self.log.debug("Path of tarfile is: {}".format(tmp))
        with tarfile.open(tmp, "w") as tar:
            for file in fr:
                self.log.debug("Adding {} to be copied into the image".format(file))
                tar.add(file, arcname=os.path.basename(file))

        self.log.info("Going to copy the files into the image")
        self.con.tar_in_opts(tmp, to)
        self.log.debug(self.con.ls(to))

    def umount(self):
        self.log.info("Trying to unmount all partions of the found operating system")
        for mountpoint, partition in reversed(self.mountpoints.items()):
            self.log.info("Trying to unmount the partion {} under {}".format(partition, mountpoint))
            self.con.umount_opts(mountpoint)

    def close(self):
        self.log.info("Flush the image and closing the connection")
        self.con.shutdown()
        self.con.close()

# test  = Disk("/var/lib/libvirt/images/ipfire-bob.qcow2")
# test.mount("1efb5389-0949-46bb-b688-5246acba9f6d", "/")
# test.copy_in("/home/jonatan/nitsi/libguestfs-test", "/root/")
# test.umount("/")
# test.close()
