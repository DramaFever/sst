#
#   Copyright (c) 2011-2013 Canonical Ltd.
#
#   This file is part of: SST (selenium-simple-test)
#   https://launchpad.net/selenium-simple-test
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from __future__ import print_function

import ast
import logging
import json
import os
import pdb
import testtools
import testtools.content
import traceback

from selenium.common import exceptions
from testrail import APIError
from sst import (
    actions,
    browsers,
    config,
    context,
    xvfbdisplay,
    testrail_helper,
    proxy,
    xvfbdisplay
)

logger = logging.getLogger('SST')


class SSTTestCase(testtools.TestCase):
    """A test case that can use the sst framework."""

    xvfb = None
    xserver_headless = False

    browser_factory = browsers.FirefoxFactory()

    assume_trusted_cert_issuer = False

    wait_timeout = 10
    wait_poll = 0.1
    base_url = None

    case_id = None
    results_directory = None
    screenshots_on = False
    debug_post_mortem = False
    extended_report = False
    use_proxy = False
    proxy = None
    proxy_address = None

    def setUp(self):
        super(SSTTestCase, self).setUp()
        if self.base_url is not None:
            actions.set_base_url(self.base_url)
        actions._set_wait_timeout(self.wait_timeout, self.wait_poll)
        # Ensures sst.actions will find me
        actions._test = self
        if self.xserver_headless and self.xvfb is None:
            # If we need to run headless and no xvfb is already running, start
            # a new one for the current test, scheduling the shutdown for the
            # end of the test.
            self.xvfb = xvfbdisplay.use_xvfb_server(self)
        config.results_directory = self.results_directory
        self.browser = None
        if self.use_proxy:
            self.start_proxy_for_test(self.id())
            self.addCleanup(self.stop_proxy)
        self.start_browser()
        self.addCleanup(self.stop_browser)
        if 'per_case' in config.api_test_results:
            self.addCleanup(self.post_api_test_result)
        if 'per_suite' in config.api_test_results:
            self.addCleanup(self._store_case_result)
        if self.screenshots_on:
            self.addOnException(self.take_screenshot_and_page_dump)
        if self.debug_post_mortem:
            self.addOnException(
                self.print_exception_and_enter_post_mortem)
        if self.extended_report:
            self.addOnException(self.report_extensively)

    def shortDescription(self):
        # testools wrongly defines this as returning self.id(). Since we're not
        # using the short description (aka the first line of the test
        # docstring) (who is ? should we ? => the docstring, if present, is
        # nice to display when the test fails...), we revert to the default
        # behavior so runners and results don't get mad.
        return None

    def start_proxy_for_test(self, test_id):
        self.proxy = proxy.Proxy(test_id)
        self.proxy_address = self.proxy.proxy.proxy

    def stop_proxy(self):
        self.proxy.stop_proxy()
        self.proxy = None
        self.proxy_address = None

    def _start_browser(self):
        self.browser_factory.setup_for_test(self)
        self.browser = self.browser_factory.browser()

    def start_browser(self):
        max_attempts = 5
        for nb_attempts in range(1, max_attempts + 1):
            try:
                logger.debug('Starting browser (attempt: %d)' % nb_attempts)
                self._start_browser()
                break
            except exceptions.WebDriverException:
                if nb_attempts >= max_attempts:
                    raise
        logger.debug('Browser started: %s' % self.browser.name)

    def stop_browser(self):
        logger.debug('Stopping browser')
        self.browser.quit()

    def take_screenshot_and_page_dump(self, exc_info):
        try:
            filename = 'screenshot-{0}.png'.format(self.id())
            actions.take_screenshot(filename)
        except Exception:
            # FIXME: Needs to be reported somehow ? -- vila 2012-10-16
            pass
        try:
            # also dump page source
            filename = 'pagesource-{0}.html'.format(self.id())
            actions.save_page_source(filename)
        except Exception:
            # FIXME: Needs to be reported somehow ? -- vila 2012-10-16
            pass

    def print_exception_and_enter_post_mortem(self, exc_info):
        exc_class, exc, tb = exc_info
        traceback.print_exception(exc_class, exc, tb)
        pdb.post_mortem(tb)

    def report_extensively(self, exc_info):
        exc_class, exc, tb = exc_info
        original_message = str(exc)
        try:
            current_url = actions.get_current_url()
        except Exception:
            current_url = 'unavailable'
        try:
            page_source = actions.get_page_source()
        except Exception:
            page_source = 'unavailable'
        self.addDetail(
            'Original exception',
            testtools.content.text_content('{0} : {1}'.format(
                exc.__class__.__name__, original_message)))
        self.addDetail('Current url',
                       testtools.content.text_content(current_url))
        self.addDetail('Page source',
                       testtools.content.text_content(page_source))

    def post_api_test_result(self):
        logger.debug("Sending test case result")
        try:
            result = self._get_case_result()
            if result:
                testrail_helper.send_result(result['case_id'],
                                            result['status_id'],
                                            result['comment'])
        except APIError, e:
            logger.debug("Could not send test case result \n" + str(e))

    def _store_case_result(self):
        if self._get_case_result():
            testrail_helper.run_results.append(self._get_case_result())

    def _get_case_result(self):
        if self.case_id:
            failed = self.getDetails()
            status_id = testrail_helper.APITestStatus.RETEST if failed \
                   else testrail_helper.APITestStatus.PASSED
            comment = json.dumps(str(failed)) if failed else None
            return { 'case_id': self.case_id,
                     'status_id': status_id,
                     'comment': comment }
        logger.debug("Could not find case_id for {}".format(self.id()))
        return None


class SSTScriptTestCase(SSTTestCase):
    """Test case used internally by sst-run and sst-remote."""

    def __init__(self, script_dir, script_name, context_row=None):
        super(SSTScriptTestCase, self).__init__('run_test_script')
        self.script_dir = script_dir
        self.script_name = script_name
        self.script_path = os.path.join(self.script_dir, self.script_name)

        # pythonify the script path into a python path
        test_id = self.script_path
        if test_id.startswith('./'):
            test_id = test_id[2:]
        self.id = lambda: '%s' % (test_id.replace(os.sep, '.'))
        if context_row is None:
            context_row = {}
        self.context = context_row

        # get id from script name for use when posting
        # results to an external test case management tool
        try:
            self.case_id = int(filter(lambda x:x.isdigit(), self.script_name))
        except ValueError:
            # if script name doesn't contain a number skip it
            pass

    def __str__(self):
        # Since we use run_test_script to encapsulate the call to the
        # compiled code, we need to override __str__ to get a proper name
        # reported.
        return "%s" % (self.id(),)

    def setUp(self):
        self._compile_script()
        # The script may override some settings. The default value for
        # ASSUME_TRUSTED_CERT_ISSUER is False, so if the user mentions it
        # in his script, it's to turn them on. Also, getting our hands on
        # the values used in the script is too hackish.
        if 'ASSUME_TRUSTED_CERT_ISSUER' in self.code.co_names:
            self.assume_trusted_cert_issuer = True
        super(SSTScriptTestCase, self).setUp()
        # Start with default values
        actions.reset_base_url()
        actions._set_wait_timeout(10, 0.1)
        # Possibly inject parametrization from associated .csv file
        previous_context = context.store_context()
        self.addCleanup(context.restore_context, previous_context)
        context.populate_context(self.context, self.script_path,
                                 self.browser.name)

    def _compile_script(self):
        self.script_path = os.path.join(self.script_dir, self.script_name)
        with open(self.script_path) as f:
            source = f.read() + '\n'
        self.code = compile(source, self.script_path, 'exec')

    def run_test_script(self, result=None):
        # Run the test catching exceptions sstnam style
        try:
            exec(self.code, self.context)
        except actions.EndTest:
            pass


def get_data(csv_path):
    """
    Return a list of data dicts for parameterized testing.

    The first row (headers) match data_map key names. rows beneath are filled
    with data values.
    """
    rows = []
    logger.debug('Reading data from %r' % os.path.split(csv_path)[-1])
    row_num = 0
    with open(csv_path) as f:
        headers = f.readline().rstrip().split('^')
        headers = [header.replace('"', '') for header in headers]
        headers = [header.replace("'", '') for header in headers]
        for line in f:
            row = {}
            row_num += 1
            row['_row_num'] = row_num
            fields = line.rstrip().split('^')
            for header, field in zip(headers, fields):
                try:
                    value = ast.literal_eval(field)
                except ValueError:
                    value = field
                    if value.lower() == 'false':
                        value = False
                    if value.lower() == 'true':
                        value = True
                row[header] = value
            rows.append(row)
    logger.debug('found %s rows' % len(rows))
    return rows
