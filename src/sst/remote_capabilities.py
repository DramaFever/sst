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

from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import logging
import requests
import sauceclient

logger = logging.getLogger('SST')

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class SauceLabs:
    """Helper class for creating an instance of sauceclient and posting results.
    Credentials should be defined in the directory where your tests
    are stored in a sauce_config.py module."""

    client = None
    URL = None
    api_base = None

    def __init__(self, username, access_key, url, apibase=None):
        logger.debug('Creating SauceLabs client')
        self.URL = url
        if apibase:
            self.api_base = apibase
        self.client = sauceclient.SauceClient(username, access_key, apibase)

    def update_job(self, session_id, name):
        if not self.api_base:
            self.client.jobs.update_job(job_id=session_id, name=name)

    def send_result(self, session_id, name, result):
        logger.debug('Sending result to SauceLabs')
        logger.debug('SauceOnDemandSessionID={} job-name={}'.format(session_id,
                                                                    name))
        if self.api_base and 'testobject' in self.api_base:
            self.send_result_testobject(session_id, result)
        else:
            self.client.jobs.update_job(job_id=session_id, name=name,
                                        passed=result)

    def send_result_testobject(self, session_id, result):
        url = self.api_base + 'v2/appium/session/{}/test'.format(session_id)
        headers = {"Content-Type": "application/json"}
        result_dict = {"passed": result}
        r = requests.put(url, headers=headers, data=json.dumps(result_dict))
        if not r.raise_for_status():
            logger.debug('Sent result to TestObject: {}'.format(result))
