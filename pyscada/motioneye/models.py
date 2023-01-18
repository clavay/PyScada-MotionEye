# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyscada.models import Device
from pyscada.models import Variable
from . import PROTOCOL_ID

from django.db import models
import logging

logger = logging.getLogger(__name__)


class MotionEyeServer(models.Model):
    url = models.URLField(blank=False, help_text="MotionEye server URL")
    admin_username = models.CharField(default='admin', max_length=50)
    admin_password = models.CharField(default='', max_length=50)
    surveillance_username = models.CharField(default='user', max_length=50)
    surveillance_password = models.CharField(default='', max_length=50)

    def __str__(self):
        return str(self.url)


class MotionEyeDevice(models.Model):
    motioneye_device = models.OneToOneField(Device, null=True, blank=True, on_delete=models.CASCADE)
    motioneye_server = models.ForeignKey(MotionEyeServer, null=True, blank=True, on_delete=models.CASCADE)
    camera_id = models.PositiveSmallIntegerField(default=0, help_text="Camera ID in the MotionEye server")

    protocol_id = PROTOCOL_ID

    def parent_device(self):
        try:
            return self.motioneye_device
        except:
            return None

    def __str__(self):
        return self.motioneye_device.short_name


class MotionEyeVariable(models.Model):
    motioneye_variable = models.OneToOneField(Variable, null=True, blank=True, on_delete=models.CASCADE)
    service_choices = (('snapshot', 'snapshot'),
                           ('lock', 'lock'),
                           ('unlock', 'unlock'),
                           ('light_on', 'light_on'),
                           ('light_off', 'light_off'),
                           ('alarm_on', 'alarm_on'),
                           ('alarm_off', 'alarm_off'),
                           ('up', 'up'),
                           ('right', 'right'),
                           ('down', 'down'),
                           ('left', 'left'),
                           ('zoom_in', 'zoom_in'),
                           ('zoom_out', 'zoom_out'),
                           ('preset1', 'preset1'),
                           ('preset2', 'preset2'),
                           ('preset3', 'preset3'),
                           ('preset4', 'preset4'),
                           ('preset5', 'preset5'),
                           ('preset6', 'preset6'),
                           ('preset7', 'preset7'),
                           ('preset8', 'preset8'),
                           ('preset9', 'preset9'),
                           ('record_start', 'record_start'),
                           ('record_stop', 'record_stop'),
                           ('set_text_overlay', 'set_text_overlay'),)
    service = models.PositiveSmallIntegerField(default='snapshot', max_length=50, choices=service_choices,
                                       help_text='Action to send or text overlay to write over the image/video')
    text_overlay_choices = (('timestamp', 'timestamp'),
                           ('camera-name', 'camera-name'),
                           ('custom-text', 'custom-text'),
                           ('disabled', 'disabled'),)
    text_overlay = models.PositiveSmallIntegerField(default='camera-name', max_length=50, choices=text_overlay_choices,
                                       help_text='Used only if service is text overlay')
    text_overlay_side_choices = (('left', 'left'),
                           ('right', 'right'),)
    text_overlay_side = models.PositiveSmallIntegerField(default='left', max_length=50, choices=text_overlay_side_choices,
                                       help_text='Used only if service is text overlay')


    protocol_id = PROTOCOL_ID

    def __str__(self):
        return self.id.__str__() + "-" + self.motioneye_variable.short_name

    def save(self, *args, **kwargs):
        self.motioneye_variable.value_class = 'BOOLEAN'
        super().save(*args, **kwargs)


class ExtendedMotionEyeDevice(Device):
    class Meta:
        proxy = True
        verbose_name = 'MotionEye Device'
        verbose_name_plural = 'MotionEye Devices'


class ExtendedMotionEyeVariable(Variable):
    class Meta:
        proxy = True
        verbose_name = 'MotionEye Variable'
        verbose_name_plural = 'MotionEye Variables'
