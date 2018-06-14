#!/usr/bin/python3

import configparser
import libvirt
import logging
import os
import time

from . import recipe
from . import virtual_environ

logger = logging.getLogger("nitsi.test")


class TestException(Exception):
    def __init__(self, message):
        self.message = message

class Test():
    def __init__(self, path, log_path):
        try:
            self.path = os.path.abspath(path)
            self.log = logger.getChild(os.path.basename(self.path))
        except BaseException as e:
            logger.error("Could not get absolute path")
            raise e

        self.log.debug("Path of this test is: {}".format(self.path))

        self.log_path = log_path

        self.settings_file = "{}/settings".format(self.path)
        if not os.path.isfile(self.settings_file):
            self.log.error("No such file: {}".format(self.settings_file))
            raise TestException("No settings file found")

        self.recipe_file = "{}/recipe".format(self.path)
        if not os.path.isfile(self.recipe_file):
            self.log.error("No such file: {}".format(self.recipe_file))
            raise TestException("No recipe file found")

    def read_settings(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.settings_file)
        self.name = self.config["DEFAULT"]["name"]
        self.description = self.config["DEFAULT"]["description"]
        self.copy_to = self.config["DEFAULT"]["copy_to"]
        self.copy_from = self.config["DEFAULT"]["copy_from"]
        self.virtual_environ_name = self.config["VIRTUAL_ENVIRONMENT"]["name"]
        self.virtual_environ_path = self.config["VIRTUAL_ENVIRONMENT"]["path"]
        self.virtual_environ_path = os.path.normpath(self.path + "/" + self.virtual_environ_path)

        # Parse copy_from setting
        self.copy_from = self.copy_from.split(",")

        tmp = []
        for file in self.copy_from:
            file = file.strip()
            # If file is empty we do not want to add it to the list
            if not file == "":
                # If we get an absolut path we do nothing
                # If not we add self.path to get an absolut path
                if not os.path.isabs(file):
                    file = os.path.normpath(self.path + "/" + file)

                # We need to check if file is a valid file or dir
                if not (os.path.isdir(file) or os.path.isfile(file)):
                    raise TestException("'{}' is not a valid file nor a valid directory".format(file))

                self.log.debug("'{}' will be copied into all images".format(file))
                tmp.append(file)

        self.copy_from = tmp



    def virtual_environ_setup(self):
        self.virtual_environ = virtual_environ.Virtual_environ(self.virtual_environ_path)

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

        # Number of chars of the longest machine name
        longest_machine_name = self.virtual_environ.longest_machine_name

        self.log.info("Try to login on all machines")
        for name in self.virtual_environ.machine_names:
            self.log.info("Try to login on {}".format(name))
            self.virtual_machines[name].login("{}/test.log".format(self.log_path),
                                                log_start_time=log_start_time,
                                                longest_machine_name=longest_machine_name)

    def load_recipe(self):
        self.log.info("Going to load the recipe")
        try:
            self.recipe = recipe.Recipe(self.recipe_file, machines=self.virtual_environ.machine_names)
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
                raise TestException("Failed to execute command '{}' on {}, return code: {}".format(line[2],line[0], return_value))
            elif return_value == "0" and line[1] == "!":
                raise TestException("Succeded to execute command '{}' on {}, return code: {}".format(line[2],line[0],return_value))
            else:
                self.log.debug("Command '{}' on {} returned with: {}".format(line[2],line[0],return_value))

    def virtual_environ_stop(self):
        for name in self.virtual_environ.machine_names:
            # We just catch exception here to avoid
            # that we stop the cleanup process if only  one command fails
            try:
                self.virtual_machines[name].shutdown()
                self.virtual_machines[name].revert_snapshot()
                self.virtual_machines[name].undefine()
            except BaseException as e:
                self.log.exception(e)

        for name in self.virtual_environ.network_names:
            try:
                self.virtual_networks[name].undefine()
            except BaseException as e:
                 self.log.exception(e)

