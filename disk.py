#!/usr/bin/python3

import guestfs

import tempfile
import tarfile
import os


class disk():
    def __init__(self, disk):
        self.con = guestfs.GuestFS(python_return_dict=True)
        self.con.add_drive_opts(disk, format="qcow2")

    def mount(self, uuid, path):
        self.con.launch()
        part = self.con.findfs_uuid(uuid)
        self.con.mount(part, path)

    def copy_in(self, fr, to):
        tmp = tempfile.mkstemp()
        tmp = tmp[1] + ".tar"
        with tarfile.open(tmp, "w") as tar:
            for file in fr:
                tar.add(file, arcname=os.path.basename(file))
        self.con.tar_in_opts(tmp, to)

    def umount(self, path):
        self.con.umount_opts(path)

    def close(self):
        self.con.shutdown()
        self.con.close()

# test  = disk("/var/lib/libvirt/images/alice.qcow2")
# test.mount("45598e92-3487-4a1b-961d-79aa3dd42a7d", "/")
# test.copy_in("/home/jonatan/nitsi/libguestfs-test", "/root/")
# test.umount("/")
# test.close()