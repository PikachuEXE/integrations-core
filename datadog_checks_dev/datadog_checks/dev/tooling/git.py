# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import re
import os

from .constants import ROOT
from ..utils import run_command

# match something like `(#1234)` and return `1234` in a group
PR_REG = re.compile(r'\(#(\d+)\)')


def get_current_branch():
    """
    Get the current branch name.
    """
    command = 'git rev-parse --abbrev-ref HEAD'
    stdout, _, _ = run_command(command, hide='out')
    return stdout.strip()


def parse_pr_numbers(git_log_lines):
    """
    Parse PR numbers from commit messages. At GitHub those have the format:

        `here is the message (#1234)`

    being `1234` the PR number.
    """
    prs = []
    for line in git_log_lines:
        match = re.search(PR_REG, line)
        if match:
            prs.append(match.group(1))
    return prs


def get_diff(check_name, target_tag):
    """
    Get the git diff from HEAD for the given check
    """
    target_path = os.path.join(ROOT, check_name)
    command = 'git log --pretty=%s {}... {}'.format(target_tag, target_path)
    stdout, _, _ = run_command(command, hide='out')
    return stdout.splitlines()


def git_commit(targets, message):
    """
    Commit the changes for the given targets.
    """
    target_paths = []
    for t in targets:
        target_paths.append(os.path.join(ROOT, t))

    run_command('git add {}'.format(' '.join(target_paths)))
    run_command('git commit -m "{}"'.format(message))


def git_tag(tag_name, push=False):
    """
    Tag the repo using an annotated tag.
    """
    run_command('git tag -a {} -m "{}"'.format(tag_name, tag_name))
    if push:
        run_command('git push origin {}'.format(tag_name))
