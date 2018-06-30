# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os
import sys

import click

from .utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting
)
from ..clean import clean_package, remove_compiled_scripts
from ...utils import dir_exists, resolve_path


@click.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Removes a project's build artifacts"
)
@click.argument('check', required=False)
@click.option(
    '--compiled-only', '-c',
    is_flag=True,
    help='Removes only .pyc files.'
)
@click.option(
    '--all', '-a', 'all_matches',
    is_flag=True,
    help=(
        "Disables the detection of a project's dedicated virtual "
        'env and/or editable installation. By default, these will '
        'not be considered.'
    )
)
@click.option(
    '--extras',
    is_flag=True,
    help='Work on `integrations-extras`.'
)
@click.option('--verbose', '-v', is_flag=True, help='Shows removed paths.')
@click.pass_context
def clean(ctx, check, compiled_only, all_matches, extras, verbose):
    """Removes a project's build artifacts.

    If `check` is not specified, the current working directory will be used.

    All `*.pyc`/`*.pyd`/`*.pyo`/`*.whl` files and `__pycache__` directories will be
    removed. Additionally, the following patterns will be removed from the root of
    the path: `.cache`, `.coverage`, `.eggs`, `.pytest_cache`, `.tox`, `build`,
    `dist`, and `*.egg-info`.
    """
    if check:
        config = ctx.obj
        repo = 'extras' if extras else 'core'
        repo_dir = config.get(repo, '')
        path = resolve_path(os.path.join(repo_dir, check))
        if not dir_exists(path):
            echo_failure(
                'Directory `{}` does not exist. Be sure to `ddev config set '
                '{repo} path/to/integrations-{repo}`.'.format(path, repo=repo)
            )
            sys.exit(1)
    else:
        path = os.getcwd()

    echo_waiting('Cleaning `{}`...'.format(path))
    if compiled_only:
        removed_paths = remove_compiled_scripts(path, detect_project=not all_matches)
    else:
        removed_paths = clean_package(path, detect_project=not all_matches)

    if verbose:
        if removed_paths:
            echo_success('Removed paths:')
            for p in removed_paths:
                echo_info('    {}'.format(p))

    if removed_paths:
        echo_success('Cleaned!')
    else:
        echo_success('Already clean!')
