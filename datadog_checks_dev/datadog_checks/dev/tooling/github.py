# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os

import requests

from .constants import CHANGELOG_LABEL_PREFIX

API_URL = 'https://api.github.com'
PR_ENDPOINT = API_URL + '/repos/DataDog/integrations-core/pulls/{}'


def get_auth_info(user, token):
    """
    See if a personal access token was passed
    """
    user = user or os.environ.get('DATADOG_GITHUB_API_USER')
    token = token or os.environ.get('DATADOG_GITHUB_API_TOKEN')
    if user and token:
        return user, token


def get_changelog_types(pr_payload):
    """
    Fetch the labels from the PR and process the ones related to the changelog.
    """
    changelog_labels = []
    for label in pr_payload.get('labels', []):
        name = label.get('name', '')
        if name.startswith(CHANGELOG_LABEL_PREFIX):
            # only add the name, e.g. for `changelog/Added` it's just `Added`
            changelog_labels.append(name.split(CHANGELOG_LABEL_PREFIX)[1])

    return changelog_labels


def get_pr(pr_num, auth=None):
    """
    Get the payload for the given PR number. Let exceptions bubble up.
    """
    response = requests.get(PR_ENDPOINT.format(pr_num), auth=auth)
    return response.json()


def from_contributor(pr_payload):
    """
    If the PR comes from a fork, we can safely assumed it's from an
    external contributor.
    """
    return pr_payload.get('head', {}).get('repo', {}).get('fork') is True
