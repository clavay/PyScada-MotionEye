# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyscada.models import Device, Variable
from .models import MotionEyeServer, MotionEyeDevice, MotionEyeVariable, ExtendedMotionEyeDevice, \
    ExtendedMotionEyeVariable

from django.dispatch import receiver
from django.db.models.signals import post_save

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MotionEyeServer)
@receiver(post_save, sender=MotionEyeDevice)
@receiver(post_save, sender=MotionEyeVariable)
@receiver(post_save, sender=ExtendedMotionEyeDevice)
@receiver(post_save, sender=ExtendedMotionEyeVariable)
def _reinit_daq_daemons(sender, instance, **kwargs):
    """
    update the daq daemon configuration when changes be applied in the models
    """
    if type(instance) is MotionEyeDevice:
        post_save.send_robust(sender=Device, instance=instance.motioneye_device)
    elif type(instance) is MotionEyeServer:
        for camera in instance.motioneyedevice_set.all():
            post_save.send_robust(sender=Device, instance=camera.motioneye_device)
    elif type(instance) is MotionEyeVariable:
        post_save.send_robust(sender=Variable, instance=instance.motioneye_variable)
    elif type(instance) is ExtendedMotionEyeVariable:
        post_save.send_robust(sender=Variable, instance=Variable.objects.get(pk=instance.pk))
    elif type(instance) is ExtendedMotionEyeDevice:
        post_save.send_robust(sender=Device, instance=Device.objects.get(pk=instance.pk))
