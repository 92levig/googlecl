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
    args -- list of strings, or string, to be expanded.
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
  if not os.path.exists(_google_cl_dir):
    os.makedirs(_google_cl_dir)
  pref_path = os.path.join(_google_cl_dir, _preferences_filename)
  if os.path.exists(pref_path):
    _config.read(pref_path)
  else:
    _config.set('DEFAULT', 'regex', False)
    with open(pref_path, 'w') as pref_file:
      _config.write(pref_file)
      
        
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
  service = args[0]
  if not is_supported_service(service):
    print 'Service %s is not supported' % service
    return
  
  task = args[1]
  client = photos.service.PhotosService()
   
  if requires_login(task):
    loggedOn = try_login(client)
    if not loggedOn:
      print 'Failed to log on, exiting'
      exit()
      
  if task == 'create':
    if len(args) >= 3:
      client.CreateAlbum(options.title, options.summary, args[2:])
    else:    
      client.CreateAlbum(options.title, options.summary, [])
      
  elif task == 'delete':
    client.DeleteAlbum(options.title, 
               regex=_config.getboolean('DEFAULT', 'regex'))
    
  elif task == 'list':
    user = raw_input('Enter a username to get albums for: ')
    entries = client.GetAlbum(user=user,
                              title=options.title,
                              regex=_config.getboolean('DEFAULT', 'regex'))
    for album in entries:
      print album.title.text
      
  elif task == 'post':
    if len(args) < 3:
      print 'Must provide photos to post!'
      return
     
    albums = client.GetAlbum(title=options.title, 
                             regex=_config.getboolean('DEFAULT', 'regex'))
    if albums:
      client.InsertPhotos(albums[0], args[2:])
    else:
      print 'No albums found that match %s' % options.title
    
  else:
    print ('Sorry, task "%s" is currently unsupported for %s.' % 
         (task, service))
    
    
def setup_parser():
  """Set up the parser.
  
  Returns: optparse.OptionParser with options configured.
  
  """
  usage = "usage: %prog service [options]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('-a', '--album', dest='title',
                    default='Boring Album Title',
                    help='Title of the album')
  parser.add_option('-d', '--date', dest='date',
                    help='Date of the album (if omitted, uses today).')
  parser.add_option('-s', '--summary', dest='summary', 
                    default='I am too lazy to summarize this album.',
                    help=('Description of the album, ' +
                          'or file containing the description.'))
  parser.add_option('-t', '--title', dest='title',
                    help='Title of the album')
  return parser


def try_login(client):
  """Try to use programmatic login to log into Picasa.
  
  Keyword arguments:
  client -- client for the Picasa service.
  
  Returns: True if login was successful, False otherwise.
  
  """
  cred_path = os.path.join(_google_cl_dir, _login_filename)
  (email, password, used_file) = client.Login(cred_path)
  if used_file and not email:
    os.remove(cred_path)
  if email and password and not used_file:
    with open(cred_path, 'w') as cred_file:
      os.chmod(cred_filename, stat.S_IRUSR | stat.S_IWUSR)
      pickle.dump((email, password), cred_file)
  return bool(email) and bool(password)  


def main():
  load_preferences()
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
