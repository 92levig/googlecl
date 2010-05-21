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
import gdata.service


config = ConfigParser.ConfigParser()
_google_cl_dir = os.path.expanduser('~/.googlecl')
_preferences_filename = 'prefs'
_login_filename = 'creds'
_auth_tokens_filename = 'auths'


class BaseServiceCL(gdata.service.GDataService):

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
        gdata.service.GDataService.Delete(self, item.GetEditLink().href)
        
  def GetEntries(self, uri, title=None, converter=None):
    """Get a list of entries from a feed uri.
    
    Keyword arguments:
      uri: URI to get the feed from.
      title: String to use when looking for entries to return. Will be compared
             to entry.title.text, using regular expressions if self.use_regex.
             (Default None for all entries from feed)
      converter: Converter to use on the feed. If specified, will be passed into
                 the GetFeed method. If None (default), GetFeed will be called
                 without the converter argument being passed in.
                 
    Returns:
      List of entries.
    
    """
    if converter:
      f = self.GetFeed(uri, converter=converter)
    else:
      f = self.GetFeed(uri)
    if not title:
      return f.entry
    if self.use_regex:
      entries = [entry for entry in f.entry 
                 if entry.title.text and re.match(title,entry.title.text)]
    else:
      entries = [entry for entry in f.entry if title == entry.title.text]
    return entries

  def IsTokenValid(self, test_uri):
    """Check that the token being used is valid.
    
    Keyword arguments:
      test_uri: URI to pass to self.Get().
      
    Returns:
      True if Get was successful, False if Get raised an exception with the
      string 'Token invalid' in its body, and raises any other exceptions.
    
    """
    try:
      self.Get(test_uri)
    except gdata.service.RequestError as e:
      if e.args[0]['body'].find('Token invalid') != -1:
        return False
      else:
        raise
    else:
      return True
  
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
    except gdata.service.BadAuthentication as e:
      print e
    except gdata.service.CaptchaRequired:
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
    self.client_id = 'GoogleCL'
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
  
  def __init__(self, description, callback=None, required=[], optional=[],
               login_required=True, args_desc=''):
    """Constructor.
    
    Keyword arguments:
      description: Description of what the task does.
      callback: Function to use to execute task.
                (Default None, prints a message instead of running)
      required: Required options for the task. (Default [])
      optional: Optional options for the task. (Default [])
      login_required: If logging in with a username is required to do this task.
                If True, can typically ignore 'user' as a required attribute. 
                (Default True)
      args_desc: Description of what the arguments should be. 
                 (Default '', for no arguments necessary for this task)
      
    """
    if isinstance(required, basestring):
      required = [required]
    if isinstance(optional, basestring):
      optional = [optional]
    self.description = description
    self.run = callback or self._not_impl
    self.required = required
    self.optional = optional
    self.login_required = login_required
    # Take the "required" list, join all the terms by the following rules:
    # 1) if the term is a string, leave it.
    # 2) if the term is a list, join it with the ' OR ' string.
    # Then join the resulting list with ' AND '.
    if self.required:
      req_str = ' AND '.join(['('+' OR '.join(a)+')' if isinstance(a, list) \
                              else a for a in self.required])
    else:
      req_str = 'none'
    if self.optional:
      opt_str = '\tOptional: ' + str(self.optional)[1:-1].replace("'", '')
    else:
      opt_str = ''
    if args_desc:
      args_desc = '\tArguments: ' + args_desc
    self.usage = 'Requires: ' + req_str + opt_str + args_desc
    
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
    choices = [sublist for sublist in self.required
               if isinstance(sublist, list) and attribute in sublist]
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
      
  def _not_impl(self, *args):
    """Just use this as a place-holder for Task callbacks."""
    print 'Sorry, this task is not yet implemented!'


def entry_to_string(entry, style_list, delimiter, missing_field_value=None):
  """Return a useful string describing a gdata.data.GDEntry.
  
  Keyword arguments:
    entry: Entry to convert to string.
    style: List of strings that describe what the return string should be
           composed of. Valid style strings are:
           'title' - title of the entry (entry.title.text).
           'url' - treated as 'url-direct' or 'url-site' depending on
                   setting in preferences file.
           'url-site' - url of the site associated with the entry
                        (entry.GetHtmlLink().href).
           'url-direct' - url directly to the resource 
                          (entry.content.src).
           'author' - author of the entry 
                      (e.name.text for every e in entry.author).
           The difference between url-site and url-direct is best exemplified
           by a picasa PhotoEntry: 'url-site' gives a link to the photo in the
           user's album, 'url-direct' gives a link to the image url.
           If 'url-direct' is specified but is not applicable, 'url-site' is
           placed in its stead, and vice-versa.
    delimiter: String to use as the delimiter between fields.
    missing_field_value: If any of the styles for any of the entries are
                         invalid or undefined, put this in its place
                         (Default None to use "missing_field_value" config
                         option).
    
  
  """
  def _string_for_style(style, entry):
    if style == 'title' or style == 'name':
      return entry.title.text
    elif style[:3] == 'url':
      substyle = style[4:] or config.get('GENERAL', 'default_url_style')
      try:
        href = entry.GetHtmlLink().href
      except AttributeError:
        if not entry.GetHtmlLink():
          href = ''
        else:
          raise
      if substyle == 'direct':
        return entry.content.src or href
      else:
        return href or entry.content.src
    elif style == 'author' and entry.author:
      author_string = str([a.name.text for a in entry.author])[1:-1]
      author_string = author_string.replace("'", '')
      return author_string
    elif style == 'email':
      if hasattr(entry, 'email'):
        email_string = str([e.address for e in entry.email])[1:-1]
        email_string = email_string.replace("'", '')
      else:
        email_string = ''
      return email_string
    else:
      raise ValueError("'Unknown listing style: '" + style + "'")

  return_string = ''
  missing_field_value = missing_field_value or config.get('GENERAL',
                                                          'missing_field_value')
  for style in style_list:
    try:
      return_string += _string_for_style(style, entry) or missing_field_value
    except ValueError as e:
      print e.args + ' (Did not add entry for style ' + style + ')'
    except AttributeError as e:
      if e.args[0].find("'NoneType' object has no attribute") != -1:
        return_string += missing_field_value
      else:
        raise 
    return_string += delimiter
  return return_string.rstrip(delimiter)


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


def generate_tag_sets(tags):
  """Generate sets of tags based on a string.
  
  Keyword arguments:
    tags: Comma-separated list of tags. Tags with a '-' in front will be
          removed from each photo. A tag of '--' will delete all tags.
          A backslash in front of a '-' will keep the '-' in the tag.
          Examples:
            'tag1, tag2, tag3'      Add tag1, tag2, and tag3
            '-tag1, tag4, \-tag5'   Remove tag1, add tag4 and -tag5
            '--, tag6'              Remove all tags, then add tag6
  Returns:
    (remove_set, add_set, replace_tags) where...
      remove_set: set object of the tags to remove
      add_set: set object of the tags to add
      replace_tags: boolean indicating if all the old tags are removed
      
  """
  tags = tags.replace(', ', ',')
  tagset = set(tags.split(','))
  remove_set = set(tag[1:] for tag in tagset if tag[0] == '-')
  if '-' in remove_set:
    replace_tags = True
  else:
    replace_tags = False
  add_set = set()
  if len(remove_set) != len(tagset):
    # TODO: Can do this more cleanly with regular expressions?
    for tag in tagset:
      # Remove the escape '\' for calculation of 'add' set
      if tag[:1] == '\-':
        add_set.add(tag[1:])
      # Don't add the tags that are being removed
      elif tag[0] != '-':
        add_set.add(tag) 
  return (remove_set, add_set, replace_tags)


def get_list_style(section):
  try:
    return config.get(section, 'default_list_style').split(',')
  except ConfigParser.NoSectionError:
    return config.get('GENERAL', 'default_list_style').split(',')
  except ConfigParser.NoOptionError:
    return config.get('GENERAL', 'default_list_style').split(',')


def load_preferences():
  """Load preferences / configuration file.
  
  Sets up the global ConfigParser.ConfigParser, config.
  
  """
  def set_options():
    import picasa
    import docs
    """Ensure the config file has all of the configuration options."""
    # These may be useful to define at the module level, but for now,
    # keep them here.
    _options = {'editor': 'pico',
                'delimiter': ','}
    _picasa = {'access': 'public'}
    _general = {'regex': False,
               'delete_by_default': False,
               'delete_prompt': True,
               'tags_prompt': False,
               'use_default_username': True,
               'default_url_style': 'site',
               'default_list_style': 'title,url-site',
               'missing_field_value': 'N/A'}
    _docs = {'document_format': 'txt',
             'spreadsheet_format': 'xls',
             'presentation_format': 'ppt',
             'format': 'txt',
             'document_editor': 'vim',
             'spreadsheet_editor': 'openoffice.org',
             'presentation_editor': 'openoffice.org',
             'editor': 'nano'}
    CONFIG_DEFAULTS = {docs.SECTION_HEADER: _docs,
                       picasa.SECTION_HEADER: _picasa,
                       'GENERAL': _general,
                       'OPTION_DEFAULTS': _options}
    made_changes = False
    for section_name in CONFIG_DEFAULTS.keys():
      if not config.has_section(section_name):
        config.add_section(section_name)
      section = CONFIG_DEFAULTS[section_name]
      missing_opts = set(section.keys()) - set(config.options(section_name))
      if missing_opts:
        made_changes = True
      for opt in missing_opts:
        config.set(section_name, opt, section[opt])
    return made_changes
      
  if not os.path.exists(_google_cl_dir):
    os.makedirs(_google_cl_dir)
  pref_path = os.path.join(_google_cl_dir, _preferences_filename)
  if os.path.exists(pref_path):
    config.read(pref_path)
      
  made_changes = set_options()
  if made_changes:
    with open(pref_path, 'w') as pref_file:
      config.write(pref_file)


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


def read_auth_token(service):
  """Try to read an authorization token from a file.
  
  Keyword arguments:
    service: Service the token is for. E.g. picasa, docs, blogger.
  
  Returns:
    The authorization token, if it exists. If there is no authorization token,
    return NoneType.
  
  """
  token_path = os.path.join(_google_cl_dir, _auth_tokens_filename)
  if os.path.exists(token_path):
    with open(token_path, 'r') as token_file:
      token_dict = pickle.load(token_file)
    try:
      token = token_dict[service.lower()]
    except KeyError:
      print 'No token for ' + service
      return None
    else:
      return token
  else:
    return None


def remove_auth_token(service):
  """Remove an auth token for a particular service."""
  token_path = os.path.join(_google_cl_dir, _auth_tokens_filename)
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


def write_auth_token(service, token):
  """Write an authorization token to a file.
  
  Keyword arguments:
    service: Service the token is for. E.g. picasa, docs, blogger.
  
  """
  token_path = os.path.join(_google_cl_dir, _auth_tokens_filename)
  if os.path.exists(token_path):
    with open(token_path, 'r') as token_file:
      token_dict = pickle.load(token_file)
  else:
    token_dict = {}
  token_dict[service] = token 
  with open(token_path, 'w') as token_file:
    # Ensure only the owner of the file has read/write permission
    os.chmod(token_path, stat.S_IRUSR | stat.S_IWUSR)
    pickle.dump(token_dict, token_file)


def write_creds(email, password, cred_path):
  """Write the email/password to the credentials file."""
  with open(cred_path, 'w') as cred_file:
    # Ensure only the owner of the file has read/write permission
    os.chmod(cred_path, stat.S_IRUSR | stat.S_IWUSR)
    pickle.dump((email, password), cred_file)