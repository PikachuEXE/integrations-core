# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os
from collections import OrderedDict
from copy import deepcopy

import toml
from appdirs import user_data_dir
from atomicwrites import atomic_write

from ..utils import ensure_parent_dir_exists, file_exists, read_file

APP_DIR = user_data_dir('dd-checks-dev', '')
CONFIG_FILE = os.path.join(APP_DIR, 'config.toml')

DEFAULT_CONFIG = OrderedDict([
    ('core', os.path.expanduser(os.path.join('~', 'dd', 'integrations-core'))),
    ('extras', os.path.expanduser(os.path.join('~', 'dd', 'integrations-extras'))),
])


def config_file_exists():
    return file_exists(CONFIG_FILE)


def copy_default_config():
    return deepcopy(DEFAULT_CONFIG)


def load_config():
    config = copy_default_config()

    try:
        config.update(toml.loads(read_file(CONFIG_FILE), OrderedDict))
    except FileNotFoundError:
        pass

    return config


def save_config(config):
    ensure_parent_dir_exists(CONFIG_FILE)
    with atomic_write(CONFIG_FILE, mode='wb', overwrite=True) as f:
        f.write(toml.dumps(config).encode('utf-8'))


def restore_config():
    config = copy_default_config()
    save_config(config)
    return config


def update_config():
    config = copy_default_config()
    config.update(load_config())
    save_config(config)
    return config
