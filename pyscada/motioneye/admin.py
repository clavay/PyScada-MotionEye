# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import PROTOCOL_ID
from models import MotionEyeDevice, ExtendedMotionEyeDevice
from models import MotionEyeVariable, ExtendedMotionEyeVariable
from pyscada.admin import DeviceAdmin
from pyscada.admin import VariableAdmin
from pyscada.admin import admin_site
from pyscada.models import Device, DeviceProtocol
from django.contrib import admin
import logging

logger = logging.getLogger(__name__)


class MotionEyeAdminInline(admin.StackedInline):
    model = MotionEyeDevice


class MotionEyeDeviceAdmin(DeviceAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'protocol':
            kwargs['queryset'] = DeviceProtocol.objects.filter(pk=PROTOCOL_ID)
            db_field.default = PROTOCOL_ID
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        """Limit Pages to those that belong to the request's user."""
        qs = super().get_queryset(request)
        return qs.filter(protocol_id=PROTOCOL_ID)

    inlines = [
        MotionEyeDeviceAdminInline
    ]


class MotionEyeVariableAdminInline(admin.StackedInline):
    model = MotionEyeVariable


class MotionEyeVariableAdmin(VariableAdmin):
    list_display = ('id', 'name', 'description', 'unit', 'device_name', 'value_class', 'active', 'writeable')
    list_editable = ('active', 'writeable',)
    list_display_links = ('name',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'device':
            kwargs['queryset'] = Device.objects.filter(protocol=PROTOCOL_ID)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        """Limit Pages to those that belong to the request's user."""
        qs = super().get_queryset(request)
        return qs.filter(device__protocol_id=PROTOCOL_ID)

    inlines = [
        MotionEyeVariableAdminInline
    ]


# admin_site.register(ExtendedMotionEyeDevice, MotionEyeDeviceAdmin)
# admin_site.register(ExtendedMotionEyeVariable, MotionEyeVariableAdmin)
