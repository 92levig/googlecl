#!/usr/bin/python
#
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


"""Main function for the Google command line tool, GoogleCL.

This program provides some functionality for a number of Google services from
the command line.

Example usage (omitting the initial "./google"):
  # Create a photo album with tags "Vermont" and name "Summer Vacation 2009"
  picasa create -n "Summer Vacation 2009" -t Vermont ~/photos/vacation2009/*

  # Post photos to an existing album
  picasa post -n "Summer Vacation 2008" ~/old_photos/*.jpg

  # Download another user's albums whose titles match a regular expression
  picasa get --user my.friend.joe --name ".*computer.*" ~/photos/joes_computer

  # Delete some posts you accidentally put up
  blogger delete -n "Silly post, number [0-9]*"

  # Post your latest film endeavor to YouTube
  youtube post --category Film --tag "Jane Austen, zombies" ~/final_project.mp4

Some terminology in use:
  service: The Google service being accessed (e.g. Picasa, Blogger, YouTube).
  task: What the client wants done by the service (e.g. post, get, delete).

"""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import glob
import logging
import optparse
import os
import sys
import googlecl

# Renamed here to reduce verbosity in other sections
safe_encode = googlecl.safe_encode
safe_decode = googlecl.safe_decode


VERSION = '0.9.11'

AVAILABLE_SERVICES = ['picasa', 'blogger', 'youtube', 'docs', 'contacts',
                      'calendar', 'finance']
LOG = logging.getLogger(googlecl.LOGGER_NAME)


class Error():
  """Base error for this module."""
  pass


def authenticate(service, client, section_header, options):
  """Set a (presumably valid) OAuth token for the client to use.

  The OAuth access token is retrieved by doing the following:
  1) Try to read an access token from file.
  2) If the token was read, and options."""

  # Only try to set the access token if we're not forced to authenticate.
  # XXX: logic in here is iffy. Don't bother checking access token if it's not
  # set
  if not options.force_auth:
    set_token = set_access_token(service, client)
    if set_token:
      LOG.debug('Successfully set token')
      skip_auth = options.skip_auth or \
                  googlecl.get_config_option(section_header, 'skip_auth',
                                             default=False, option_type=bool)
    else:
      LOG.debug('Failed to set token!')
      skip_auth = False
  else:
    LOG.debug('Forcing retrieval of new token')
    skip_auth = False

  if options.force_auth or not skip_auth:
    valid_token = check_access_token(service, client)
    if not valid_token:
      valid_token = retrieve_and_set_access_token(service,
                                                  client,
                                                  options.hostid)
    if valid_token:
      googlecl.set_missing_default(section_header, 'skip_auth',
                                   True, options.config)
      return True
    else:
      LOG.debug('valid_token evaulates to false,')
      return False
  else:
    # Already set an access token and we're not being forced to authenticate
    return True


def check_access_token(service_name, client):
  """Check that the set access token is valid, remove it if not.

  Args:
    service_name: str Name of the Google service being accessed.
    client: BaseCL instance doing the accessing.

  Returns:
    True if the token is valid, False otherwise. False will be returned
    whether or not the token was successfully removed with
    googlecl.remove_access_token().

  """
  try:
    token_valid = client.IsTokenValid()
  except AttributeError, err:
    # Attribute errors crop up when using different gdata libraries
    # but the same token.
    token_valid = False
    LOG.debug('Caught AttributeError: ' + str(err))
  if token_valid:
    LOG.debug('Token valid!')
    return True
  else:
    removed = googlecl.remove_access_token(service_name, client.email)
    if removed:
      LOG.debug('Removed invalid token')
    else:
      LOG.debug('Failed to remove invalid token')
    return False


# I don't know if this and shlex.split() can replace expand_as_command_line
# because of the behavior of globbing characters that are in ""
def expand_args(args, on_linesep, on_glob, on_homepath):
  """Expands arguments list.

  Args:
    on_linesep: Set True to split on occurrences of os.linesep. This is
        reasonably safe -- line separators appear to be escaped when given to
        Python on the command line.
    on_glob: Set True to glob expressions. May not be safe! For example, if user
        passes in "A*" (including the quotes) the * should NOT be expanded.
        Recommended only if sys.platform == 'win32'
    on_homepath: Set True to replace a leading ~/ with the user's home
        directory. May not be safe! Same situation as on_glob, described above.

  Returns:
    List of arguments that have been expanded
  """
  new_args = []
  for arg in args:
    temp_arg_list = None
    if on_linesep:
      temp_arg_list = arg.split(os.linesep)
    if on_homepath:
      if temp_arg_list:
        tmp = []
        for sub_arg in temp_arg_list:
          tmp.append(os.path.expanduser(sub_arg))
        temp_arg_list = tmp
      else:
        arg = os.path.expanduser(arg)
    # Globbing needs to happen last, otherwise it wont be able to find
    # any files.
    if on_glob:
      if temp_arg_list:
        tmp = []
        for sub_arg in temp_arg_list:
          tmp.extend(glob.glob(sub_arg))
        temp_arg_list = tmp
      else:
        temp_arg_list = glob.glob(arg)

    if temp_arg_list:
      new_args.extend(temp_arg_list)
    else:
      new_args.append(arg)
  return new_args


def expand_as_command_line(command_string):
  """Expand a string as if it was entered at the command line.

  Mimics the shell expansion of '~', file globbing, and quotation marks.
  For example, 'picasa post -a "My album" ~/photos/*.png' will return
  ['picasa', 'post', '-a', 'My album', '$HOME/photos/myphoto1.png', etc.]
  It will not treat apostrophes specially, or handle environment variables.

  Keyword arguments:
    command_string: String to be expanded.

  Returns:
    A list of strings that (mostly) matches sys.argv as if command_string
    was entered on the command line.

  """
  if not command_string:
    return []
  # Sub in the home path.
  home_path = os.path.expanduser('~/')
  # We may get a tilde that needs expansion in the middle of the string...
  # (Replace with the space to make sure we don't screw up /really/~/weird/path
  command_string = command_string.replace(' ~/', ' ' + home_path)
  # Or, if we're given options.src to expand, it could be the first few
  # characters.
  if command_string.startswith('~/'):
    command_string = home_path + command_string[2:]
  token_list = command_string.split()
  args_list = []
  while token_list:
    tmp = token_list.pop(0)
    start_of_quote = tmp[0] == '"'
    # A test to see if the end of a qutoed argument has been reached
    end_quote = lambda s: s[-1] == '"' and len(s) > 1 and s[-2] != '\\'
    while start_of_quote and not end_quote(tmp):
      if token_list:
        tmp += ' ' + token_list.pop(0)
      else:
        raise Error('Encountered end of string without finding matching "')
    if start_of_quote:
      # Add the resulting arg, stripping the " off
      args_list.append(tmp[1:-1])
    else:
      # Grab all the tokens in a row that end with unescaped \
      while tmp[-1] == '\\' and len(tmp) > 1 and tmp[-2] != '\\':
        if token_list:
          tmp = tmp[:-1] + ' ' + token_list.pop(0)
        else:
          raise Error('Encountered end of string ending in \\')

      expanded_args = glob.glob(tmp)
      if expanded_args:
        args_list.extend(expanded_args)
      else:
        args_list.append(tmp)
  return args_list


def fill_out_options(args, service_header, task, options):
  """Fill out required options via config file and command line prompts.

  If there are any required fields missing for a task, fill them in.
  This is attempted by checking the following sources, in order:
  1) The service_header section of the preferences file.
  2) The arguments list given to this function.
  3) Prompting the user.

  Note that 'user' and 'hostid' are special options -- they are always
  required, and they will skip step (2) when checking sources as mentioned
  above.

  Keyword arguments:
    args: list Arguments that may be options.
    service_header: str Name of the section in the config file for the
                    active service.
    task: Requirements of the task (see class googlecl.service.Task).
    options: Contains attributes that have been specified already, typically
             through options on the command line (see setup_parser()).

  Returns:
    Nothing, though options may be modified to hold the required fields.

  """
  def _retrieve_value(attr, service_header):
    """Retrieve value from config file or user prompt."""
    value = googlecl.get_config_option(service_header, attr)
    if value:
      return value
    else:
      return raw_input('Please specify ' + attr + ': ')

  if options.user is None:
    options.user = _retrieve_value('user', service_header)
  if options.hostid is None:
    options.hostid = _retrieve_value('hostid', service_header)
  missing_reqs = task.get_outstanding_requirements(options)
  LOG.debug('missing_reqs: ' + str(missing_reqs))

  for attr in missing_reqs:
    value = googlecl.get_config_option(service_header, attr)
    if not value:
      if args:
        value = args.pop(0)
      else:
        value = raw_input('Please specify ' + attr + ': ')
    setattr(options, attr, value)

  # Expand those options that might be a filename in disguise.
  max_file_size = 500000    # Value picked arbitrarily - no idea what the max
                            # size in bytes of a summary is.
  if options.summary and os.path.exists(os.path.expanduser(options.summary)):
    with open(options.summary, 'r') as summary_file:
      options.summary = summary_file.read(max_file_size)
  if options.devkey and os.path.exists(os.path.expanduser(options.devkey)):
    with open(options.devkey, 'r') as key_file:
      options.devkey = key_file.read(max_file_size).strip()


def get_hd_domain(username, default_domain='default'):
  """Return the domain associated with an email address.

  Intended for use with the OAuth hd parameter for Google.

  Keyword arguments:
    username: Username to parse.
    default_domain: Domain to set if '@suchandsuch.huh' is not part of the
                    username. Defaults to 'default' to specify a regular
                    Google account.

  Returns:
    String of the domain associated with username.

  """
  name, at_sign, domain = username.partition('@')
  # If user specifies gmail.com, it confuses the hd parameter (thanks, bartosh!)
  if domain == 'gmail.com' or domain == 'googlemail.com':
    return 'default'
  return domain or default_domain


def get_task_help(service, tasks):
  help = 'Available tasks for service ' + service + \
         ': ' + str(tasks.keys())[1:-1] + '\n'
  for task_name in tasks.keys():
    help += ' ' + task_name + ': ' + tasks[task_name].description + '\n'
    help += '  ' + tasks[task_name].usage + '\n\n'

  return help


def import_service(service):
  """Import vital information about a service.

  The goal of this function is to allow expansion to other "service" classes
  in the future. In the same way that the v2 and v3 API python library uses
  a module called "client", googlecl will do the same.

  Keyword arguments:
    service: Name of the service to import e.g. 'picasa', 'youtube'

  Returns:
    Tuple of service_class, tasks, and section header, where
      service_class is the class to instantiate for the service
      tasks is the dictionary mapping names to Task objects
      section_header is the name of the section in the config file that contains
                     options specific to the service.

  """
  LOG.debug('Your pythonpath: ' + str(os.environ.get('PYTHONPATH')))
  try:
    # Not sure why the fromlist keyword argument became necessary...
    package = __import__('googlecl.' + service, fromlist=['SECTION_HEADER'])
  except ImportError, err:
    LOG.error(err.args[0])
    LOG.error('Did you specify the service correctly? Must be one of ' +
              str(AVAILABLE_SERVICES)[1:-1])
    return (None, None, None)
  use_v1 = googlecl.get_config_option(package.SECTION_HEADER,
                                      'force_gdata_v1',
                                      default=False,
                                      option_type=bool)
  if use_v1:
    service_module = __import__('googlecl.' + service + '.service',
                                globals(), locals(), -1)
  else:
    try:
      service_module = __import__('googlecl.' + service + '.client',
                                  globals(), locals(), -1)
    except ImportError:
      service_module = __import__('googlecl.' + service + '.service',
                                  globals(), locals(), -1)
  return (service_module.SERVICE_CLASS,
          service_module.TASKS,
          package.SECTION_HEADER)


def print_help(service=None, tasks=None):
  """Print help messages to the screen.

  Keyword arguments:
    service: Service to get help on. (Default None, prints general help)
    tasks: Dictionary of tasks that can be done by the given service.
           (Default None)

  """
  if not service:
    print 'Welcome to the Google CL tool!'
    print '  Commands are broken into several parts: '
    print '    service, task, options, and arguments.'
    print '  For example, in the command'
    print '      "> picasa post --title "My Cat Photos" photos/cats/*"'
    print '  the service is "picasa", the task is "post", the single'
    print '  option is a title of "My Cat Photos", and the argument is the '
    print '  path to the photos.'
    print ''
    print '  The available services are '
    print str(AVAILABLE_SERVICES)[1:-1]
    print '  Enter "> help <service>" for more information on a service.'
    print '  Or, just "quit" to quit.'
  else:
    print get_task_help(service, tasks)


def retrieve_and_set_access_token(service_name, client, hostid):
  """Request a new access token from Google, set it upon retrieval.

  The token will not be written to file if it was granted for an account
  other than the one specified by client.email. Instead, a False value will
  be returned.

  Args:
    service_name: str Name of the Google service being accessed.
    client: BaseCL instance doing the accessing.
    hostid: str Identifier for the host machine. Used for token request.

  Returns:
    True if the token was retrieved and written to file. False otherwise.

  """
  domain = get_hd_domain(client.email)
  if client.RequestAccess(domain, hostid):
    authorized_account = client.get_email()
    # Only write the token if it's for the right user.
    if verify_email(client.email, authorized_account):
      # token is saved in client.auth_token for GDClient,
      # client.current_token for GDataService.
      googlecl.write_access_token(service_name,
                                  client.email,
                                  client.auth_token or client.current_token)
      return True
    else:
      LOG.error('You specified account ' + client.email +
                ' but granted access for ' + authorized_account + '.' +
                ' Please log out of ' + authorized_account +
                ' and grant access with ' + client.email + '.')
  else:
    LOG.error('Failed to get valid access token!')
  return False


def run_interactive(parser):
  """Run an interactive shell for the google commands.

  Keyword arguments:
    parser: Object capable of parsing a list of arguments via parse_args.

  """
  history_file = googlecl.get_data_path(googlecl.HISTORY_FILENAME)
  try:
    import readline
    try:
      readline.read_history_file(history_file)
    except EnvironmentError:
      LOG.debug('Could not read history file.')
  except ImportError:
    LOG.debug('Could not import readline module.')

  while True:
    try:
      command_string = raw_input('> ')
      if command_string.startswith('python '):
        LOG.info('HINT: No need to include "python" in interactive mode')
        command_string = command_string.replace('python ', '', 1)
      if command_string.startswith('google '):
        LOG.info('HINT: No need to include "google" in interactive mode')
        command_string = command_string.replace('google ', '', 1)
      if not command_string:
        continue
      elif command_string == '?':
        print_help()
      elif command_string == 'quit':
        break
      else:
        try:
          args_list = expand_as_command_line(command_string)
        except Error, err:
          LOG.error(err)
          continue
        (options, args) = parser.parse_args(args_list)
        setup_logger(options)
        run_once(options, args)
    except (KeyboardInterrupt, ValueError), err:
      # It would be nice if we could simply unregister or reset the
      # signal handler defined in the initial if __name__ block.
      # Windows will raise a KeyboardInterrupt, GNU/Linux seems to also
      # potentially raise a ValueError about I/O operation.
      if isinstance(err, ValueError) and \
         str(err).find('I/O operation on closed file') == -1:
        raise err
      print ''
      print 'Quit via keyboard interrupt'
      break
    except EOFError:
      print ''
      break
    except SystemExit:
      # optparse.OptParser prints the usage statement and calls
      # sys.exit when there are any option errors.
      # Printing usage good, SystemExit bad. So catch it and do nothing.
      pass
    except BaseException:
      from traceback import print_exc
      print_exc()
  if 'readline' in sys.modules:
    readline.write_history_file(history_file)


def run_once(options, args):
  """Run one command.

  Keyword arguments:
    options: Options instance as built and returned by optparse.
    args: Arguments to GoogleCL, also as returned by optparse.

  """
  try:
    service = args.pop(0)
    task_name = args.pop(0)
  except IndexError:
    if service == 'help':
      print_help()
    else:
      LOG.error('Must specify at least a service and a task!')
    return

  if service == 'help':
    service_class, tasks, section_header = import_service(task_name)
    if tasks:
      print_help(task_name, tasks)
      return
  else:
    service_class, tasks, section_header = import_service(service)
  if not service_class:
    return

  client = service_class()
  # Activate debugging output from HTTP requests. "service" clients only!
  # "client" versions need to set self.http_client.debug in their own __init__
  client.debug = googlecl.get_config_option(section_header,
                                            'debug',
                                            default=options.debug,
                                            option_type=bool)
  # XXX: Not the best place for this.
  if hasattr(client, 'http_client'):
    client.http_client.debug = client.debug
  try:
    task = tasks[task_name]
    task.name = task_name
  except KeyError:
    LOG.error('Did not recognize task, please use one of ' + \
              str(tasks.keys()))
    return

  if 'devkey' in task.required:
    # If a devkey is required, and there is none specified via an option
    # BEFORE fill_out_options, insert the key from file or the key given
    # to GoogleCL.
    # You can get your own key at http://code.google.com/apis/youtube/dashboard
    if not options.devkey:
      options.devkey = googlecl.read_devkey() or 'AI39si4d9dBo0dX7TnGyfQ68bNiKfEeO7wORCfY3HAgSStFboTgTgAi9nQwJMfMSizdGIs35W9wVGkygEw8ei3_fWGIiGSiqnQ'

  # fill_out_options will read the key from file if necessary, but will not set
  # it since it will always get a non-empty value beforehand.
  fill_out_options(args, section_header, task, options)
  client.email = options.user

  # Set missing defaults, even if the authentication step later on fails.
  googlecl.set_missing_default(section_header, 'user',
                               client.email, options.config)
  if options.blog:
    googlecl.set_missing_default(section_header, 'blog',
                                 options.blog, options.config)
  if options.devkey:
    client.developer_key = options.devkey
    # This may save an invalid dev key -- it's up to the user to specify a
    # valid dev key eventually.
    # TODO: It would be nice to make this more efficient.
    googlecl.write_devkey(options.devkey)

  # Unicode-ize options and args
  for attr_name in dir(options):
    attr = getattr(options, attr_name)
    if not attr_name.startswith('_') and isinstance(attr, str):
      setattr(options, attr_name, safe_decode(attr, googlecl.TERMINAL_ENCODING))
  if args:
    args = [safe_decode(string, googlecl.TERMINAL_ENCODING) for string in args]

  # Expand options.src. The goal is to expand things like
  # --src=~/Photos/album1/* (which does not normally happen)
  # XXX: This ought to be in fill_out_options(), along with unicode-ize above.
  if options.src:
    expanded_args = glob.glob(options.src)
    if expanded_args:
      options.src = expanded_args
    else:
      options.src = [options.src]
  else:
    options.src = []

  # Take a gander at the options filled in.
  if LOG.getEffectiveLevel() == logging.DEBUG:
    import inspect
    for attr_name in dir(options):
      if not attr_name.startswith('_'):
        attr = getattr(options, attr_name)
        if attr is not None and not inspect.ismethod(attr):
          LOG.debug(safe_encode('Option ' + attr_name + ': ' + unicode(attr)))
  LOG.debug(safe_encode('args: ' + unicode(args)))

  authenticated = authenticate(service, client, section_header, options)

  if authenticated:
    task.run(client, options, args)
  else:
    LOG.debug('Authentication failed, exiting run_once')


def set_access_token(service_name, client):
  """Read an access token from file and set it to be used by the client.

  Args:
    service_name: str Name of the Google service being accessed.
    client: BaseCL instance doing the accessing.

  Returns:
    True if the token was read and set, False otherwise.

  """
  try:
    token = googlecl.read_access_token(service_name, client.email)
  except (KeyError, IndexError):
    LOG.warning('Token file appears to be corrupted. Not using.')
  else:
    if token:
      LOG.debug('Loaded token from file')
      client.SetOAuthToken(token)
      return True
    else:
      LOG.debug('read_access_token evaluated to False')
  return False


def setup_logger(options):
  """Setup the global (root, basic) configuration for logging."""
  msg_format = '%(message)s'
  if options.debug:
    level = logging.DEBUG
    msg_format = '%(levelname)s:%(name)s:%(message)s'
  elif options.verbose:
    level = logging.DEBUG
  elif options.quiet:
    level = logging.ERROR
  else:
    level = logging.INFO
  # basicConfig does nothing if it's been called before
  # (e.g. in run_interactive loop)
  logging.basicConfig(level=level, format=msg_format)
  # Redundant for single-runs, but necessary for run_interactive.
  LOG.setLevel(level)
  # XXX: Inappropriate location (style-wise).
  if options.debug or options.verbose:
    import gdata
    LOG.debug('Gdata will be imported from ' + gdata.__file__)


def setup_parser():
  """Set up the parser.

  Returns:
    optparse.OptionParser with options configured.

  """
  available_services = '[' + '|'.join(AVAILABLE_SERVICES) + ']'
  # NOTE: Usage string formatted to work with help2man.  After changing it,
  # please run:
  # 'help2man -N -n "command-line access to (some) Google services" \
  #  -i ../man/examples.help2man  ./google > google.1'
  # then 'man ./google.1' and make sure the generated manpage still looks
  # reasonable.  Then save it to man/google.1
  usage = ('Usage: %prog ' + available_services + ' TASK [options]\n'
           '\n'
           'This program provides command-line access to\n'
           '(some) google services via their gdata APIs.\n'
           'Called without a service name, it starts an interactive session.\n'
           '\n'
           'NOTE: GoogleCL will interpret arguments as required options in the\n'
           'order they appear in the descriptions below, excluding options\n'
           'set in the configuration file and non-primary terms in '
           'parenthesized\n'
           'OR groups. For example:\n'
           '\n'
           '\t$ google picasa get my_album .\n'
           'is interpreted as "google picasa get --title=my_album --dest=.\n'
           '\n'
           '\t$ google contacts list john\n'
           'is interpreted as "$ google contacts list '
           '--fields=<config file def> --title=john --delimiter=,"\n'
           '(only true if you have not removed the default definition in the '
           'config file!)\n'
           '\n'
           '\t$ google docs get my_doc .\n'
           'is interpreted as "$ google docs get --title=my_doc --dest=.\n'
           '(folder is NOT set, since the title option is satisfied first.)\n\n')

  # XXX: If we're going to bother doing an __import__ of all the modules, we
  # might as well reuse the one the user actually wants to use.
  for service in AVAILABLE_SERVICES:
    service_module = __import__('googlecl.' + service + '.service',
                                globals(), locals(), -1)
    if service_module:
      usage += get_task_help(service, service_module.TASKS) + '\n'

  parser = optparse.OptionParser(usage=usage, version='%prog ' + VERSION)
  parser.add_option('--access', dest='access',
                    help='Specify access/visibility level of an upload')
  parser.add_option('--blog', dest='blog',
                    help='Blogger only - specify a blog other than your' +
                    ' primary.')
  parser.add_option('--cal', dest='cal',
                    help='Calendar only - specify a calendar other than your' +
                    ' primary.')
  parser.add_option('-c', '--category', dest='category',
                    help='YouTube only - specify video categories' +
                    ' as a comma-separated list, e.g. "Film, Travel"')
  parser.add_option('--commission', dest='commission',
                    help=("Finance only - specify commission for transaction"))
  parser.add_option('--config', dest='config',
                    help='Specify location of config file.')
  parser.add_option('--currency', dest='currency',
                    help=("Finance only - specify currency for portfolio"))
  parser.add_option('--devtags', dest='devtags',
                    help='YouTube only - specify developer tags' +
                    ' as a comma-separated list.')
  parser.add_option('--devkey', dest='devkey',
                    help='YouTube only - specify a developer key')
  parser.add_option('-d', '--date', dest='date',
                    help=('Calendar only - date of the event to add/look for. '
                          'Can also specify a range with a comma.\n'
                          'Picasa only - sets the date of the album\n'
                          'Finance only - transaction creation date'))
  parser.add_option('--debug', dest='debug',
                    action='store_true',
                    help=('Enable all debugging output, including HTTP data'))
  parser.add_option('--delimiter', dest='delimiter', default=',',
                    help='Specify a delimiter for the output of the list task.')
  parser.add_option('--dest', dest='dest',
                    help=('Destination. Typically, where to save data being'
                          ' downloaded.'))
  parser.add_option('--draft', dest='access',
                    action='store_const', const='draft',
                    help=('Blogger only - post as a draft. Shorthand for '
                          '--access=draft'))
  parser.add_option('--editor', dest='editor',
                    help='Docs only - editor to use on a file.')
  parser.add_option('--fields', dest='fields',
                    help='Fields to list with list task.')
  parser.add_option('-f', '--folder', dest='folder',
                    help='Docs only - specify folder(s) to upload to '+
                    '/ search in.')
  parser.add_option('--force-auth', dest='force_auth',
                    action='store_true',
                    help='Force validation step for re-used access tokens' +
                         ' (Overrides --skip-auth).')
  parser.add_option('--format', dest='format',
                    help='Docs only - format to download documents as.')
  parser.add_option('--hostid', dest='hostid',
                    help='Label the machine being used.')
  parser.add_option('-n', '--title', dest='title',
                    help='Title of the item')
  parser.add_option('--no-convert', dest='convert',
                    action='store_false', default=True,
                    help='Google Apps Premier only - do not convert the file' +
                    ' on upload. (Else converts to native Google Docs format)')
  parser.add_option('--notes', dest='notes',
                    help=("Finance only - specify notes for transaction"))
  parser.add_option('-o', '--owner', dest='owner',
                    help=('Username or ID of the owner of the resource. ' +
                          'For example,' +
                          " 'picasa list-albums -o bob' to list bob's albums"))
  parser.add_option('--price', dest='price',
                    help=("Finance only - specify price for transaction"))
  parser.add_option('-q', '--query', dest='query',
                    help=('Full text query string for specifying items.'
                          + ' Searches on titles, captions, and tags.'))
  parser.add_option('--quiet', dest='quiet',
                    action='store_true',
                    help='Print only prompts and error messages')
  parser.add_option('--reminder', dest='reminder',
                    help=("Calendar only - specify time for added event's " +
                          'reminder, e.g. "10m", "3h", "1d"'))
  parser.add_option('--shares', dest='shares',
                    help=("Finance only - specify amount of shares " +
                          "for transaction"))
  parser.add_option('--skip-auth', dest='skip_auth',
                    action='store_true',
                    help='Skip validation step for re-used access tokens.')
  parser.add_option('--src', dest='src',
                    help='Source. Typically files to upload.')
  parser.add_option('-s', '--summary', dest='summary',
                    help=('Description of the upload, ' +
                          'or file containing the description.'))
  parser.add_option('-t',  '--tags', dest='tags',
                    help='Tags for item, e.g. "Sunsets, Earth Day"')
  parser.add_option('--ticker', dest='ticker',
                    help=("Finance only - specify ticker"))
  parser.add_option('--ttype', dest='ttype',
                    help=("Finance only - specify transaction type, " +
                          'e.g. "Bye", "Sell", "Buy to Cover", "Sell Short"'))
  parser.add_option('--txnid', dest='txnid',
                    help=("Finance only - specify transaction id"))
  parser.add_option('-u', '--user', dest='user',
                    help='Username to log in with for the service.')
  parser.add_option('-v', '--verbose', dest='verbose',
                    action='store_true',
                    help='Print all messages.')
  return parser


def verify_email(given_account, authorized_account):
  """Make sure user didn't clickfest his/her way into a mistake.

  Keyword arguments:
    given_account: String of account specified by the user to GoogleCL,
                   probably by options.user. If domain is not included,
                   assumed to be 'gmail.com'
    authorized_account: Account returned by client.get_email(). Must
                        include domain!

  Returns:
    True if given_account and authorized_account match, False otherwise.

  """
  if authorized_account.find('@') == -1:
    raise Exception('authorized_account must include domain!')
  if given_account.find('@') == -1:
    given_account += '@gmail.com'
  return given_account == authorized_account


def main():
  """Entry point for GoogleCL script."""
  parser = setup_parser()
  (options, args) = parser.parse_args()
  setup_logger(options)
  if not googlecl.load_preferences(options.config):
    if options.config:
      LOG.warning('Could not read config file at ' + options.config)
    return
  if not args:
    run_interactive(parser)
  else:
    is_windows = sys.platform == 'win32'
    args = expand_args(args, True, is_windows, is_windows)
    try:
      run_once(options, args)
    except KeyboardInterrupt:
      print ''


def exit_from_int(*args):
  """Handler for SIGINT signal."""
  print ''
  exit(0)


if __name__ == '__main__':
  import signal
  signal.signal(signal.SIGINT, exit_from_int)
  main()
