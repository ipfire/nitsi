#!/usr/bin/python3


import libvirt

import os

import configparser

import time

from nitsi.virtual_environ import virtual_environ
from nitsi.recipe import recipe

import logging

logger = logging.getLogger("nitsi.test")

class test():
    def __init__(self, path, log_path):
        try:
            self.path = os.path.abspath(path)
            self.log = logger.getChild(os.path.basename(self.path))
        except BaseException as e:
            logger.error("Could not get absolute path")

        self.log.debug("Path of this test is: {}".format(self.path))

        self.log_path = log_path

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

        # Time to which all serial output log entries are relativ
        log_start_time = time.time()

        self.log.debug("Try to login on all machines")
        for name in self.virtual_environ.machine_names:
            self.log.debug("Try to login on {}".format(name))
            self.virtual_machines[name].login("{}/test.log".format(self.log_path), log_start_time)

    def load_recipe(self):
        self.log.info("Going to load the recipe")
        try:
            self.recipe = recipe(self.recipe_file)
            for line in self.recipe.recipe:
                self.log.debug(line)

            self.log.debug("This was the recipe")
        except BaseException as e:
            self.log.error("Failed to load recipe")
            raise e

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



