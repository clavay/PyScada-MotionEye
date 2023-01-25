# -*- coding: utf-8 -*-

# from https://github.com/home-assistant/core/tree/dev/homeassistant/components/motioneye
from __future__ import unicode_literals
from .. import PROTOCOL_ID
from pyscada.models import DeviceProtocol, VariableProperty

import traceback
import re
from time import time
import json
from typing import Any

from asgiref.sync import async_to_sync

import logging

logger = logging.getLogger(__name__)

try:
    from motioneye_client.client import *
    driver_ok = True
except ImportError:
    logger.error("Cannot import motioneye_client")
    driver_ok = False


async def async_query_motioneye_server(device) -> dict[str, Any] or None:
    try:
        url = device.motioneye_server.url
        admin_username = device.motioneye_server.admin_username
        admin_password = device.motioneye_server.admin_password
        surveillance_username = device.motioneye_server.surveillance_username
        surveillance_password = device.motioneye_server.surveillance_password
        async with MotionEyeClient(url, admin_username, admin_password, surveillance_username, surveillance_password) as client:
            if not client:
                return None

            await client.async_client_login()
            manifest = await client.async_get_manifest()
            server_config = await client.async_get_server_config()
            cameras = await client.async_get_cameras()

            resp = dict()
            resp['manifest'] = manifest
            resp['server_config'] = server_config
            resp['cameras'] = cameras

            #logger.debug(json.dumps(resp, indent=5))
            return resp
    except MotionEyeClientInvalidAuthError:
        logger.warning("Invalid motionEye authentication for {}.".format(device))
    except MotionEyeClientConnectionError:
        logger.warning("MotionEye connection failure for {}.".format(device))
    except MotionEyeClientRequestError:
        logger.warning("MotionEye request failure for {}.".format(device))
    except MotionEyeClientURLParseError:
        logger.warning("Unable to parse the URL for {}.".format(device))
    except MotionEyeClientPathError:
        logger.warning("Invalid path provided for {}.".format(device))
    return None


async def async_get_cameras_config(device):
    # Refresh cameras configurations
    inst = None
    camera_config = None
    try:
        inst = await async_query_motioneye_server(device.motioneyedevice)
        if type(inst) == dict and 'cameras' in inst and type(inst['cameras']) == dict and 'cameras' in inst['cameras']:
            for camera in inst['cameras']['cameras']:
                if camera['id'] == device.motioneyedevice.camera_id:
                    camera_config = camera
    except Exception as e:
        logger.warning(e)
        logger.warning(traceback.format_exc())
    return inst, camera_config


async def async_set_cameras_config(device, conf):
    try:
        url = device.motioneye_server.url
        admin_username = device.motioneye_server.admin_username
        admin_password = device.motioneye_server.admin_password
        surveillance_username = device.motioneye_server.surveillance_username
        surveillance_password = device.motioneye_server.surveillance_password
        async with MotionEyeClient(url, admin_username, admin_password, surveillance_username, surveillance_password) as client:
            await client.async_set_camera(device.camera_id, conf)
    except MotionEyeClientInvalidAuthError:
        logger.warning("Invalid motionEye authentication for {}.".format(device))
    except MotionEyeClientConnectionError:
        logger.warning("MotionEye connection failure for {}.".format(device))
    except MotionEyeClientRequestError:
        logger.warning("MotionEye request failure for {}.".format(device))
    except MotionEyeClientURLParseError:
        logger.warning("Unable to parse the URL for {}.".format(device))
    except MotionEyeClientPathError:
        logger.warning("Invalid path provided for {}.".format(device))
    return None


async def async_do_action(device, camera_id, action):
    try:
        url = device.motioneye_server.url
        admin_username = device.motioneye_server.admin_username
        admin_password = device.motioneye_server.admin_password
        surveillance_username = device.motioneye_server.surveillance_username
        surveillance_password = device.motioneye_server.surveillance_password
        async with MotionEyeClient(url, admin_username, admin_password, surveillance_username, surveillance_password) as client:
            await client.async_action(camera_id, action)

        # Set the action variable to False to be settable again
        return False
    except MotionEyeClientInvalidAuthError:
        logger.warning("Invalid motionEye authentication for {}.".format(device))
    except MotionEyeClientConnectionError:
        logger.warning("MotionEye connection failure for {}.".format(device))
    except MotionEyeClientRequestError as e:
        logger.warning("MotionEye request failure for {} : {}".format(device, e))
    except MotionEyeClientURLParseError:
        logger.warning("Unable to parse the URL for {}.".format(device))
    except MotionEyeClientPathError:
        logger.warning("Invalid path provided for {}.".format(device))
    return None


class GenericDevice:
    def __init__(self, pyscada_device, variables):
        self._device = pyscada_device
        self._variables = variables
        self.inst = None
        self.camera_config = None
        self.last_value = None
        self._device_not_accessible = 0

    def connect(self):
        """
        establish a connection to the Instrument
        """
        if not driver_ok:
            return False

        if self._device.protocol.id != PROTOCOL_ID:
            logger.error("Wrong handler selected : it's for %s device while device protocol is %s" %
                         (str(DeviceProtocol.objects.get(id=PROTOCOL_ID)).upper(),
                          str(self._device.protocol).upper()))
            return False

        self.inst, self.camera_config = async_to_sync(async_get_cameras_config)(self._device)

        if self.inst is not None:
            if self._device_not_accessible < 1:
                self._device_not_accessible = 1
                logger.info('Connected to MotionEye device : {}'.format(self._device))
        else:
            if self._device_not_accessible > -1:
                self._device_not_accessible = -1
                logger.info('MotionEye device {} is not accessible'.format(self._device))
        return True

    def disconnect(self):
        if self.inst is not None:
            self.inst = None
            return True
        return False

    def before_read(self):
        """
        will be called before the first read_data
        """
        return None

    def after_read(self):
        """
        will be called after the last read_data
        """
        return None

    def read_data(self, variable_instance):
        """
        read values from the device
        """
        value = None
        if self.camera_config is not None and variable_instance.motioneyevariable.service in self.camera_config:
            value = self.camera_config[variable_instance.motioneyevariable.service]
        return value

    def read_data_and_time(self, variable_instance):
        """
        read values and timestamps from the device
        """

        return self.read_data(variable_instance), self.time()

    def read_data_all(self, variables_dict):
        output = []

        if self.connect():
            for item in variables_dict.values():
                value, read_time = self.read_data_and_time(item)

                if value is not None and item.update_value(value, read_time):
                    output.append(item.create_recorded_data_element())
        return output

    def write_data(self, variable_id, value, task):
        """
        write values to the device
        """
        if self.connect():
            for var in self._variables:
                var = self._variables[var]
                if variable_id == var.id:
                    if self.camera_config is not None and var.motioneyevariable.service in self.camera_config:
                        # Config
                        if var.value_class == 'BOOLEAN':
                            value = str(bool(value))
                        else:
                            for field in var.motioneyevariable.service_not_boolean:
                                if re.compile(field, re.IGNORECASE).match(var.motioneyevariable.service):
                                #if field in var.motioneyevariable.service:
                                    value = str(var.motioneyevariable.service_not_boolean[field][int(value)][0])

                                # for custom text overlay
                                if int(value) == 2:
                                    if 'left' in var.motioneyevariable.service:
                                        try:
                                            self.camera_config['custom_' + var.motioneyevariable.service] = str(var.variableproperty_set.get(name='text').value())
                                        except VariableProperty.DoesNotExist:
                                            logger.warning('VariableProperty named text does not exist '
                                                           'for custom text overlay var id {}'.format(var.id))

                        self.camera_config[var.motioneyevariable.service] = value

                        async_to_sync(async_set_cameras_config)(var.device.motioneyedevice, self.camera_config)


                        return value
                    else:
                        # Actions
                        for action in var.motioneyevariable.service_actions_choices:
                            if var.motioneyevariable.service == action[0]:
                                value = async_to_sync(async_do_action)(var.device.motioneyedevice, var.device.motioneyedevice.camera_id, str(action[0]))
                                return value

                        logger.info('write {} failed for {}'.format(var.motioneyevariable.service, var.device))
                        return None

            logger.warning('Variable {} not in variable list {} of device {}'.format(variable_id, self._variables, self._device))
        return None

    def time(self):
        return time()
