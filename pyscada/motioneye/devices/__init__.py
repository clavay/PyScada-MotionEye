# -*- coding: utf-8 -*-

# from https://github.com/home-assistant/core/tree/dev/homeassistant/components/motioneye
from __future__ import unicode_literals
from .. import PROTOCOL_ID
from pyscada.models import DeviceProtocol, VariableProperty
from pyscada.device import GenericHandlerDevice

import traceback
import re
from time import time
import json
from typing import Any

from asgiref.sync import async_to_sync
from async_timeout import timeout
from asyncio import wait_for

try:
    from asyncio.exceptions import TimeoutError as asyncioTimeoutError
    from asyncio.exceptions import CancelledError as asyncioCancelledError
except ModuleNotFoundError:
    # for python version < 3.8
    from asyncio import TimeoutError as asyncioTimeoutError
    from asyncio import CancelledError as asyncioCancelledError

import logging

logger = logging.getLogger(__name__)

try:
    from motioneye_client.client import *

    driver_ok = True
except ImportError:
    logger.error("Cannot import motioneye_client")
    driver_ok = False


async def async_set_cameras_config(device, conf):
    try:
        url = device.motioneye_server.url
        admin_username = device.motioneye_server.admin_username
        admin_password = device.motioneye_server.admin_password
        surveillance_username = device.motioneye_server.surveillance_username
        surveillance_password = device.motioneye_server.surveillance_password
        async with MotionEyeClient(
            url,
            admin_username,
            admin_password,
            surveillance_username,
            surveillance_password,
        ) as client:
            try:
                await wait_for(
                    client.async_set_camera(device.camera_id, conf), timeout=5
                )
            except (TimeoutError, asyncioTimeoutError):
                logger.warning("Timeout for {}.".format(device))
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
        async with MotionEyeClient(
            url,
            admin_username,
            admin_password,
            surveillance_username,
            surveillance_password,
        ) as client:
            try:
                await wait_for(client.async_action(camera_id, action), timeout=5)
            except (TimeoutError, asyncioTimeoutError):
                logger.warning("Timeout for {}.".format(device))
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


class GenericDevice(GenericHandlerDevice):
    def __init__(self, pyscada_device, variables):
        super().__init__(pyscada_device, variables)
        self._protocol = PROTOCOL_ID
        self.driver_ok = driver_ok
        self.camera_config = None
        self.last_value = None

    def connect(self):
        """
        establish a connection to the Instrument
        """
        super().connect()

        async_to_sync(self.async_get_cameras_config)()

        self.accessibility()
        return True

    def read_data(self, variable_instance):
        """
        read values from the device
        """
        value = None
        if (
            self.camera_config is not None
            and variable_instance.motioneyevariable.service in self.camera_config
        ):
            value = self.camera_config[variable_instance.motioneyevariable.service]
        return value

    def write_data(self, variable_id, value, task):
        """
        write values to the device
        """
        if self.connect():
            for var in self._variables:
                var = self._variables[var]
                if variable_id == var.id:
                    if (
                        self.camera_config is not None
                        and var.motioneyevariable.service in self.camera_config
                    ):
                        # Config
                        if var.value_class == "BOOLEAN":
                            value = str(bool(value))
                        else:
                            for field in var.motioneyevariable.service_not_boolean:
                                if re.compile(field, re.IGNORECASE).match(
                                    var.motioneyevariable.service
                                ):
                                    # if field in var.motioneyevariable.service:
                                    value = str(
                                        var.motioneyevariable.service_not_boolean[
                                            field
                                        ][int(value)][0]
                                    )

                                # for custom text overlay
                                if int(value) == 2:
                                    if "left" in var.motioneyevariable.service:
                                        try:
                                            self.camera_config[
                                                "custom_"
                                                + var.motioneyevariable.service
                                            ] = str(
                                                var.variableproperty_set.get(
                                                    name="text"
                                                ).value()
                                            )
                                        except VariableProperty.DoesNotExist:
                                            logger.warning(
                                                "VariableProperty named text does not exist "
                                                "for custom text overlay var id {}".format(
                                                    var.id
                                                )
                                            )

                        self.camera_config[var.motioneyevariable.service] = value

                        async_to_sync(async_set_cameras_config)(
                            var.device.motioneyedevice, self.camera_config
                        )

                        return value
                    else:
                        # Actions
                        for action in var.motioneyevariable.service_actions_choices:
                            if var.motioneyevariable.service == action[0]:
                                value = async_to_sync(async_do_action)(
                                    var.device.motioneyedevice,
                                    var.device.motioneyedevice.camera_id,
                                    str(action[0]),
                                )
                                return value

                        logger.info(
                            "write {} failed for {}".format(
                                var.motioneyevariable.service, var.device
                            )
                        )
                        return None

            logger.warning(
                "Variable {} not in variable list {} of device {}".format(
                    variable_id, self._variables, self._device
                )
            )
        return None

    async def async_get_cameras_config(self):
        # Refresh cameras configurations
        self.inst = None
        self.camera_config = None
        try:
            self.inst = await self.async_query_motioneye_server()
            if (
                type(self.inst) == dict
                and "cameras" in self.inst
                and type(self.inst["cameras"]) == dict
                and "cameras" in self.inst["cameras"]
            ):
                for camera in self.inst["cameras"]["cameras"]:
                    if camera["id"] == self._device.motioneyedevice.camera_id:
                        self.camera_config = camera
        except (TimeoutError, asyncioTimeoutError):
            self._not_accessible_reason = "Timeout"
        except Exception as e:
            self._not_accessible_reason = e
            # logger.warning(traceback.format_exc())

    async def async_query_motioneye_server(self) -> dict[str, Any] or None:
        try:
            url = self._device.motioneyedevice.motioneye_server.url
            admin_username = (
                self._device.motioneyedevice.motioneye_server.admin_username
            )
            admin_password = (
                self._device.motioneyedevice.motioneye_server.admin_password
            )
            surveillance_username = (
                self._device.motioneyedevice.motioneye_server.surveillance_username
            )
            surveillance_password = (
                self._device.motioneyedevice.motioneye_server.surveillance_password
            )
            async with timeout(10) as tm:
                client = MotionEyeClient(
                    url,
                    admin_username,
                    admin_password,
                    surveillance_username,
                    surveillance_password,
                )
                try:
                    if not client:
                        self._not_accessible_reason = f"MotionEyeClient is {client}"
                        return None
                    resp = dict()

                    await client.async_client_login()

                    manifest = await client.async_get_manifest()
                    server_config = await client.async_get_server_config()
                    cameras = await client.async_get_cameras()

                    resp["manifest"] = manifest
                    resp["server_config"] = server_config
                    resp["cameras"] = cameras

                    return resp

                except asyncioCancelledError:
                    self._not_accessible_reason = "Timeout"
                finally:
                    await client.async_client_close()

        except MotionEyeClientInvalidAuthError:
            self._not_accessible_reason = (
                f"Invalid motionEye authentication for {self._device.motioneyedevice}."
            )
        except MotionEyeClientConnectionError:
            self._not_accessible_reason = (
                f"MotionEye connection failure for {self._device.motioneyedevice}."
            )
        except MotionEyeClientRequestError:
            self._not_accessible_reason = (
                f"MotionEye request failure for {self._device.motioneyedevice}."
            )
        except MotionEyeClientURLParseError:
            self._not_accessible_reason = (
                f"Unable to parse the URL for {self._device.motioneyedevice}."
            )
        except MotionEyeClientPathError:
            self._not_accessible_reason = (
                f"Invalid path provided for {self._device.motioneyedevice}."
            )
        return None
