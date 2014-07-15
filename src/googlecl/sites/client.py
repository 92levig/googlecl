# Copyright (C) 2013 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Service details and instances for the Sites service using version 1.4.

Some use cases:

"""
from __future__ import with_statement

import gdata.sites.client
import logging
import os
import shutil
import googlecl
import googlecl.client
from googlecl.sites import SECTION_HEADER


LOG = logging.getLogger(googlecl.sites.LOGGER_NAME + '.client')


class SitesClientCL(gdata.sites.client.SitesClient,
                   googlecl.client.BaseClientCL):

  """Extends gdata.sites.client.SitesClient for the command line.

  This class adds some features focused on using Google Sites via an installed
  app with a command line interface.

  """
  def __init__(self, config):
    """Constructor."""
    domain = config.lazy_get(SECTION_HEADER, 'domain')
    site = config.lazy_get(SECTION_HEADER, 'site')
    gdata.sites.client.SitesClient.__init__(
        self, source='GoogleCL', domain=domain, site=site)
    googlecl.client.BaseClientCL.__init__(self, SECTION_HEADER, config)

  def is_token_valid(self, test_uri='/feeds/'):
    """Check that the token being used is valid."""
    return googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid


SERVICE_CLASS = SitesClientCL
