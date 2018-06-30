# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import click
import toml

from .utils import CONTEXT_SETTINGS, echo_info, echo_success
from ..config import CONFIG_FILE, restore_config, save_config, update_config
from ..utils import string_to_toml_type


@click.group(
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
    short_help='Locates, updates, or restores the config file'
)
@click.option(
    '--update', '-u',
    is_flag=True,
    help='Updates the config file with any new fields.'
)
@click.option(
    '--restore',
    is_flag=True,
    help='Restores the config file to default settings.'
)
@click.pass_context
def config(ctx, update, restore):
    """Locates, updates, or restores the config file.

    \b
    $ ddev config
    /home/ofek/.local/share/dd-checks-dev/config.toml
    """
    if update:
        user_config = update_config()
        ctx.obj = user_config
        echo_success('Settings were successfully updated.')

    if restore:
        user_config = restore_config()
        ctx.obj = user_config
        echo_success('Settings were successfully restored.')

    if not ctx.invoked_subcommand:
        if update or restore:
            echo_info('Settings location: `{}`'.format(CONFIG_FILE))
        else:
            echo_info('"{}"'.format(CONFIG_FILE))


@config.command(
    'set',
    context_settings=CONTEXT_SETTINGS,
    short_help='Assigns values to config file entries'
)
@click.argument('key')
@click.argument('value')
@click.pass_context
def set_value(ctx, key, value):
    """Assigns values to config file entries.

    \b
    $ ddev config set foo.bar value
    New setting:
    [foo]
    bar = "value"
    """
    user_config = ctx.obj

    updated_config = {}
    new_config = updated_config
    data = [value]
    data.extend(reversed(key.split('.')))
    key = data.pop()
    value = data.pop()

    # Consider dots as keys
    while data:
        new_config[key] = {value: ''}
        new_config = new_config[key]
        key = value
        value = data.pop()
    new_config[key] = string_to_toml_type(value)

    user_config.update(updated_config)
    save_config(user_config)

    echo_success('New setting:')
    echo_info(toml.dumps(updated_config).rstrip())
