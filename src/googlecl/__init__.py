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


"""Contains configuration and read/write utility functions for GoogleCL."""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import ConfigParser
import os


CONFIG = ConfigParser.ConfigParser()
GOOGLE_CL_DIR = os.path.expanduser(os.path.join('~', '.googlecl'))
CONFIG_FILENAME = 'config'
HISTORY_FILENAME = 'history'
TOKENS_FILENAME_FORMAT = 'access_tok_%s'
DEVKEY_FILENAME = 'yt_devkey'


def get_config_option(section, option, default=None, type=None):
  """Return option from config file.
  
  Tries to retrieve <option> from the given section. If that fails, tries to
  retrieve the same option from the GENERAL section. If that fails,
  returns value of "default" parameter.
  
  Keyword arguments:
    section: Name of the section to initially try to retrieve the option from.
    option: Name of the option to retrieve.
    default: Value to return if the option does not exist in a searched section.
    type: Conversion function to use on the string, or None to leave as string.
          For example, if you want an integer value returned, this should be
          set to int. This is not applied to the "default" parameter.
  
  Returns:
    Value of the option if it exists in the prefs file, or value of "default"
    if option does not exist.
  
  """
  try:
    try:
      value = CONFIG.get(section, option)
    except ConfigParser.NoSectionError:
      value = CONFIG.get('GENERAL', option)
    except ConfigParser.NoOptionError:
      value = CONFIG.get('GENERAL', option)
    if type:
      # bool() function doesn't actually do what we wanted, so intercept it and
      # replace with comparison
      if type == bool:
        return value.lower() == 'true'
      else:
        return type(value)
    else:
      return value
  except ConfigParser.NoOptionError:
    return default


def load_preferences(path=None):
  """Load preferences / configuration file.
  
  Keyword arguments:
    path: Path to the configuration file. Default None for the default location.
  
  """
  def set_options():
    """Set the most basic options in the config file."""
    import googlecl
    import getpass
    # These may be useful to define at the module level, but for now,
    # keep them here.
    # REMEMBER: updating these means you need to update the CONFIG readme.
    default_hostid = getpass.getuser() + '@' +  os.uname()[1]
    _youtube = {'max_results': '50'}
    _contacts = {'list_style': 'title,email'}
    _calendar = {'list_style': 'title,when'}
    _picasa = {'access': 'public'}
    _general = {'regex': 'True',
               'delete_by_default': 'False',
               'delete_prompt': 'True',
               'tags_prompt': 'False',
               'url_style': 'site',
               'list_style': 'title,url-site',
               'missing_field_value': 'N/A',
               'date_print_format': '%b %d %H:%M',
               'cap_results': 'False',
               'hostid': default_hostid}
    _docs = {'document_format': 'txt',
             'spreadsheet_format': 'xls',
             'presentation_format': 'ppt',
             'format': 'txt',
             'spreadsheet_editor': 'openoffice.org',
             'presentation_editor': 'openoffice.org'}
    config_defaults = {googlecl.docs.SECTION_HEADER: _docs,
                       googlecl.picasa.SECTION_HEADER: _picasa,
                       googlecl.contacts.SECTION_HEADER: _contacts,
                       googlecl.calendar.SECTION_HEADER: _calendar,
                       googlecl.youtube.SECTION_HEADER: _youtube,
                       'GENERAL': _general}
    made_changes = False
    for section_name in config_defaults.keys():
      if not CONFIG.has_section(section_name):
        CONFIG.add_section(section_name)
      section = config_defaults[section_name]
      missing_opts = set(section.keys()) - set(CONFIG.options(section_name))
      if missing_opts:
        made_changes = True
      for opt in missing_opts:
        CONFIG.set(section_name, opt, section[opt])
    return made_changes
  
  if path:
    try:
      CONFIG.read(path)
    except ConfigParser.ParsingError, err:
      print err
      return False
  else:
    if not os.path.exists(GOOGLE_CL_DIR):
      os.makedirs(GOOGLE_CL_DIR)
    config_path = os.path.join(GOOGLE_CL_DIR, CONFIG_FILENAME)
    if os.path.exists(config_path):
      CONFIG.read(config_path)
    else:
      print 'Did not find config / preferences file at ' + config_path
      print '... making new one.'
  made_changes = set_options()
  if made_changes:
    with open(config_path, 'w') as config_file:
      CONFIG.write(config_file)
  return True


def read_access_token(service, user):
  """Try to read an authorization token from a file.
  
  Keyword arguments:
    service: Service the token is for. E.g. 'picasa', 'docs', 'blogger'.
    user: Username / email the token is associated with.
  
  Returns:
    The access token, if it exists. If there is no access token,
    return NoneType.
  
  """
  import pickle
  token_path = os.path.join(GOOGLE_CL_DIR, TOKENS_FILENAME_FORMAT % user)
  if os.path.exists(token_path):
    with open(token_path, 'rb') as token_file:
      token_dict = pickle.load(token_file)
    try:
      token = token_dict[service.lower()]
    except KeyError:
      return None
    else:
      return token
  else:
    return None


def read_devkey():
  """Return the cached YouTube developer's key."""
  key_path = os.path.join(GOOGLE_CL_DIR, DEVKEY_FILENAME)
  devkey = None
  if os.path.exists(key_path):
    with open(key_path, 'r') as key_file:
      devkey = key_file.read().strip()
  return devkey


def remove_access_token(service, user):
  """Remove an auth token for a particular user and service."""
  import pickle
  token_path = os.path.join(GOOGLE_CL_DIR, TOKENS_FILENAME_FORMAT % user)
  success = False
  if os.path.exists(token_path):
    with open(token_path, 'r+') as token_file:
      token_dict = pickle.load(token_file)
      try:
        del token_dict[service.lower()]
      except KeyError:
        print 'No token for ' + service
      else:
        pickle.dump(token_dict, token_file)
        success = True
  return success


def set_missing_default(section, option, value, config_path=None):
  """Set the option for a section if not defined already.
  
  Keyword arguments:
    section: Title of the section to set the option in.
    option: Option to set.
    value: Value to give the option.
    config_path: Path to the configuration file.
                 Default None to use the default path defined in this module.
  
  """
  existing_value = ''
  try:
    existing_value = CONFIG.get(section, option)
  except ConfigParser.NoSectionError:
    CONFIG.add_section(section)
  except ConfigParser.NoOptionError:
    # If there's no such option, that's fine. We'll fix that in a sec.
    pass
  if not existing_value:
    if not config_path:
      config_path = os.path.join(GOOGLE_CL_DIR, CONFIG_FILENAME)
    if os.path.exists(config_path):
      CONFIG.set(section, option, value)
      with open(config_path, 'w') as config_file:
        CONFIG.write(config_file)


def write_access_token(service, user, token):
  """Write an authorization token to a file.
  
  Keyword arguments:
    service: Service the token is for. E.g. 'picasa', 'docs', 'blogger'.
    user: Username / email the token is associated with.
  
  """
  import pickle
  import stat
  token_path = os.path.join(GOOGLE_CL_DIR, TOKENS_FILENAME_FORMAT % user)
  if os.path.exists(token_path):
    with open(token_path, 'rb') as token_file:
      try:
        token_dict = pickle.load(token_file)
      except (KeyError, IndexError):
        print 'Failed to load token_file (may be corrupted?)'
        file_invalid = True
      else:
        file_invalid = False
    if file_invalid:
      new_path = token_path + '.failed'
      os.rename(token_path, new_path)
      print 'Moved ' + token_path + ' to ' + new_path
      token_dict = {}
  else:
    token_dict = {}
  token_dict[service] = token 
  with open(token_path, 'wb') as token_file:
    # Ensure only the owner of the file has read/write permission
    os.chmod(token_path, stat.S_IRUSR | stat.S_IWUSR)
    pickle.dump(token_dict, token_file)


def write_devkey(devkey):
  """Write the devkey to the youtube devkey file."""
  import stat
  key_path = os.path.join(GOOGLE_CL_DIR, DEVKEY_FILENAME)
  with open(key_path, 'w') as key_file:
    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
    key_file.write(devkey)
