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
    def __init__(self, log_path, dir=None, recipe_file=None, settings_file=None, cmd_settings=None):
        # init settings var
        self.settings = {}

        self.cmd_settings = cmd_settings
        self.log_path = log_path

        # Init all vars with None
        self.settings_file = None
        self.recipe_file = None
        self.path = None

        # We need at least a path to a recipe file or a dir to a test
        if not dir and not recipe:
            raise TestException("Did not get a path to a test or to a recipe file")

        # We cannot decide which to use when we get both
        if (dir and recipe_file) or (dir and settings_file):
            raise TestException("Get dir and path to recipe or settings file")

        if dir:
            try:
                if not os.path.isabs(dir):
                    self.path = os.path.abspath(dir)
            except BaseException as e:
                logger.error("Could not get absolute path")
                raise e

            logger.debug("Path of this test is: {}".format(self.path))

            self.recipe_file = "{}/recipe".format(self.path)
            self.settings_file = "{}/settings".format(self.path)

        if recipe_file:
            if not os.path.isabs(recipe_file):
                self.recipe_file = os.path.abspath(recipe_file)
            else:
                self.recipe_file = recipe_file

        if settings_file:
            if not os.path.isabs(settings_file):
                self.settings_file = os.path.abspath(settings_file)
            else:
                self.settings_file = settings_file

        if not os.path.isfile(self.settings_file):
            logger.error("No such file: {}".format(self.settings_file))
            raise TestException("No settings file found")

        if not os.path.isfile(self.recipe_file):
            logger.error("No such file: {}".format(self.recipe_file))
            raise TestException("No recipe file found")

        # Init logging
        if dir:
             self.log = logger.getChild(os.path.basename(self.path))

        if recipe:
            self.log = logger.getChild(os.path.basename(self.recipe_file))

    def read_settings(self):
        if self.settings_file:
            self.log.debug("Going to read all settings from the ini file")
            try:
                self.config = configparser.ConfigParser()
                self.config.read(self.settings_file)
            except BaseException as e:
                self.log.error("Failed to parse the config")
                raise e

            self.settings["name"] = self.config.get("GENERAL","name", fallback="")
            self.settings["description"] = self.config.get("GENERAL", "description",  fallback="")
            self.settings["copy_to"] = self.config.get("GENERAL", "copy_to", fallback=None)
            self.settings["copy_from"] = self.config.get("GENERAL", "copy_from", fallback=None)
            self.settings["virtual_environ_path"] = self.config.get("VIRTUAL_ENVIRONMENT", "path", fallback=None)

        if not self.settings["virtual_environ_path"]:
            self.log.error("No path for virtual environment found.")
            raise TestException("No path for virtual environment found.")

        self.settings["virtual_environ_path"] = os.path.normpath(self.path + "/" + self.settings["virtual_environ_path"])

        # Parse copy_from setting
        if self.settings["copy_from"]:
            self.log.debug("Going to parse the copy_from setting.")
            self.settings["copy_from"] = self.settings["copy_from"].split(",")

            tmp = []
            for file in self.settings["copy_from"]:
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

            self.settings["copy_from"] = tmp



    def virtual_environ_setup(self):
        self.virtual_environ = virtual_environ.Virtual_environ(self.settings["virtual_environ_path"])

        self.virtual_networks = self.virtual_environ.get_networks()

        self.virtual_machines = self.virtual_environ.get_machines()

    def virtual_environ_start(self):
        for name in self.virtual_environ.network_names:
            self.virtual_networks[name].define()
            self.virtual_networks[name].start()

        for name in self.virtual_environ.machine_names:
            self.virtual_machines[name].define()
            self.virtual_machines[name].create_snapshot()
            # We can only copy files when we know which and to which dir
            if self.settings["copy_from"] and self.settings["copy_to"]:
                self.virtual_machines[name].copy_in(self.settings["copy_from"], self.settings["copy_to"])
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

