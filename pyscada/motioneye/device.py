# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from time import time, sleep
from devices import GenericDevice

import sys

import logging
logger = logging.getLogger(__name__)

try:
    from motioneye_client.client import MotionEyeClient
    driver_ok = True
except ImportError:
    logger.error('Cannot import motioneye_client')
    driver_ok = False


class Device:
    """
    MotionEye device
    """

    def __init__(self, device):
        self.variables = {}
        self.device = device
        try:
            if self.device.motioneyedevice.instrument_handler is not None \
                    and self.device.motioneyedevice.instrument_handler.handler_path is not None:
                sys.path.append(self.device.motioneyedevice.instrument_handler.handler_path)
                mod = __import__(self.device.motioneyedevice.instrument_handler.handler_class, fromlist=['Handler'])
                device_handler = getattr(mod, 'Handler')
                self._h = device_handler(self.device, self.variables)
            else:
                self._h = GenericDevice(self.device, self.variables)
            self.driver_handler_ok = True
        except ImportError:
            self.driver_handler_ok = False
            logger.error("Handler import error : %s" % self.device.short_name)

        for var in self.device.variable_set.filter(active=1):
            if not hasattr(var, 'motioneyevariable'):
                continue
            self.variables[var.pk] = var

        if driver_ok and self.driver_handler_ok:
            logger.error("motioneye connect")
            if not self._h.connect():
                sleep(60)
                self._h.connect()

    def request_data(self):

        output = []

        if not driver_ok or not self.driver_handler_ok:
            return output
        if driver_ok and self.driver_handler_ok and self._h.inst is None:
            self._h.connect()

        for item in self.variables.values():
            value = self._h.read_data(item)

            if value is not None and item.update_value(value, time()):
                output.append(item.create_recorded_data_element())

        return output

    def write_data(self, variable_id, value, task):
        """
        write value to a Serial Device
        """

        output = []
        if not driver_ok or not self.driver_handler_ok:
            return output
        if driver_ok and self.driver_handler_ok and self._h.inst is None:
            self._h.connect()
            
        for item in self.variables:
            if self.variables[item].id == variable_id:
                if not self.variables[item].writeable:
                    return False
                read_value = self._h.write_data(variable_id, value, task)
                if read_value is not None and self.variables[item].update_value(read_value, time()):
                    output.append(self.variables[item].create_recorded_data_element())

        return output
