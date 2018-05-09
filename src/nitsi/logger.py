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


class TestFormatter(logging.Formatter):
    def __init__(self, start_time=None, name=None):
        super().__init__(fmt="[%(asctime)s] %(message)s")
        logger.debug("Initiating TestFormatter for")
        if start_time == None:
            self.starttime = time.time()
        else:
            self.starttime = start_time

        if name == None:
            self.name = ""
        else:
            self.name = name

    def converter(self, recordtime):

        # This returns a timestamp relatively to the time when we started
        # the test.

        recordtime -= self.starttime

        return time.gmtime(recordtime)

    def format(self, record):
        return "[{}][{}] {}".format(self.formatTime(record), self.name, record.getMessage())

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        t = time.strftime("%H:%M:%S", ct)
        s = "{}.{:03d}".format(t, round(record.msecs,None))
        return s
