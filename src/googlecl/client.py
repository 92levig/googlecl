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


import gdata.client
import googlecl
import googlecl.base
import logging

LOG = logging.getLogger(googlecl.LOGGER_NAME)

# This class CANNOT be used unless an instance also inherits from
# gdata.client.GDClient somehow.
# TODO: pylint bugs out over the missing functions/attributes here,
# but there are no run-time errors. Make pylint happy!
class BaseClientCL(googlecl.base.BaseCL):

  """Extension of gdata.GDataService specific to GoogleCL."""

  def __init__(self, section, request_error_class=gdata.client.RequestError,
               *args, **kwargs):
    super(BaseClientCL, self).__init__(section, request_error_class,
                                       *args, **kwargs)
    LOG.debug('Initialized googlecl.client.BaseClientCL')

  def is_token_valid(self, test_uri):
    try:
      return super(BaseClientCL, self).is_token_valid(test_uri)
    # If access has been revoked through account settings, get weird Unauthorized
    # error complaining about AuthSub.
    except gdata.client.Unauthorized:
      return False

  IsTokenValid = is_token_valid

  def request_access(self, domain, hostid, scopes=None):
    """Do all the steps involved with getting an OAuth access token.

    Keyword arguments:
      domain: Domain to request access for.
              (Sets the hd query parameter for the authorization step).
      hostid: string Descriptor for the machine doing the requesting.
              e.g. 'username@host'
      scopes: String or list of strings describing scopes to request
              access to. If None, tries to access self.auth_scopes

    Returns:
      True if access token was succesfully retrieved and set, otherwise False.

    """
    import ConfigParser
    import webbrowser
    import urllib
    import time
    # XXX: Not sure if get_oauth_token() will accept a list of mixed strings and
    # atom.http_core.Uri objects...
    if not scopes:
      scopes = self.auth_scopes
    if not isinstance(scopes, list):
      scopes = [scopes,]
    # Some scopes are packaged as tuples, which is a no-no for
    # gauth.generate_request_for_request_token() (called by get_oauth_token)
    for i, scope in enumerate(scopes):
      if isinstance(scope, tuple):
        scopes[i:i+1] = list(scope)
    scopes.extend(['https://www.googleapis.com/auth/userinfo#email'])
    LOG.debug('Scopes being requested: ' + str(scopes))

    display_name = 'GoogleCL %s' % hostid
    url = gdata.gauth.REQUEST_TOKEN_URL + '?xoauth_displayname=' +\
          urllib.quote(display_name)
    try:
      # Installed applications do not have a pre-registration and so follow
      # directions for unregistered applications

      # No idea where this is actually documented, but next='oob' will
      # redirect the user to a confirmation page that provides
      # the oauth_verifier. This seems the only way to get it for
      # installed apps?
      request_token = self.get_oauth_token(scopes, next='oob',
                                           consumer_key='anonymous',
                                           consumer_secret='anonymous',
                                           url=url)
    except self.request_error, err:
      LOG.error(err[0]['body'].strip() + '; Request token retrieval failed!')
      if str(err).find('Timestamp') != -1:
        LOG.info('Is your system clock up to date? See the FAQ on our ' +
                 'wiki: http://code.google.com/p/googlecl/w/list')
      return False
    auth_url = request_token.generate_authorization_url(
                                                      google_apps_domain=domain)
    try:
      try:
        browser_str = googlecl.CONFIG.get('GENERAL', 'auth_browser')
      except ConfigParser.NoOptionError:
        browser = webbrowser.get()
      else:
        browser = webbrowser.get(browser_str)
      browser.open(str(auth_url))
    except (webbrowser.Error, OSError), err:
      LOG.info('Failed to launch web browser: ' + str(err))
    print 'Please log in and/or grant access at ' + str(auth_url)
    # Try to keep that damn "Created new window in existing browser session."
    # message away from raw_input call.
    time.sleep(2)
    print ''
    request_token.verifier = raw_input('Please enter the verification code on'
                                       ' the success page: ').strip()
    # This upgrades the token, and if successful, sets the access token
    try:
      access_token = self.get_access_token(request_token)
    except gdata.client.RequestError, err:
      LOG.error(err)
      LOG.error('Token upgrade failed! Could not get OAuth access token.')
      return False
    else:
      self.auth_token = access_token
      return True

  RequestAccess = request_access

  def SetOAuthToken(self, token):
    self.auth_token = token
