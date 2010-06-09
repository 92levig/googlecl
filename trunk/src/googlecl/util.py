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


"""Utility functions for the Google command line tool"""


from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import ConfigParser
import getpass
import glob
import os
import pickle
import re
import stat
import time
import gdata.service


config = ConfigParser.ConfigParser()
_google_cl_dir = os.path.expanduser(os.path.join('~', '.googlecl'))
_preferences_filename = 'config'
_tokens_filename_format = 'access_tok_%s'
_devkey_filename = 'yt_devkey'
DATE_FORMAT = '%Y-%m-%d'


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

  def GetSingleEntry(self, uri, title=None, converter=None):
    """Return exactly one entry.
    
    Uses GetEntries to retrieve the entries, then asks the user to select one of
    them by entering a number.
    
    Keyword arguments:
      uri: URI to get feed from. See GetEntries.
      title: Title to match on. See GetEntries. (Default None).
      converter: Conversion function to apply to feed. See GetEntries.
    
    Returns:
      None if there were no matches, or one entry matching the given title.
    
    """
    entries = self.GetEntries(uri, title, converter)
    if not entries:
      return None
    elif len(entries) == 1:
      return entries[0]
    elif len(entries) > 1:
      print 'More than one match for title ' + (title or '')
      for num, entry in enumerate(entries):
        print '%i) %s' % (num, entry.title.text)
      selection = -1
      while selection < 0 or selection > len(entries)-1: 
        selection = int(raw_input('Please select one of the items by number: '))
      return entries[selection]

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
    except gdata.service.RequestError, e:
      if e.args[0]['body'].find('Token invalid') != -1:
        return False
      else:
        raise
    else:
      return True
  
  def RequestAccess(self):
    """Do all the steps involved with getting an OAuth access token.
    
    Return:
      True if access token was succesfully retrieved and set, otherwise False.
    
    """
    import gdata.auth
    # Installed applications do not have a pre-registration and so follow
    # directions for unregistered applications
    self.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                 consumer_key='anonymous',
                                 consumer_secret='anonymous')
    request_token = self.FetchOAuthRequestToken()
    auth_url = self.GenerateOAuthAuthorizationURL(request_token=request_token)
    junk = raw_input('Please log in at: ' + auth_url + ' then come back and'
                    + ' hit enter.')
    # This upgrades the token, and if successful, sets the access token
    try:
      self.UpgradeToOAuthAccessToken(request_token)
    except gdata.service.TokenUpgradeFailed:
      print 'Token upgrade failed! Could not get OAuth access token.'
      return False
    else:
      return True

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
    # To resolve Issue 367
    # http://code.google.com/p/gdata-python-client/issues/detail?id=367
    self.ssl = False
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
    style_list: List of strings that describe what the return string should be
           composed of. Valid style strings are:
           'title', 'name' - title of the entry (entry.title.text).
           'url' - treated as 'url-direct' or 'url-site' depending on
                   setting in preferences file.
           'url-site' - url of the site associated with the entry
                        (entry.GetHtmlLink().href).
           'url-direct' - url directly to the resource 
                          (entry.content.src).
           'author' - author of the entry (entry.author[:].name.text).
           'email' - email addresses of entry (entry.email[:].address),
           'where' - location associated with the entry
                     (entry.where[:].value_string).
           'when' - time of the entry
                    (entry.when[:].start_time - entry.when[:].end_time)
           'summary', 'description', 'desc' - Summary / caption / description
                    of the entry (entry.media.description.text or
                    entry.summary.text).
           'tags', 'labels' - Keywords / tags / labels of the entry
                              (entry.media.description.keywords.text or
                              entry.categories[:].term).
                               
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
  def _string_for_style(style, entry, join_string):
    # We can access attributes willy-nilly, and catch the NoneTypes later.
    value = ''
    if style == 'title' or style == 'name':
      value = entry.title.text
    elif style[:3] == 'url':
      substyle = style[4:] or config.get('GENERAL', 'url_style')
      try:
        href = entry.GetHtmlLink().href
      except AttributeError:
        if not entry.GetHtmlLink():
          href = ''
        else:
          raise
      if substyle == 'direct':
        value = entry.content.src or href
      else:
        value = href or entry.content.src
    elif style == 'author' and entry.author:
      author_string = str([a.name.text for a in entry.author])[1:-1]
      value = author_string.replace("'", '')
    elif style == 'email':
      if hasattr(entry, 'email'):
        email_string = str([e.address for e in entry.email])[1:-1]
        value= email_string.replace("'", '')
    elif style == 'when':
      start_time_data, end_time_data, freq = get_datetimes(entry)
      print_format = config.get('GENERAL', 'date_print_format')
      start_time = time.strftime(print_format, start_time_data)
      end_time = time.strftime(print_format, end_time_data)
      value = start_time + ' - ' + end_time
      if freq:
        if freq.has_key('BYDAY'):
          value += ' (' + freq['BYDAY'].lower() + ')'
        else:
          value += ' (' + freq['FREQ'].lower() + ')'
    elif style == 'where':
      value = join_string.join([w.value_string for w in entry.where
                                if w.value_string])
    elif style == 'summary' or style[:4] == 'desc':
      try:
        # Try to access the "default" description
        value = entry.media.description.text
      except:
        # If it's not there, try the summary attribute
        value = entry.summary.text
      else:
        if not value:
          # If the "default" description was there, but it was empty,
          # try the summary attribute.
          value = entry.summary.text
    elif style == 'tags' or style == 'labels':
      try:
        value = entry.media.description.keywords.text
      except:
        # Blogger uses categories.
        value = join_string.join([c.term for c in entry.category if c.term])
    else:
      raise ValueError("'Unknown listing style: '" + style + "'")
    return value

  return_string = ''
  missing_field_value = missing_field_value or config.get('GENERAL',
                                                          'missing_field_value')
  if not delimiter:
    delimiter = ','
  if delimiter.strip() == ',':
    join_string = ';'
  else:
    join_string = ','
  for style in style_list:
    value = ''
    try:
      # Get the value, replacing NoneTypes and empty strings
      # with the missing field value.
      value = _string_for_style(style, entry, join_string) or missing_field_value
    except ValueError, e:
      print e.args[0] + ' (Did not add value for style ' + style + ')'
    except AttributeError, e:
      if e.args[0].find("'NoneType' object has no attribute") != -1:
        return_string += missing_field_value
      else:
        raise
    # Ensure the delimiter won't appear in a non-delineation role.
    return_string += value.replace(delimiter, ' ') + delimiter
  
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


def get_config_option(section, option):
  """Return option from config file.
  
  Tries to retrieve <option> from the given section. If that fails, tries to
  retrieve the same option from the GENERAL section.
  
  Keyword arguments:
    section: Name of the section to initially try to retrieve the option from.
    option: Name of the option to retrieve.
  
  Returns:
    Value of the option if it exists in the prefs file, or None if it does not
    exist.
  
  """
  try:
    try:
      return config.get(section, option)
    except ConfigParser.NoSectionError:
      return config.get('GENERAL', option)
    except ConfigParser.NoOptionError:
      return config.get('GENERAL', option)
  except ConfigParser.NoOptionError:
    return None


def get_datetimes(cal_entry):
  """Get datetime objects for the start and end of the event specified by a
  calendar entry.
  
  Keyword arguments:
    cal_entry: A CalendarEventEntry.
  
  Returns:
    (start_time, end_time, freq) where
      start_time - datetime object of the start of the event.
      end_time - datetime object of the end of the event.
      freq - string that tells how often the event repeats (NoneType if the
           event does not repeat (does not have a gd:recurrence element)).
  
  """
  if cal_entry.recurrence:
    return parse_recurrence(cal_entry.recurrence.text)
  else:
    freq = None
    w = cal_entry.when[0]
    try:
      start_time_data = time.strptime(w.start_time[:-10],
                                      '%Y-%m-%dT%H:%M:%S')
      end_time_data = time.strptime(w.end_time[:-10],
                                    '%Y-%m-%dT%H:%M:%S')
    except ValueError, e:
      # Handle date format for all-day events
      if e.args[0].find('does not match format') != -1:
        start_time_data = time.strptime(w.start_time, '%Y-%m-%d')
        end_time_data = time.strptime(w.end_time, '%Y-%m-%d')
  return (start_time_data, end_time_data, freq)


def load_preferences():
  """Load preferences / configuration file.
  
  Sets up the global ConfigParser.ConfigParser, config.
  
  """
  def set_options():
    import googlecl.picasa
    import googlecl.docs
    """Ensure the config file has all of the configuration options."""
    # These may be useful to define at the module level, but for now,
    # keep them here.
    # REMEMBER: updating these means you need to update the CONFIG readme.
    _picasa = {'access': 'public'}
    _general = {'regex': 'False',
               'delete_by_default': 'False',
               'delete_prompt': 'True',
               'tags_prompt': 'False',
               'use_default_username': 'True',
               'url_style': 'site',
               'list_style': 'title,url-site',
               'missing_field_value': 'N/A',
               'date_print_format': '%b %d %H:%M'}
    _docs = {'document_format': 'txt',
             'spreadsheet_format': 'xls',
             'presentation_format': 'ppt',
             'format': 'txt',
             'spreadsheet_editor': 'openoffice.org',
             'presentation_editor': 'openoffice.org'}
    CONFIG_DEFAULTS = {googlecl.docs.SECTION_HEADER: _docs,
                       googlecl.picasa.SECTION_HEADER: _picasa,
                       'GENERAL': _general}
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
  config_path = os.path.join(_google_cl_dir, _preferences_filename)
  if os.path.exists(config_path):
    config.read(config_path)
  else:
    print 'Did not find config / preferences file at ' + config_path
  made_changes = set_options()
  if made_changes:
    with open(pref_path, 'w') as pref_file:
      config.write(pref_file)


def parse_recurrence(time_string):
  """Parse recurrence data found in event entry.
  
  Keyword arguments:
    time_string: Value of entry's recurrence.text field.
  
  Returns:
    Tuple of (start_time, end_time, frequency). All values are in the user's
    current timezone (I hope). start_time and end_time are datetime objects,
    and frequency is a dictionary mapping RFC 2445 RRULE parameters to their
    values. (http://www.ietf.org/rfc/rfc2445.txt, section 4.3.10)
  
  """
  # Google calendars uses a pretty limited section of RFC 2445, and I'm
  # abusing that here. This will probably break if Google ever changes how
  # they handle recurrence, or how the recurrence string is built.
  data = time_string.split('\n')
  start_time_string = data[0].split(':')[-1]
  start_time = time.strptime(start_time_string,'%Y%m%dT%H%M%S')
  
  end_time_string = data[1].split(':')[-1]
  end_time = time.strptime(end_time_string,'%Y%m%dT%H%M%S')
  
  freq_string = data[2][6:]
  freq_properties = freq_string.split(';')
  freq = {}
  for p in freq_properties:
    key, value = p.split('=')
    freq[key] = value
  return (start_time, end_time, freq)


def read_access_token(service, user):
  """Try to read an authorization token from a file.
  
  Keyword arguments:
    service: Service the token is for. E.g. 'picasa', 'docs', 'blogger'.
    user: Username / email the token is associated with.
  
  Returns:
    The access token, if it exists. If there is no access token,
    return NoneType.
  
  """
  token_path = os.path.join(_google_cl_dir, _tokens_filename_format % user)
  if os.path.exists(token_path):
    with open(token_path, 'r') as token_file:
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
  key_path = os.path.join(_google_cl_dir, _devkey_filename)
  devkey = None
  if os.path.exists(key_path):
    with open(key_path, 'r') as key_file:
      devkey = key_file.read().strip()
  return devkey


def remove_access_token(service, user):
  """Remove an auth token for a particular user and service."""
  token_path = os.path.join(_google_cl_dir, _tokens_filename_format % user)
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


def write_access_token(service, user, token):
  """Write an authorization token to a file.
  
  Keyword arguments:
    service: Service the token is for. E.g. 'picasa', 'docs', 'blogger'.
    user: Username / email the token is associated with.
  
  """
  token_path = os.path.join(_google_cl_dir, _tokens_filename_format % user)
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


def write_devkey(devkey):
  """Write the devkey to the youtube devkey file."""
  key_path = os.path.join(_google_cl_dir, _devkey_filename)
  with open(key_path, 'w') as key_file:
    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
    key_file.write(devkey)