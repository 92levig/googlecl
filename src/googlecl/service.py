# Copyright (C) 2010 Google Inc.
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


"""Basic service extensions for the gdata python client library for use on
  the command line."""


import gdata.service
import googlecl
import googlecl.base
import logging

LOG = logging.getLogger(googlecl.LOGGER_NAME)


class BaseServiceCL(googlecl.base.BaseCL):

  """Extension of gdata.GDataService specific to GoogleCL."""

  def __init__(self, section, request_error_class=gdata.service.RequestError,
               *args, **kwargs):
    super(BaseServiceCL, self).__init__(section,
                                        request_error_class,
                                        *args,
                                        **kwargs)
    # Most services using old gdata API have to disable ssl.
    self.ssl = False
    LOG.debug('Initialized googlecl.service.BaseServiceCL')

  def request_access(self, domain, hostid, scopes=None):
    """Do all the steps involved with getting an OAuth access token.
    
    Keyword arguments:
      domain: Domain to request access for.
              (Sets the hd query parameter for the authorization step).
      scopes: String or list/tuple of strings describing scopes to request
              access to. Default None for default scope of service.
    Returns:
      True if access token was succesfully retrieved and set, otherwise False.
    
    """
    import ConfigParser
    import webbrowser
    # Installed applications do not have a pre-registration and so follow
    # directions for unregistered applications
    self.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                 consumer_key='anonymous',
                                 consumer_secret='anonymous')
    display_name = 'GoogleCL %s' % hostid
    fetch_params = {'xoauth_displayname':display_name}
    # First and third if statements taken from
    # gdata.service.GDataService.FetchOAuthRequestToken.
    # Need to do this detection/conversion here so we can add the 'email' API
    if not scopes:
      scopes = gdata.service.lookup_scopes(self.service)
    if isinstance(scopes, tuple):
      scopes = list(scopes)
    if not isinstance(scopes, list):
      scopes = [scopes,]
    scopes.extend(['https://www.googleapis.com/auth/userinfo#email'])
    LOG.debug('Scopes being requested: ' + str(scopes))

    try:
      request_token = self.FetchOAuthRequestToken(scopes=scopes,
                                                  extra_parameters=fetch_params)
    except gdata.service.FetchingOAuthRequestTokenFailed, err:
      LOG.error(err[0]['body'].strip() + '; Request token retrieval failed!')
      return False
    auth_params = {'hd': domain}
    auth_url = self.GenerateOAuthAuthorizationURL(request_token=request_token,
                                                  extra_params=auth_params)
    try:
      try:
        browser_str = googlecl.CONFIG.get('GENERAL', 'auth_browser')
      except ConfigParser.NoOptionError:
        browser = webbrowser.get()
      else:
        browser = webbrowser.get(browser_str)
      browser.open(auth_url)
    except webbrowser.Error, err:
      LOG.info('Failed to launch web browser: ' + str(err))
    message = 'Please log in and/or grant access via your browser at ' +\
              auth_url + ' then hit enter.'
    raw_input(message)
    # This upgrades the token, and if successful, sets the access token
    try:
      self.UpgradeToOAuthAccessToken(request_token)
    except gdata.service.TokenUpgradeFailed:
      LOG.error('Token upgrade failed! Could not get OAuth access token.')
      return False
    else:
      return True

  RequestAccess = request_access
