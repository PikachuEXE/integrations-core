# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

from mock import patch

from datadog_checks.nagios import Nagios
from .common import CHECK_NAME, CUSTOM_TAGS

# Random test values
METRIC_NAME = 'nagios.metric_name'
METRIC_VALUE = 42
METRIC_TAGS = CUSTOM_TAGS
METRIC_TIMESTAMP = 1337404007


class TestGaugeWrapper:

    def test_gauge_without_timestamp(self):
        """
        Test the 'gauge' wrapper to see if it strips the 'timestamp' arg for gauge functions that do not accept it
        """

        def timestamp_excluded_gauge(self, name, value, **kwargs):
            """
            A gauge function that does not accept the 'timestamp' argument
            """
            # Make sure we get the original arguments back and timestamp is not being received
            assert name == METRIC_NAME
            assert value == METRIC_VALUE
            assert 'timestamp' not in kwargs
            assert kwargs['tags'] == METRIC_TAGS

        # Make sure we're removing timestamps for gauge functions that do not accept 'timestamp'
        with patch('datadog_checks.checks.AgentCheck.gauge', new=timestamp_excluded_gauge):
            nagios = Nagios(CHECK_NAME, {}, {})
            nagios.gauge(METRIC_NAME, METRIC_VALUE, tags=METRIC_TAGS, timestamp=METRIC_TIMESTAMP)

    def test_gauge_with_timestamp(self):
        """
        Test the 'gauge' wrapper to see if it doesn't strip anything for gauge functions that accept timestamps
        """

        def timestamp_included_gauge(self, name, value, tags=None, timestamp=None):
            """
            A gauge function that should accept the 'timestamp' argument
            """

            # Make sure we get the original arguments back
            assert name == METRIC_NAME
            assert value == METRIC_VALUE
            assert timestamp == METRIC_TIMESTAMP
            assert tags == METRIC_TAGS

        # Make sure we're removing timestamps for gauge functions that do not accept 'timestamp'
        with patch('datadog_checks.checks.AgentCheck.gauge', new=timestamp_included_gauge):
            nagios = Nagios(CHECK_NAME, {}, {})
            nagios.gauge(METRIC_NAME, METRIC_VALUE, tags=METRIC_TAGS, timestamp=METRIC_TIMESTAMP)
