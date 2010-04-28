#!/usr/bin/python
"""Main function for the Google command line utility.

Some terminology in use:
client -- the end user.
service -- the Google service being accessed (Picasa, translate, YouTube, etc.)
task -- what the client wants done by the service.

"""
import ConfigParser
import photos.service
import getpass
import glob
import optparse
import os
import pickle
import stat
import urllib


_google_cl_dir = os.path.expanduser('~/.googlecl')
_preferences_filename = 'prefs'
_login_filename = 'creds'
_config = ConfigParser.ConfigParser()


def expand_as_command_line(command_string):
  """Expand a string as if it was entered at the command line.
  
  Mimics the shell expansion of '~', file globbing, and quotation marks.
  For example, 'picasa post -a "My album" ~/photos/*.png' will return
  ['picasa', 'post', '-a', 'My album', '$HOME/photos/myphoto1.png', etc.]
  It will not treat apostrophes specially, or handle environment variables.
  
  Keyword arguments:
  command_string -- the string to be expanded.
  
  Returns: A list of strings that (mostly) matches sys.argv if command_string
    was entered on the command line.
  
  """ 
  def do_globbing(args, final_args_list):
    """Do filename expansion.
    
    Uses glob.glob to expand the default special characters of bash. Note that
    the command line will leave in arguments that do not expand to anything,
    unlike glob.glob. For example, entering 'myprogram.py total_nonsense*.txt'
    will pass through 'total_nonsense*.txt' as sys.argv[1].
    
    Keyword arguments:
    args -- string, or list of strings, to be expanded.
    final_args_list -- list that expanded arguments should be added to.
    
    Returns: Nothing, though final_args_list is modified.
    
    """
    if isinstance(args, basestring):
      expanded_str = glob.glob(args)
      if expanded_str:
        final_args_list.extend(expanded_str)
      else:
        final_args_list.append(args)
    else:
      for arg in args:
        expanded_arg = glob.glob(arg)
        if expanded_arg:
          final_args_list.extend(expanded_arg)
        else:
          final_args_list.append(arg)
        
  # End of do_globbing, begin expand_as_command_line
  if not command_string:
    return []
  
  # Sub in the home path.
  home_path = os.path.expanduser('~/')
  command_string = command_string.replace( ' ~/', ' ' + home_path)
  
  # Look for quotation marks
  quote_index = command_string.find('"')
  if quote_index == -1:
    args_list = command_string.split()
    final_args_list = []
    do_globbing(args_list, final_args_list)
    
  else:
    final_args_list = []
    while quote_index != -1:
      start = quote_index
      end = command_string.find('"', start+1)
      quoted_arg = command_string[start+1:end] 
      non_quoted_args = command_string[:start].split()
      
      # Only do filename expansion on non-quoted args!
      # do_globbing will modify final_args_list appropriately
      do_globbing(non_quoted_args, final_args_list) 
      final_args_list.append(quoted_arg)
      
      command_string = command_string[end+1:]
      if command_string:
        quote_index = command_string.find('"')
      else:
        quote_index = -1
        
    if command_string:
      do_globbing(command_string.strip(), final_args_list)
    
  return final_args_list
      
      
def is_supported_service(service):
  """Check to see if a service is supported."""
  if service.lower() == 'picasa':
    return True
  else:
    return False
  
  
def load_preferences():
  """Load preferences / configuration file.
  
  Sets up the global ConfigParser.ConfigParser, _config.
  
  """
  def set_options():
    """Ensure the config file has all of the configuration options."""
    made_changes = False
    if not _config.has_option('DEFAULT', 'regex'):
      _config.set('DEFAULT', 'regex', False)
      made_changes = True
    if not _config.has_option('DEFAULT', 'delete_by_default'):
      _config.set('DEFAULT', 'delete_by_default', False)
      made_changes = True
    if not _config.has_option('DEFAULT', 'delete_prompt'):
      _config.set('DEFAULT', 'delete_prompt', True)
      made_changes = True
    if not _config.has_option('DEFAULT', 'tags_prompt'):
      _config.set('DEFAULT', 'tags_prompt', False)
      made_changes = True
    if not _config.has_option('DEFAULT', 'access'):
      _config.set('DEFAULT', 'access', 'public')
      made_changes = True
    if not _config.has_option('DEFAULT', 'use_default_username'):
      _config.set('DEFAULT', 'use_default_username', False)
      made_changes = True
    return made_changes
  
  def validate_options():
    pub_values = ['public', 'private', 'protected']
    try:
      _config.getboolean('DEFAULT', 'regex')
      _config.getboolean('DEFAULT', 'delete_by_default')
      _config.getboolean('DEFAULT', 'delete_prompt')
      _config.getboolean('DEFAULT', 'tags_prompt')
      _config.getboolean('DEFAULT', 'use_default_username')
      if not _config.get('DEFAULT', 'access') in pub_values: 
        raise ValueError('"access" must be one of %s' % pub_values)
    except Exception as e:
      print 'Error in configuration file:', e
      return False
    else:
      return True
      
  if not os.path.exists(_google_cl_dir):
    os.makedirs(_google_cl_dir)
  pref_path = os.path.join(_google_cl_dir, _preferences_filename)
  if os.path.exists(pref_path):
    _config.read(pref_path)
      
  made_changes = set_options()
  if made_changes:
    with open(pref_path, 'w') as pref_file:
      _config.write(pref_file)
        
  return validate_options()
        
        
def print_help():
  """Print a help message."""
  print 'Welcome to the google-cl super alpha'
  print ('The only thing working so far is picasa, ', 
       'so give that a shot by entering ''picasa'' at the prompt')
  print ('Quitting also works, despite what your parents told you.',
       ' Enter ''quit'' to exit.') 


def requires_login(task):
  """Check if a task requires a client login.
  
  Keyword arguments:
  task -- the task to be performed.
  
  """
  login_tasks = ['create', 'delete', 'post']
  if task in login_tasks:
    return True
  else:
    return False
       
       
def run_interactive(parser):
  """Run an interactive shell for the google commands."""
  command_string = ''
  while not command_string == 'quit': 
    command_string = raw_input('> ')
    if not command_string:
      continue
    args_list = expand_as_command_line(command_string)
    (options, args) = parser.parse_args(args_list)
    if is_supported_service(args[0]):
      run_once(options, args)
    elif command_string == '?' or command_string == 'help':
      print_help()
    elif command_string != 'quit':
      print '> Enter "?" or "help" to print the help menu'
 
      
def run_once(options, args):
  """Run one command.
  
  Keyword arguments:
  options -- the options class as built and returned by optparse.
  args -- the arguments to google-cl, also as returned by optparse.
  
  """
  if len(args) < 2:
    print 'Must specify at least a service and a task!'
    return
  service = args[0]
  if not is_supported_service(service):
    print 'Service %s is not supported' % service
    return
  
  task = args[1]
  client = photos.service.PhotosService(_config.getboolean('DEFAULT', 'regex'),
                                        _config.getboolean('DEFAULT', 
                                                           'tags_prompt'),
                                        _config.getboolean('DEFAULT', 
                                                           'delete_prompt'))
   
  if requires_login(task):
    try_login(client, options.user, options.password)
    if not client.logged_in:
      print 'Failed to log on!'
      return
  
  if (not client.logged_in and not options.user and 
      _config.getboolean('DEFAULT', 'use_default_username')):
    cred_path = os.path.join(_google_cl_dir, _login_filename)
    (email, password) = client.LoadCreds(cred_path)
    options.user = email
    
  if options.summary and os.path.exists(os.path.expanduser(options.summary)):
    with open(options.summary, 'r') as summary_file:
      options.summary = summary_file.read()
      
  if task == 'create':
    if not options.title:
      title = raw_input('Enter a name for the album: ')
    else:
      title = options.title
      
    client.CreateAlbum(title, options.summary, 
                       date=options.date, photo_list=args[2:], 
                       access=_config.get('DEFAULT', 'access'))
      
  elif task == 'delete':
    client.DeleteAlbum(options.title,
                       delete_default=_config.getboolean('DEFAULT', 
                                                         'delete_by_default'))
    
  elif task == 'list':
    if not options.user:
      user = raw_input('Enter a username to get albums for: ')
    else:
      user = options.user
    entries = client.GetAlbum(user=user, title=options.title)
    for album in entries:
      print album.title.text
      
  elif task == 'post':
    if len(args) < 3:
      print 'Must provide photos to post!'
      return
     
    albums = client.GetAlbum(title=options.title)
    if len(albums) == 1:
      client.InsertPhotos(albums[0], args[2:], tags=options.tags)
    elif len(albums) > 1:
      print 'More than one album matches %s' % options.title
      upload_all = raw_input('Would you like to upload photos ' + 
                             'to each album? (Y/n) ')
      if not upload_all or upload_all.lower() == 'y':
        for album in albums:
          client.InsertPhotos(album, args[2:], tags=options.tags)
      
    else:
      print 'No albums found that match %s' % options.title
    
  elif task == 'get':
    if len(args) < 3:
      print 'Must provide destination of album(s)!'
      return
    base_path = args[2]
    
    if not options.user:
      user = raw_input('Enter a username to get albums for: ')
    else:
      user = options.user
      
    client.DownloadAlbum(base_path, user=user, title=options.title)
    
  else:
    print ('Sorry, task "%s" is currently unsupported for %s.' % 
         (task, service))
    
    
def setup_parser():
  """Set up the parser.
  
  Returns: optparse.OptionParser with options configured.
  
  """
  usage = "usage: %prog service task [options]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('-a', '--album', dest='title',
                    default='',
                    help='Title of the album')
  parser.add_option('-d', '--date', dest='date',
                    default='',
                    help='Date of the album in MM/DD/YYYY format.' + 
                    ' If omitted, uses today.')
  parser.add_option('-p', '--password', dest='password',
                    default='',
                    help='Password for the username specifed via -u option.')
  parser.add_option('-s', '--summary', dest='summary', 
                    default='',
                    help=('Description of the album, ' +
                          'or file containing the description.'))
  parser.add_option('-t',  '--tag', dest='tags',
                    default='',
                    help='Tags for photos, e.g. "Sunsets, Earth Day"')
  parser.add_option('-u', '--user', dest='user',
                    default='',
                    help=('Username to use for the task. Exact application ' +
                          'is task-dependent. If authentication is ' +
                          'necessary, this will force the user to specify a ' +
                          'password through a command line prompt or option.'))
 
  return parser


def try_login(client, email=None, password=None):
  """Try to use programmatic login to log into Picasa.
  
  Keyword arguments:
  client -- client for the Picasa service.
  email -- email used to log in to Picasa. If '@my-mail.com' is not included,
          '@gmail.com' is inferred. (Default None - will first check for a file
          containing email/password, or prompt for one)  
  password -- password used to authenticate the account given by 'email'.
          (Default None - will first check for a file containing email/password,
          or prompt for one) 
  
  Returns: True if login was successful, False otherwise.
  
  """
  cred_path = os.path.join(_google_cl_dir, _login_filename)
  if os.path.exists(cred_path) and not email:
    client.Login(credentials_path=cred_path)
    if not client.logged_in:
      os.remove(cred_path)
  else:
    if not email:
      email = raw_input('Enter your username: ')
    if not password:
      password = getpass.getpass('Enter your password: ')
      
    client.Login(email=email, password=password)
    if client.logged_in:
      with open(cred_path, 'w') as cred_file:
        os.chmod(cred_path, stat.S_IRUSR | stat.S_IWUSR)
        pickle.dump((email, password), cred_file)


def main():
  valid_prefs = load_preferences()
  if not valid_prefs:
    print 'Quitting...'
    return -1
  parser = setup_parser()
    
  (options, args) = parser.parse_args()
  if not args:
    try:
      run_interactive(parser)
    except KeyboardInterrupt:
      print ''
      print 'Quit via keyboard interrupt'
  else:
    if is_supported_service(args[0]):
      try:
        run_once(options, args)
      except KeyboardInterrupt:
        print ''
    else:
      print 'Unsupported service:', args[0]
     
     
if __name__ == '__main__':
  main()
