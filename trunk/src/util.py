import ConfigParser
import getpass
import glob
import os
import pickle
import stat


config = ConfigParser.ConfigParser()
_google_cl_dir = os.path.expanduser('~/.googlecl')
_preferences_filename = 'prefs'
_login_filename = 'creds'


def expand_as_command_line(command_string):
  """Expand a string as if it was entered at the command line.
  
  Mimics the shell expansion of '~', file globbing, and quotation marks.
  For example, 'picasa post -a "My album" ~/photos/*.png' will return
  ['picasa', 'post', '-a', 'My album', '$HOME/photos/myphoto1.png', etc.]
  It will not treat apostrophes specially, or handle environment variables.
  
  Keyword arguments:
    command_string: The string to be expanded.
  
  Returns: 
    A list of strings that (mostly) matches sys.argv as if command_string
    was entered on the command line.
  
  """ 
  def do_globbing(args, final_args_list):
    """Do filename expansion.
    
    Uses glob.glob to expand the default special characters of bash. Note that
    the command line will leave in arguments that do not expand to anything,
    unlike glob.glob. For example, entering 'myprogram.py total_nonsense*.txt'
    will pass through 'total_nonsense*.txt' as sys.argv[1].
    
    Keyword arguments:
      args: String, or list of strings, to be expanded.
      final_args_list: The list that expanded arguments should be added to.
    
    Returns:
      Nothing, though final_args_list is modified.
    
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
        
  # End of do_globbing(), begin expand_as_command_line()
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


def load_preferences():
  """Load preferences / configuration file.
  
  Sets up the global ConfigParser.ConfigParser, config.
  
  """
  def set_options():
    """Ensure the config file has all of the configuration options."""
    made_changes = False
    if not config.has_option('DEFAULT', 'regex'):
      config.set('DEFAULT', 'regex', False)
      made_changes = True
    if not config.has_option('DEFAULT', 'delete_by_default'):
      config.set('DEFAULT', 'delete_by_default', False)
      made_changes = True
    if not config.has_option('DEFAULT', 'delete_prompt'):
      config.set('DEFAULT', 'delete_prompt', True)
      made_changes = True
    if not config.has_option('DEFAULT', 'tags_prompt'):
      config.set('DEFAULT', 'tags_prompt', False)
      made_changes = True
    if not config.has_option('DEFAULT', 'access'):
      config.set('DEFAULT', 'access', 'public')
      made_changes = True
    if not config.has_option('DEFAULT', 'use_default_username'):
      config.set('DEFAULT', 'use_default_username', False)
      made_changes = True
    return made_changes
  
  def validate_options():
    """Ensure that the config file's options are valid."""
    pub_values = ['public', 'private', 'protected']
    try:
      config.getboolean('DEFAULT', 'regex')
      config.getboolean('DEFAULT', 'delete_by_default')
      config.getboolean('DEFAULT', 'delete_prompt')
      config.getboolean('DEFAULT', 'tags_prompt')
      config.getboolean('DEFAULT', 'use_default_username')
      if not config.get('DEFAULT', 'access') in pub_values: 
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
    config.read(pref_path)
      
  made_changes = set_options()
  if made_changes:
    with open(pref_path, 'w') as pref_file:
      config.write(pref_file)
        
  return validate_options()


def read_creds():
  """Return the email/password found in the credentials file."""
  cred_path = os.path.join(_google_cl_dir, _login_filename)
  if os.path.exists(cred_path):
    with open(cred_path, 'r') as cred_file:
      (email, password) = pickle.load(cred_file)
  else:
    email = None
    password = None
  return (email, password)


def try_login(client, email=None, password=None):
  """Try to use programmatic login to log into Picasa.
  
  Keyword arguments:
    client: Client for the Picasa service.
    email: E-mail used to log in to Picasa. If '@my-mail.com' is not included,
          '@gmail.com' is inferred. (Default None - will first check for a file
          containing email/password, or prompt for one)  
    password: Password used to authenticate the account given by 'email'.
          (Default None - will first check for a file containing email/password,
          or prompt for one) 
  
  Returns:
    True if login was successful, False otherwise.
  
  """
  
  if not email:
    (email, password) = read_creds()
  if not email:
    email = raw_input('Enter your username: ')
  if not password:
    password = getpass.getpass('Enter your password: ')
      
  client.Login(email, password)
  cred_path = os.path.join(_google_cl_dir, _login_filename)
  if os.path.exists(cred_path) and not client.logged_in:
    os.remove(cred_path)
  elif not os.path.exists(cred_path) and client.logged_in:
    write_creds(email, password, cred_path)


def write_creds(email, password, cred_path):
  """Write the email/password to the credentials file."""
  with open(cred_path, 'w') as cred_file:
    os.chmod(cred_path, stat.S_IRUSR | stat.S_IWUSR)
    pickle.dump((email, password), cred_file)
  
  