#!/usr/bin/python3

import guestfs
import logging
import os
import tarfile
import tempfile

logger = logging.getLogger("nitsi.disk")


class disk():
    def __init__(self, disk):
        self.log = logger.getChild(os.path.basename(disk))
        self.log.debug("Initiated a disk class for {}".format(disk))
        self.con = guestfs.GuestFS(python_return_dict=True)
        self.con.add_drive_opts(disk, format="qcow2")

    def mount(self, uuid, path):
        self.log.debug("Trying to mount the partion with uuid: {} under {}".format(uuid, path))
        self.con.launch()
        part = self.con.findfs_uuid(uuid)
        self.con.mount(part, path)

    def copy_in(self, fr, to):
        self.log.debug("Going to copy some files into the image.")
        tmp = tempfile.mkstemp()
        tmp = tmp[1] + ".tar"
        with tarfile.open(tmp, "w") as tar:
            for file in fr:
                self.log.debug("Adding {} to be copied into the image".format(file))
                tar.add(file, arcname=os.path.basename(file))

        self.log.debug("Going to copy the files into the image")
        self.con.tar_in_opts(tmp, to)

    def umount(self, path):
        self.log.debug("Unmounting the image")
        self.con.umount_opts(path)

    def close(self):
        self.log.debug("Flush the image and closing the connection")
        self.con.shutdown()
        self.con.close()

# test  = disk("/var/lib/libvirt/images/alice.qcow2")
# test.mount("45598e92-3487-4a1b-961d-79aa3dd42a7d", "/")
# test.copy_in("/home/jonatan/nitsi/libguestfs-test", "/root/")
# test.umount("/")
# test.close()
