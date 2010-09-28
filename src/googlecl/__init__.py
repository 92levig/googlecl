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
import logging
import os
import re

CONFIG = ConfigParser.ConfigParser()
SUBDIR_NAME = 'googlecl'
DEFAULT_GOOGLECL_DIR = os.path.expanduser(os.path.join('~', '.googlecl'))
HISTORY_FILENAME = 'history'
TOKENS_FILENAME_FORMAT = 'access_tok_%s'
DEVKEY_FILENAME = 'yt_devkey'

FILE_EXT_PATTERN = re.compile('.*\.([a-zA-Z0-9]{3,}$)')
LOGGER_NAME = 'googlecl'
LOG = logging.getLogger(LOGGER_NAME)


def determine_terminal_encoding():
  import sys
  in_enc = ''
  out_enc = ''
  if sys.stdin.encoding:
    in_enc = sys.stdin.encoding
  if sys.stdout.encoding:
    out_enc = sys.stdout.encoding

  # Sometimes these are both defined, and hopefully they are both equal.
  # I'm not sure if they are guaranteed to be equal.
  if in_enc.lower() == out_enc.lower():
    # If they're not defined, return the python system-wide default encoding
    if not in_enc:
      return_enc = sys.getdefaultencoding()
    else:
      return_enc = in_enc
  # If they are not equal, at least one of them must be defined.
  else:
    # Both defined, but are not the same
    if in_enc and out_enc:
      LOG.warning('HEY! You have a different encoding for input and output')
      LOG.warning('Input: ' + in_enc)
      LOG.warning('Output: ' + in_enc)
    return_enc = out_enc or in_enc
  LOG.debug('determine_terminal_encoding(): ' + return_enc)
  return return_enc


TERMINAL_ENCODING = determine_terminal_encoding()


class SafeEncodeError(Exception):
  pass


class SafeDecodeError(Exception):
  pass


def get_config_option(section, option, default=None, option_type=None):
  """Return option from config file.

  Tries to retrieve <option> from the given section. If that fails, tries to
  retrieve the same option from the GENERAL section. If that fails,
  returns value of "default" parameter.

  Keyword arguments:
    section: Name of the section to initially try to retrieve the option from.
    option: Name of the option to retrieve.
    default: Value to return if the option does not exist in a searched section.
    option_type: Conversion function to use on the string, or None to leave as
          string. For example, if you want an integer value returned, this
          should be set to int. This is not applied to the "default" parameter.

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
    if option_type:
      # bool() function doesn't actually do what we wanted, so intercept it and
      # replace with comparison
      if option_type == bool:
        return value.lower() == 'true'
      else:
        return option_type(value)
    else:
      return value
  except ConfigParser.NoOptionError:
    return default


def get_config_path(filename='config',
                    default_directories=None,
                    create_missing_dir=False):
  """Get the full path to the configuration file.

  See _get_xdg_path()

  """
  return _get_xdg_path(filename, 'CONFIG', default_directories,
                       create_missing_dir)


def get_data_path(filename,
                  default_directories=None,
                  create_missing_dir=False):
  """Get the full path to the history file.

  See _get_xdg_path()

  """
  return _get_xdg_path(filename, 'DATA', default_directories,
                       create_missing_dir)


def get_extension_from_path(path):
  """Return the extension of a file."""
  match = FILE_EXT_PATTERN.match(path)
  if match:
    return match.group(1)
  else:
    return None


def _get_xdg_path(filename, data_type, default_directories=None,
                  create_missing_dir=False):
  """Get the full path to a file using XDG file layout spec.

  Follows XDG Base Directory Specification.
  (http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html).
  Tries default_directories and DEFAULT_GOOGLECL_DIR if no file is found
  via XDG spec.

  Keyword arguments:
    filename: Filename of the file.
    data_type: One of 'config' for config files or 'data' for data files.
    default_directories: List of directories to check if no file is found
        in directories specified by XDG spec and DEFAULT_GOOGLECL_DIR.
        Default None.
    create_missing_dir: Whether or not to create a missing config subdirectory
        in the default base directory. Default False.

  Returns:
    Path to config file, which may not exist. If create_missing_dir,
    the directory where the config file should be will be created if it
    does not exist.

  """
  data_type = data_type.upper()
  if data_type not in ('CONFIG', 'DATA'):
    raise Exception('Invalid value for data_type: ' + data_type)
  xdg_home_dir = os.environ.get('XDG_' + data_type + '_HOME')
  if not xdg_home_dir:
    home_dir = os.path.expanduser('~')
    if data_type == 'DATA':
      xdg_home_dir = os.path.join(home_dir, '.local', 'share')
    elif data_type == 'CONFIG':
      # No variable defined, using $HOME/.config
      xdg_home_dir = os.path.join(home_dir, '.config')
  xdg_home_dir = os.path.join(xdg_home_dir, SUBDIR_NAME)

  xdg_dir_list = os.environ.get('XDG_' + data_type + '_DIRS')
  if not xdg_dir_list:
    if data_type == 'DATA':
      xdg_dir_list = '/usr/local/share/:/usr/share/'
    elif data_type == 'CONFIG':
      xdg_dir_list = '/etc/xdg'
  xdg_dir_list = [os.path.join(d, SUBDIR_NAME)
                  for d in xdg_dir_list.split(':')]

  dir_list = [os.path.abspath('.'), xdg_home_dir] + xdg_dir_list +\
             [DEFAULT_GOOGLECL_DIR]
  if default_directories:
    dir_list += default_directories
  for directory in dir_list:
    config_path = os.path.join(directory, filename)
    if os.path.isfile(config_path):
      return config_path
  LOG.debug('Could not find ' + filename + ' in any of ' + str(dir_list))

  if os.name == 'posix':
    default_dir = xdg_home_dir
    mode = 0700
  else:
    default_dir = DEFAULT_GOOGLECL_DIR
    mode = 0777
  if not os.path.isdir(default_dir) and create_missing_dir:
    try:
      os.makedirs(default_dir, mode)
    except OSError, err:
      LOG.error(err)
      return ''
  return os.path.join(default_dir, filename)


def load_preferences(path=None):
  """Load preferences / configuration file.

  Keyword arguments:
    path: Path to the configuration file. Default None for the default location.

  """
  def set_options():
    """Set the most basic options in the config file."""
    import googlecl
    import getpass
    import socket
    # These may be useful to define at the module level, but for now,
    # keep them here.
    # REMEMBER: updating these means you need to update the CONFIG readme.
    default_hostid = getpass.getuser() + '@' +  socket.gethostname()
    _youtube = {'max_results': '50'}
    _contacts = {'fields': 'name,email'}
    _calendar = {'fields': 'title,when'}
    _picasa = {'access': 'public'}
    _general = {'regex': 'True',
               'delete_by_default': 'False',
               'delete_prompt': 'True',
               'tags_prompt': 'False',
               'url_field': 'site',
               'fields': 'title,url-site',
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

  if not path:
    path = get_config_path(create_missing_dir=True)
    if not path:
      LOG.error('Could not create config directory!')
      return False
  if not os.path.exists(path):
    LOG.debug('Did not find config / preferences file at ' + path +
              '... making new one.')
  else:
    try:
      CONFIG.read(path)
    except ConfigParser.ParsingError, err:
      LOG.error(err)
      return False
  made_changes = set_options()
  if made_changes:
    with open(path, 'w') as config_file:
      CONFIG.write(config_file)
  return True


def _move_failed_token_file(token_path):
  new_path = token_path + '.failed'
  LOG.debug('Moving ' + token_path + ' to ' + new_path)
  if os.path.isfile(new_path):
    LOG.debug(new_path + ' already exists. Deleting it.')
    try:
      os.remove(new_path)
    except IOError, err:
      LOG.debug('Cannot remove old failed token file: ' + str(err))
  try:
    os.rename(token_path, new_path)
  except IOError, err:
    LOG.debug('Cannot rename token file to ' + new_path + ': ' + str(err))


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
  token_path = get_data_path(TOKENS_FILENAME_FORMAT % user)
  if os.path.exists(token_path):
    with open(token_path, 'rb') as token_file:
      try:
        token_dict = pickle.load(token_file)
      except ImportError:
        return None
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
  key_path = get_data_path(DEVKEY_FILENAME)
  devkey = None
  if os.path.exists(key_path):
    with open(key_path, 'r') as key_file:
      devkey = key_file.read().strip()
  return devkey


def remove_access_token(service, user):
  """Remove an auth token for a particular user and service."""
  import pickle
  token_path = get_data_path(TOKENS_FILENAME_FORMAT % user)
  success = False
  file_invalid = False
  if os.path.exists(token_path):
    with open(token_path, 'r+') as token_file:
      try:
        token_dict = pickle.load(token_file)
      except ImportError, err:
        LOG.error(err)
        LOG.info('You probably have been using different versions of gdata.')
        _move_failed_token_file(token_path)
        return False

      try:
        del token_dict[service.lower()]
      except KeyError:
        LOG.debug('No token for ' + service)
      else:
        try:
          pickle.dump(token_dict, token_file)
        except IOError, err:
          # IOError shouldn't happen, but I've seen Errno 0 pop up
          # on Windows XP with Python 2.5.
          LOG.error(err)
          if err.errno == 0:
            _move_failed_token_file(token_path)
        else:
          success = True
  return success


def safe_encode(string, target_encoding=TERMINAL_ENCODING,
                errors='backslashreplace'):
  """Encode a unicode string to target_encoding.

  If given a str type, check to see that target_encoding can decode it
  without an error. Raises a SafeEncodeError if it can't.
  Given any other type, returns str() version of it.

  Args:
    string: unicode String to encode.
    target_encoding: str Encoding to encode to. Default TERMINAL_ENCODING.
    errors: str Name of the error handler to call if something goes wrong.
            See docs on the codecs module. Default 'backslashreplace'.

  Returns:
    A string encoded with target_encoding, or raises an error.

  """
  if isinstance(string, unicode):
    return string.encode(target_encoding, errors)
  elif isinstance(string, str):
    try:
      string.decode(target_encoding)
    except UnicodeDecodeError:
      raise SafeEncodeError('Passed a non-unicode string to safe_encode!')
    else:
      return string
  else:
    # Got something else, probably an int or bool or the like.
    return str(string)


def safe_decode(string, current_encoding='utf-8', errors='strict'):
  """Decode a byte string.

  Raises a SafeDecodeError if current_encoding cannot decode the string and
  the value of errors causes an exception to be raised.
  If given a unicde type, returns it immediately.
  Given any other type, returns unicode() version of it.

  Args:
    string: str String to decode.
    target_encoding: str Encoding to decode with. Default 'utf-8'.
    errors: str Name of the error handler to call if something goes wrong.
            See docs on the codecs module. Default 'strict'.

  Returns:
    A unicode string, or raises an error.

  """
  if isinstance(string, str):
    try:
      return string.decode(current_encoding, errors)
    except UnicodeDecodeError:
      raise SafeDecodeError(current_encoding + ' could not decode ' +
                            repr(string))
  elif isinstance(string, unicode):
    return string
  else:
    # Got something elese, probably an int or bool or the like.
    return unicode(string)


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
  if type(value) not in [unicode, str]:
    value = str(value)
  try:
    existing_value = CONFIG.get(section, option)
  except ConfigParser.NoSectionError:
    CONFIG.add_section(section)
  except ConfigParser.NoOptionError:
    # If there's no such option, that's fine. We'll fix that in a sec.
    pass
  if not existing_value:
    if not config_path:
      config_path = get_config_path()
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
  token_path = get_data_path(TOKENS_FILENAME_FORMAT % user,
                             create_missing_dir=True)
  LOG.debug('Writing access token to ' + token_path)
  if os.path.exists(token_path):
    with open(token_path, 'rb') as token_file:
      try:
        token_dict = pickle.load(token_file)
      except (KeyError, IndexError), err:
        LOG.error(err)
        LOG.error('Failed to load token_file (may be corrupted?)')
        file_invalid = True
      except ImportError, err:
        LOG.error(err)
        LOG.info('You probably have been using different versions of gdata.')
        file_invalid = True
      else:
        file_invalid = False
    if file_invalid:
      _move_failed_token_file(token_path)
      token_dict = {}
  else:
    token_dict = {}
  token_dict[service] = token
  if token_path:
    with open(token_path, 'wb') as token_file:
      # Ensure only the owner of the file has read/write permission
      os.chmod(token_path, stat.S_IRUSR | stat.S_IWUSR)
      pickle.dump(token_dict, token_file)
  else:
    LOG.debug('Cannot save access token!')


def write_devkey(devkey):
  """Write the devkey to the youtube devkey file."""
  import stat
  key_path = get_data_path(DEVKEY_FILENAME)
  with open(key_path, 'w') as key_file:
    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
    key_file.write(devkey)
