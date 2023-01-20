# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pyscada
from . import config

__version__ = '0.7.1rc1'
__author__ = 'Camille Lavayssière'

PROTOCOL_ID = 92

parent_process_list = [{'pk': PROTOCOL_ID,
                        'label': 'pyscada.' + config.plugin_name_lower,
                        'process_class': 'pyscada.' + config.plugin_name_lower + '.worker.Process',
                        'process_class_kwargs': '{"dt_set":30}',
                        'enabled': True}]
