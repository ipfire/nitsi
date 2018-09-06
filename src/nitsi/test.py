#!/usr/bin/python3

import configparser
import libvirt
import logging
import os
import time

from . import recipe
from . import virtual_environ
from . import settings
from . import cmd

logger = logging.getLogger("nitsi.test")


class TestException(Exception):
    def __init__(self, message):
        self.message = message

class Test():
    def __init__(self, log_path, dir=None, recipe_file=None, settings_file=None, cmd_settings=None):
        # init settings var
        self.settings = {}

        # Set default values for the settings dict
        self.settings["name"] = ""
        self.settings["description"] = ""
        self.settings["copy_from"] = None
        self.settings["copy_to"] = None
        self.settings["virtual_environ_path"] = None
        self.settings["interactive_error_handling"] = True

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

        # We can also go on without a settings file
        if self.settings_file:
            if not os.path.isfile(self.settings_file):
                logger.error("No such file: {}".format(self.settings_file))
                raise TestException("No settings file found")

        # os.path.isfile fails if self.recipe_file is None so we cannot use an and statement
        if self.recipe_file:
            if not os.path.isfile(self.recipe_file):
                logger.error("No such file: {}".format(self.recipe_file))
                raise TestException("No recipe file found")
        else:
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

            # We need to parse some settings here because they are loaded from a settings file
            if not os.path.isabs(self.settings["virtual_environ_path"]):
                self.settings["virtual_environ_path"] = os.path.normpath(os.path.dirname(
                    self.settings_file) + "/" + self.settings["virtual_environ_path"])

            # Parse copy_from setting
            if self.settings["copy_from"]:
                self.settings["copy_from"] = settings.settings_parse_copy_from(self.settings["copy_from"],
                path=os.path.dirname(self.settings_file))

        # Update all settings from the cmd
        self.settings.update(self.cmd_settings)

        if not os.path.isabs(self.settings["virtual_environ_path"]):
            self.settings["virtual_environ_path"] = os.path.abspath(self.settings["virtual_environ_path"])


        # Check if we get at least a valid a valid path to virtual environ
        if not self.settings["virtual_environ_path"]:
            self.log.error("No path for virtual environment found.")
            raise TestException("No path for virtual environment found.")

        # Print all settings for debugging purpose
        self.log.debug("Settings are:")
        for key in self.settings:
            self.log.debug("{}: {}".format(key, self.settings[key]))


    def virtual_environ_setup_stage_1(self):
        self.virtual_environ = virtual_environ.VirtualEnviron(self.settings["virtual_environ_path"])

        self.virtual_networks = self.virtual_environ.get_networks()

        self.virtual_machines = self.virtual_environ.get_machines()

    def virtual_environ_setup_stage_2(self):
        # built up which machines which are used in our recipe
        used_machines = []

        for line in self.recipe.recipe:
            if not line[0] in used_machines:
                used_machines.append(line[0])

        self.log.debug("Machines used in this recipe {}".format(used_machines))

        self.used_machine_names = used_machines

        for machine in self.used_machine_names:
            if not machine in self.virtual_environ.machine_names:
                raise TestException("{} is listed as machine in the recipe, but the virtual environmet does not have such a machine".format(machine))


    def virtual_environ_start(self):
        for name in self.virtual_environ.network_names:
            self.virtual_networks[name].define()
            self.virtual_networks[name].start()

        for name in self.used_machine_names:
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

        self.log.info("Try to intialize the serial connection, connect and login on all machines")
        for name in self.used_machine_names:
            self.log.info("Try to initialize the serial connection connect and login on {}".format(name))
            self.virtual_machines[name].serial_init(log_file="{}/test.log".format(self.log_path),
                                                log_start_time=log_start_time,
                                                longest_machine_name=longest_machine_name)
            self.virtual_machines[name].serial_connect()

    def load_recipe(self):
        self.log.info("Going to load the recipe")
        try:
            self.recipe = recipe.Recipe(self.recipe_file,
                fallback_machines=self.virtual_environ.machine_names)

            for line in self.recipe.recipe:
                self.log.debug(line)

            self.log.debug("This was the recipe")
        except BaseException as e:
            self.log.error("Failed to load recipe")
            raise e

    # This functions tries to handle an rror of the test (eg. when 'echo "Hello World"' failed)
    # in an interactive way
    # returns False when the test should exit right now, and True when the test should go on
    def interactive_error_handling(self):
        if not self.settings["interactive_error_handling"]:
            return False

        _cmd = cmd.CMD(intro="You are droppped into an interative debugging shell because of the previous errors",
            help={"exit": "Exit the test rigth now",
                "continue": "Continues the test without any error handling, so do not expect that the test succeeds.",
                "debug": "Disconnects from the serial console and prints the devices to manually connect to the virtual machines." \
                    "This is useful when you can fix th error with some manual commands. Please disconnect from the serial consoles and " \
                    "choose 'exit or 'continue'  when you are done"})

        command = _cmd.get_input(valid_commands=["continue", "exit", "debug"])

        if command == "continue":
            # The test should go on but we do not any debugging, so we return True
            return True
        elif command == "exit":
            # The test should exit right now (normal behaviour)
            return False

        # If we get here we are in debugging mode
        # Disconnect from the serial console:

        for name in self.used_machine_names:
            _cmd.print_to_cmd("Disconnect from the serial console of {}".format(name))
            self.virtual_machines[name].serial_disconnect()

        # Print the serial device for each machine
        for name in self.used_machine_names:
            device  = self.virtual_machines[name].get_serial_device()
            _cmd.print_to_cmd("Serial device of {} is {}".format(name, device))

        _cmd.print_to_cmd("You can now connect to all serial devices, and send custom commands to the virtual machines." \
            "Please type 'continue' or 'exit' when you disconnected from als serial devices and want to go on.")

        command = _cmd.get_input(valid_commands=["continue", "exit"])

        if command == "exit":
            return False

        # We should continue whit the test
        # Reconnect to the serial devices

        for name in self.used_machine_names:
            self.log.info("Try to reconnect to {}".format(name))
            self.virtual_machines[name].serial_connect()

        return True

    def run_recipe(self):
        for line in self.recipe.recipe:
            return_value = self.virtual_machines[line[0]].cmd(line[2])
            self.log.debug("Return value is: {}".format(return_value))
            if return_value != "0" and line[1] == "":
                err_msg = "Failed to execute command '{}' on {}, return code: {}".format(line[2],line[0], return_value)
                # Try to handle this error in an interactive way, if we cannot go on
                # raise an exception and exit
                if not self.interactive_error_handling():
                    raise TestException(err_msg)

            elif return_value == "0" and line[1] == "!":
                err_msg = "Succeded to execute command '{}' on {}, return code: {}".format(line[2],line[0],return_value)
                self.log.error(err_msg)
                # Try to handle this error in an interactive way, if we cannot go on
                # raise an exception and exit
                if not self.interactive_error_handling():
                    raise TestException(err_msg)
            else:
                self.log.debug("Command '{}' on {} returned with: {}".format(line[2],line[0],return_value))

    def virtual_environ_stop(self):
        for name in self.used_machine_names:
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

