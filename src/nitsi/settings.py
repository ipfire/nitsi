#!/usr/bin/python3

import logging
import os
import configparser

logger = logging.getLogger("nitsi.settings")

class SettingsException(Exception):
    def __init__(self, message):
        self.message = message

def settings_parse_copy_from(copy_from, path=None):
    logger.debug("Going to parse the copy_from setting.")

    # Check if we already get a list:
    if not isinstance(copy_from, list):
        copy_from = copy_from.split(" ")

    tmp = []
    for file in copy_from:
        file = file.strip()
        # If file is empty we do not want to add it to the list
        if not file == "":
            # If we get an absolut path we do nothing
            # If not we add self.path to get an absolut path
            if not os.path.isabs(file):
                if path:
                    file = os.path.normpath(path + "/" + file)
                else:
                    file = os.path.abspath(file)

            logger.debug("Checking if '{}' is a valid file or dir".format(file))
            # We need to check if file is a valid file or dir
            if not (os.path.isdir(file) or os.path.isfile(file)):
                raise SettingsException("'{}' is not a valid file nor a valid directory".format(file))

            logger.debug("'{}' will be copied into all images".format(file))
            tmp.append(file)

    return tmp

class CommonSettings():
    def __init__(self, priority_list=[]):
        if "cache" in priority_list:
            raise SettingsException("Cache is reserved and so an invalid type")

        self.priority_list = ["cache"] + priority_list

        self._settings = {}

    def set_config_value(self, key, value, type=None):
        self.check_type(type)

        # Add value to the dict
        self._settings[type].setdefault(key, value)
        logger.debug("Added key '{}' with value '{}' of type {} to settings".format(key, value, type))

        # If this key is in the cache and type is not "cache" we need to refresh the cache
        if "cache" in self._settings and type != "cache":
            if key in self._settings["cache"]:
                logger.debug("Removing key '{}' of cache because of new value".format(key))
                self._settings["cache"].pop(key)

    def get_config_value(self, key):
        # loop through the priority list and try to find the config value

        for type in self.priority_list:
            if type in self._settings:
                if key in self._settings[type]:
                    logger.debug("Found key '{}' in '{}'".format(key, type))
                    value = self._settings[type].get(key)
                    break

        # Update cache:
        if type != "cache":
            self.set_config_value(key, value, type="cache")

        return value

    # checks if a type passed to a set_* function is valid
    def check_type(self, type):
        if type == None:
            raise SettingsException("Type for a new config value cannot be None")

        if type not in self.priority_list:
            raise SettingsException("Type {} is not a valid type".format(type))

        # Add a new type to the settings dict
        if type not in self._settings:
            self._settings.setdefault(type, {})

# A settings class with some nitsi defaults
class NitsiSettings(CommonSettings):
    def __init__(self, priority_list=[]):
        super().__init__(priority_list)

        # Set default settings
        self.set_config_value("name", "", type="nitsi-default")
        self.set_config_value("description", "", type="nitsi-default")
        self.set_config_value("copy_from", None, type="nitsi-default")
        self.set_config_value("copy_to", None, type="nitsi-default")
        self.set_config_value("virtual_environ_path", None, type="nitsi-default")
        self.set_config_value("interactive_error_handling", False, type="nitsi-default")

    def set_config_values_from_file(self, file, type):
        self.check_type(type)

        logger.debug("Path of settings file is: {}".format(file))
        # Check that file is an valid file
        if not os.path.isfile(file):
            raise SettingsException("No such file: {}".format(file))

        # Check that we are use an absolut path
        if not os.path.isabs(file):
            file = os.path.abspath(file)

        try:
            config = configparser.ConfigParser()
            config.read(file)
        except BaseException as e:
            raise e

        if "GENERAL" in config:
            for key in ["name", "description", "copy_to", "copy_from"]:
                if key in config["GENERAL"]:
                    # Handle the copy from setting in a special way
                    if key == "copy_from":
                        self.set_config_value(key, settings_parse_copy_from(config["GENERAL"][key], path=os.path.dirname(file)), type=type)
                    else:
                        self.set_config_value(key, config["GENERAL"][key], type=type)


        if "VIRTUAL_ENVIRONMENT" in config:
            if "path" in config["VIRTUAL_ENVIRONMENT"]:
                path = config["VIRTUAL_ENVIRONMENT"]["path"]
                if not os.path.isabs(path):
                    path  = os.path.normpath(os.path.dirname(file) + "/" + path)
                self.set_config_value("virtual_environ_path", path, type=type)


    def check_config_values(self):
        # Check if we get at least a valid a valid path to virtual environ
        if not os.path.isdir(self.get_config_value("virtual_environ_path")):
            raise SettingsException("No path for virtual environment found.")
