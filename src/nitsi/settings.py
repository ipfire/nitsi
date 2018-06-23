#!/usr/bin/python3

import logging
import os

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