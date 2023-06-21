# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pyscada.device import GenericDevice
from .devices import GenericDevice as GenericHandlerDevice

from time import time

import logging

logger = logging.getLogger(__name__)

try:
    from motioneye_client.client import MotionEyeClient

    driver_ok = True
except ImportError:
    logger.error("Cannot import motioneye_client", exc_info=True)
    driver_ok = False


class Device(GenericDevice):
    """
    MotionEye device
    """

    def __init__(self, device):
        self.driver_ok = driver_ok
        self.handler_class = GenericHandlerDevice
        super().__init__(device)

        for var in self.device.variable_set.filter(active=1):
            if not hasattr(var, "motioneyevariable"):
                continue
            self.variables[var.pk] = var
