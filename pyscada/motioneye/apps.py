# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

import config


class PyScadaMotionEyeConfig(AppConfig):
    name = 'pyscada.' + config.plugin_name_lower
    verbose_name = _("PyScada " + config.plugin_name)
    path = os.path.dirname(os.path.realpath(__file__))
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import signals
