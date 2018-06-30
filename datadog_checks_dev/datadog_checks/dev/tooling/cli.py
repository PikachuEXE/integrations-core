# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import click

from .commands import ALL_COMMANDS
from .commands.utils import CONTEXT_SETTINGS, echo_warning
from .config import config_file_exists, load_config
from .constants import set_root


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option()
@click.pass_context
def ddev(ctx):
    if not config_file_exists():
        echo_warning(
            'No config file found; using default settings. Please see `ddev config -h`.'
        )

    # Load and store configuration for sub-commands.
    config = load_config()
    ctx.obj = config

    # Set the default root to `integrations-core`.
    set_root(config.get('core', ''))


for command in ALL_COMMANDS:
    ddev.add_command(command)
