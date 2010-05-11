"""
Utility functions for the Google command line tool

@author: Tom Miller
"""

import ConfigParser
import getpass
import glob
import os
import pickle
import re
import stat
from gdata.service import GDataService, BadAuthentication, CaptchaRequired


config = ConfigParser.ConfigParser()
_google_cl_dir = os.path.expanduser('~/.googlecl')
_preferences_filename = 'prefs'
_login_filename = 'creds'


class BaseServiceCL(GDataService):

  """Small extension of gdata.GDataService specific to the command line."""

  def Delete(self, entries, entry_type, delete_default):
    """Extends Delete to handle a list of entries.
    
    Keyword arguments:
      entries: List of entries to delete.
      entry_type: String describing the thing being deleted (e.g. album, post).
      delete_default: Whether or not the default action should be deletion.
      
    """
    if delete_default and self.prompt_for_delete:
      prompt_str = '(Y/n)'
    elif self.prompt_for_delete:
      prompt_str = '(y/N)'
    for item in entries:
      if self.prompt_for_delete:
        delete_str = raw_input('Are you SURE you want to delete %s "%s"? %s: ' % 
                               (entry_type, item.title.text, prompt_str))
        if not delete_str:
          delete = delete_default
        else:
          delete = delete_str.lower() == 'y'
      else:
        delete = True
      
      if delete:
        GDataService.Delete(self, item.GetEditLink().href)
        
  def GetEntries(self, uri, title=None):
    f = self.GetFeed(uri)
    if not title:
      return f.entry
    if self.use_regex:
      entries = [entry for entry in f.entry if re.match(title,entry.title.text)]
    else:
      entries = [entry for entry in f.entry if title == entry.title.text]
    return entries
  
  def Login(self, email, password):
    """Extends programmatic login.
    
    Keyword arguments:
      email: Email account to log in with.
      password: Un-encrypted password to log in with.
    
    Returns:
      Sets self.logged_in to True if login was a success. Otherwise, sets it
      to False.
    
    """
    self.logged_in = False
    if not (email and password):
      print ('You must give an email/password combo to log in with.')
      return
    
    self.email = email
    self.password = password
    
    try:
      self.ProgrammaticLogin()
    except BadAuthentication as e:
      print e
    except CaptchaRequired:
      print 'Too many failed logins; Captcha required.'
    else:
      self.logged_in = True
  
  def set_params(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Set constructor and basic parameters.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as album titles. (Default False)
      tags_prompt: Indicates if while inserting items, instance should prompt
                   for tags on each item. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting an item. (Default True)
              
    """
    self.source = 'GoogleCL'
    
    self.logged_in = False
    self.use_regex = regex
    self.prompt_for_tags = tags_prompt
    self.prompt_for_delete = delete_prompt
    

class Task(object):
  
  """A container of requirements.
  
  Each requirement matches up with one of the attributes of the option parser
  used to parse command line arguments. Requirements are given as lists.
  For example, if a task needs to have attr1 and attr2 and either attr3 or 4,
  the list would look like ['attr1', 'attr2', ['attr3', 'attr4']]
  
  """
  
  def __init__(self, required=[], optional=[], login_required=True):
    """Constructor.
    
    Keyword arguments:
      required: The required attributes for the task. (Default [])
      optional: The optional attributes for the task. Currently unused. 
                (Default [])
      login_required: If logging in with a username is required to do this task.
                If True, can typically ignore 'user' as a required attribute. 
                (Default True)
      
    """
    if isinstance(required, basestring):
      required = [required]
    if isinstance(optional, basestring):
      optional = [optional]
    self.required = required
    self.optional = optional
    self.login_required = login_required
    
  def mentions(self, attribute):
    """See if an attribute is optional or required."""
    return self.is_optional(attribute) or self.requires(attribute)
  
  def is_optional(self, attribute):
    """See if an attribute is optional"""
    # No list of lists in the optional fields
    if attribute in self.optional:
      return True
    return False
  
  def requires(self, attribute, options=None):
    """See if a attribute is required.
    
    Keyword arguments:
      attribute: Attribute in question.
      options: Object with attributes to check for. If provided, intelligently
               checks if the attribute is necessary, given the attributes
               already in options. (Default None)
    Returns:
      True if the attribute is required.
      False or [] if the attribute is never required
      If options is provided, a list of lists, where each sublist contains the
        name of the attribute that is required. For example, if either 'title'
        or 'query' is required, will return [['title','query']] 
    
    """
    # Get a list of all the sublists that contain attribute
    choices = [sublist for sublist in self.required if isinstance(sublist, list) and attribute in sublist]
    if options:
      if attribute in self.required:
        return not bool(getattr(options, attribute))
      if choices:
        for sublist in choices:
          for item in sublist:
            if getattr(options, item):
              return False
        return True
    else:
      if attribute in self.required:
        return True
      else:
        return choices


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
  def do_globbing(args, final_args_list):
    """Do filename expansion.
    
    Uses glob.glob to expand the default special characters of bash. Note that
    the command line will leave in arguments that do not expand to anything,
    unlike glob.glob. For example, entering 'myprogram.py total_nonsense*.txt'
    will pass through 'total_nonsense*.txt' as sys.argv[1].
    
    Keyword arguments:
      args: String, or list of strings, to be expanded.
      final_args_list: List that expanded arguments should be added to.
    
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
      do_globbing(command_string.strip().split(), final_args_list)
    
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
  """Try to log into a service via the client.
  
  Keyword arguments:
    client: Client for the service.
    email: E-mail used to log in. If '@my-mail.com' is not included,
           the domain is inferred. (Default None - will first check for a file
           containing email/password, or prompt for one)  
    password: Password used to authenticate the account given by email.
          (Default None - will first check for a file containing email/password,
          or prompt for one) 

  """
  got_creds_from_file= False
  if not email:
    (email, password) = read_creds()
    if email and password:
      got_creds_from_file = True
  if not email:
    email = raw_input('Enter your username: ')
  if not password:
    password = getpass.getpass('Enter your password: ')
      
  client.Login(email, password)
  cred_path = os.path.join(_google_cl_dir, _login_filename)
  if got_creds_from_file and not client.logged_in:
    os.remove(cred_path)
  elif not os.path.exists(cred_path) and client.logged_in:
    write_creds(email, password, cred_path)


def write_creds(email, password, cred_path):
  """Write the email/password to the credentials file."""
  with open(cred_path, 'w') as cred_file:
    # Ensure only the owner of the file has read/write permission
    os.chmod(cred_path, stat.S_IRUSR | stat.S_IWUSR)
    pickle.dump((email, password), cred_file)
  
  