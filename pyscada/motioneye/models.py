# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyscada.models import Device
from pyscada.models import Variable
from pyscada.models import VariableProperty
from pyscada.models import Dictionary
from . import PROTOCOL_ID

from django.db import models
from django.core.exceptions import ValidationError

import re
import logging

logger = logging.getLogger(__name__)


class MotionEyeServer(models.Model):
    url = models.URLField(blank=False, help_text="MotionEye server URL", unique=True)
    admin_username = models.CharField(default='admin', max_length=50)
    admin_password = models.CharField(default='', max_length=50, blank=True)
    surveillance_username = models.CharField(default='user', max_length=50)
    surveillance_password = models.CharField(default='', max_length=50, blank=True)

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
    service_actions_choices = (('snapshot', 'Snapshot'),
                               ('lock', 'Lock'),
                               ('unlock', 'Unlock'),
                               ('light_on', 'Light on'),
                               ('light_off', 'Light off'),
                               ('alarm_on', 'Alarm on'),
                               ('alarm_off', 'Alarm off'),
                               ('up', 'Up'),
                               ('right', 'Right'),
                               ('down', 'Down'),
                               ('left', 'Left'),
                               ('zoom_in', 'Zoom in'),
                               ('zoom_out', 'Zoom out'),
                               ('preset1', 'Preset1'),
                               ('preset2', 'Preset2'),
                               ('preset3', 'Preset3'),
                               ('preset4', 'Preset4'),
                               ('preset5', 'Preset5'),
                               ('preset6', 'Preset6'),
                               ('preset7', 'Preset7'),
                               ('preset8', 'Preset8'),
                               ('preset9', 'Preset9'),
                               ('record_start', 'Record start'),
                               ('record_stop', 'Record stop'),
                               ('eventstart', 'Event start'),
                               ('eventend', 'Event stop'),
                               )

    service_other_choices = (
                       # Text overlay : 'timestamp', 'camera-name', 'custom-text', 'disabled'
                       ('left_text', 'Left text overlay'),
                       ('right_text', 'Right text overlay'),

                       ('movies', 'Movie state'),
                       ('enabled', 'Device state'),
                       ('recording_mode', 'Recording mode'),  # 'motion-triggered', 'continuous'
                       )

    service_choices = service_actions_choices + service_other_choices

    service = models.CharField(default='snapshot', choices=service_choices, max_length=50,
                               help_text='Action to send or text overlay to write over the image/video')

    protocol_id = PROTOCOL_ID

    # increment this list
    service_not_boolean = {'boolean': {0: ['False', 'False'],
                                       1: ['True', 'True']},
                           '(left|right)_text': {2: ['timestamp', 'Timestamp'],
                                                 3: ['camera-name', 'Camera name'],
                                                 # use variable property to store custom text
                                                 4: ['custom-text', 'Custom text'],
                                                 5: ['disabled', 'Disabled'],
                                                 },
                           'recording_mode': {6: ['motion-triggered', 'Motion triggered'],
                                              7: ['continuous', 'Continuous'],
                                              }
                           }

    def __str__(self):
        return self.id.__str__() + "-" + self.motioneye_variable.short_name

    def save(self, *args, **kwargs):
        self.motioneye_variable.value_class = 'BOOLEAN'
        self.motioneye_variable.writeable = True

        d = None
        for field in self.service_not_boolean:
            if re.compile(field, re.IGNORECASE).match(self.service):
            #if field in self.service:
                d, created = Dictionary.objects.get_or_create(name='MotionEye_non_boolean_services')
                for i in self.service_not_boolean[field]:
                    d.append(self.service_not_boolean[field][i][1], i, True)

        if d is not None:
            self.motioneye_variable.value_class = 'INT16'
        else:
            d, created = Dictionary.objects.get_or_create(name='MotionEye_non_boolean_services')
            field = 'boolean'
            for i in self.service_not_boolean[field]:
                d.append(self.service_not_boolean[field][i][1], i, True)

        self.motioneye_variable.dictionary = d
        super().save(*args, **kwargs)
        self.motioneye_variable.save()

        # Create variable property for custom text overlay
        if 'text_overlay' in self.service:
            VariableProperty(variable=self,
                             property_class=None,
                             value_class='STRING',
                             name='custom-text')

    def validate_unique(self, exclude=None):
        qs = MotionEyeVariable.objects.filter(service=self.service,
                                              motioneye_variable__device=self.motioneye_variable.device,
                                              ).exclude(id=self.id)
        if len(qs):
            raise ValidationError('This service already exist for this device.')
        super().validate_unique(exclude=exclude)


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
