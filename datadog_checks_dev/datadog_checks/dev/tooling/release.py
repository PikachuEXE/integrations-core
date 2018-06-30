# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os
import re
import sys
from collections import namedtuple
from datetime import datetime
from io import open

from six import StringIO

from .constants import CHANGELOG_TYPE_NONE, ROOT
from .git import parse_pr_numbers, get_diff
from .github import get_changelog_types, from_contributor, get_pr
from .utils import get_version_file, load_manifest
from ..utils import read_file

# Maps the Python platform strings to the ones we have in the manifest
PLATFORMS_TO_PY = {
    'windows': 'win32',
    'mac_os': 'darwin',
    'linux': 'linux2',
}
ALL_PLATFORMS = sorted(PLATFORMS_TO_PY)

VERSION = re.compile(r'__version__ *= *(?:[\'"])(.+?)(?:[\'"])')

ChangelogEntry = namedtuple('ChangelogEntry', 'number, title, url, author, author_url, from_contributor')


def get_release_tag_string(check_name, version_string):
    """
    Compose a string to use for release tags
    """
    return '{}-{}'.format(check_name, version_string)


def update_version_module(check_name, old_ver, new_ver):
    """
    Change the Python code in the __about__.py module so that `__version__`
    contains the new value.
    """
    version_file = get_version_file(check_name)
    contents = read_file(version_file)

    contents = contents.replace(old_ver, new_ver)
    with open(version_file, 'w') as f:
        f.write(contents)


def get_agent_requirement_line(check, version):
    """
    Compose a text line to be used in a requirements.txt file to install a check
    pinned to a specific version.
    """
    # base check and siblings have no manifest
    if check in ('datadog_checks_base', 'datadog_checks_tests_helper'):
        return '{}=={}'.format(check, version)

    m = load_manifest(check)
    platforms = sorted(m.get('supported_os', []))

    # all platforms
    if platforms == ALL_PLATFORMS:
        return '{}=={}'.format(check, version)
    # one specific platform
    elif len(platforms) == 1:
        return "{}=={}; sys_platform == '{}'".format(check, version, PLATFORMS_TO_PY.get(platforms[0]))
    # assuming linux+mac here for brevity
    elif platforms and 'windows' not in platforms:
        return "{}=={}; sys_platform != 'win32'".format(check, version)
    else:
        raise Exception("Can't parse the `supported_os` list for the check {}: {}".format(check, platforms))


def update_agent_requirements(req_file, check, newline):
    """
    Replace the requirements line for the given check
    """
    with open(req_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(req_file, 'w', encoding='utf-8') as f:
        for line in lines:
            check_name = line.split('==')[0]
            if check_name == check:
                f.write(newline + '\n')
            else:
                f.write(line)


def update_changelog(target, cur_version, new_version, dry_run=False):
    """
    Actually perform the operations needed to update the changelog, this
    method is supposed to be used by other tasks and not directly.
    """
    # get the name of the current release tag
    target_tag = get_release_tag_string(target, cur_version)

    # get the diff from HEAD
    diff_lines = get_diff(target, target_tag)

    # for each PR get the title, we'll use it to populate the changelog
    pr_numbers = parse_pr_numbers(diff_lines)
    print('Found {} PRs merged since tag: {}'.format(len(pr_numbers), target_tag))
    entries = []
    for pr_num in pr_numbers:
        try:
            payload = get_pr(pr_num)
        except Exception as e:
            sys.stderr.write('Unable to fetch info for PR #{}\n: {}'.format(pr_num, e))
            continue

        changelog_labels = get_changelog_types(payload)

        if not changelog_labels:
            sys.exit('No valid changelog labels found attached to PR #{}, please add one'.format(pr_num))
        elif len(changelog_labels) > 1:
            sys.exit('Multiple changelog labels found attached to PR #{}, please use only one'.format(pr_num))

        changelog_type = changelog_labels[0]
        if changelog_type == CHANGELOG_TYPE_NONE:
            # No changelog entry for this PR
            print("Skipping PR #{} from changelog".format(pr_num))
            continue

        author = payload.get('user', {}).get('login')
        author_url = payload.get('user', {}).get('html_url')
        title = '[{}] {}'.format(changelog_type, payload.get('title'))

        entry = ChangelogEntry(pr_num, title, payload.get('html_url'),
                               author, author_url, from_contributor(payload))

        entries.append(entry)

    # store the new changelog in memory
    new_entry = StringIO()

    # the header contains version and date
    header = '## {} / {}\n'.format(new_version, datetime.now().strftime('%Y-%m-%d'))
    new_entry.write(header)

    # one bullet point for each PR
    new_entry.write('\n')
    for entry in entries:
        thanknote = ''
        if entry.from_contributor:
            thanknote = ' Thanks [{}]({}).'.format(entry.author, entry.author_url)
        new_entry.write('* {}. See [#{}]({}).{}\n'.format(entry.title, entry.number, entry.url, thanknote))
    new_entry.write('\n')

    # read the old contents
    changelog_path = os.path.join(ROOT, target, 'CHANGELOG.md')
    with open(changelog_path, 'r') as f:
        old = f.readlines()

    # write the new changelog in memory
    changelog = StringIO()

    # preserve the title
    changelog.write(''.join(old[:2]))

    # prepend the new changelog to the old contents
    # make the command idempotent
    if header not in old:
        changelog.write(new_entry.getvalue())

    # append the rest of the old changelog
    changelog.write(''.join(old[2:]))

    # print on the standard out in case of a dry run
    if dry_run:
        print(changelog.getvalue())
        sys.exit(0)

    # overwrite the old changelog
    with open(changelog_path, 'w') as f:
        f.write(changelog.getvalue())
