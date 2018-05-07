#!/usr/bin/python3

import logging
import os
import time

logger = logging.getLogger("nitsi.logger")

class Logger_Exeception(BaseException):
    pass

# This function should create the necessary folders
# and touch the logging files
def init_logging(path):
    logger.debug("Init logging directory")
    if not os.path.isdir(path):
        logger.error("{} is not a valid directory".format(path))

    try:
        path = os.path.abspath(path)
    except BaseException as e:
        logger.error("Failed to get the absolute path for: {}".format(path))

    log_dir = "{}/log".format(path)

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    time_dir = log_dir + "/" + time.strftime("%Y-%m-%d_%H-%M-%S" ,time.gmtime(time.time()))

    if os.path.exists(time_dir):
        logger.error("Path {} alreday exist".format(time_dir))
        raise Logger_Exeception
    else:
        os.mkdir(time_dir)

    return time_dir
