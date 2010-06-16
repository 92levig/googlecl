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


import gdata.service
import googlecl
import re


DATE_FORMAT = '%Y-%m-%d'


class Error(Exception):
  """Base error for GoogleCL exceptions."""
  pass


class BaseServiceCL(gdata.service.GDataService):

  """Extension of gdata.GDataService specific to GoogleCL."""

  def _set_params(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Set some basic attributes common to all instances."""
    # Because each new xxxServiceCL class should use the more specific
    # superclass's __init__ function, don't define one here.
    self.source = 'GoogleCL'
    self.client_id = 'GoogleCL'
    # To resolve Issue 367
    # http://code.google.com/p/gdata-python-client/issues/detail?id=367
    self.ssl = False
    
    # Some new attributes, not inherited.
    self.logged_in = False
    self.use_regex = regex
    self.prompt_for_tags = tags_prompt
    self.prompt_for_delete = delete_prompt

  def delete(self, entries, entry_type, delete_default):
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
        try:
          gdata.service.GDataService.Delete(self, item.GetEditLink().href)
        except gdata.service.RequestError, err:
          print 'Could not delete event: ' + err[0]['body']

  Delete = delete

  def get_entries(self, uri, title=None, converter=None, max_results=1000):
    """Get a list of entries from a feed uri.
    
    Keyword arguments:
      uri: URI to get the feed from.
      title: String to use when looking for entries to return. Will be compared
             to entry.title.text, using regular expressions if self.use_regex.
             (Default None for all entries from feed)
      converter: Converter to use on the feed. If specified, will be passed into
                 the GetFeed method. If None (default), GetFeed will be called
                 without the converter argument being passed in.
      max_results: Value of the max-results query parameter to set on the uri.
                   This will NOT override an existing value, if it was somehow
                   set prior to this function call. Note that not all
                   services will support this, and silently fail to enforce
                   the limit. Default 1000.
                 
    Returns:
      List of entries.
    
    """
    if uri.find('?') == -1:
      uri += '?max-results=' + str(max_results)
    else:
      if uri.find('&max-results') == -1:
        uri += '&max-results=' + str(max_results)
    if converter:
      feed = self.GetFeed(uri, converter=converter)
    else:
      feed = self.GetFeed(uri)
    if not title:
      return feed.entry
    if self.use_regex:
      entries = [entry for entry in feed.entry 
                 if entry.title.text and re.match(title,entry.title.text)]
    else:
      entries = [entry for entry in feed.entry if title == entry.title.text]
    return entries

  GetEntries = get_entries

  def get_single_entry(self, uri, title=None, converter=None):
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

  GetSingleEntry = get_single_entry

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid.
    
    Keyword arguments:
      test_uri: URI to pass to self.Get(). Default None (raises error).
      
    Returns:
      True if Get was successful, False if Get raised an exception with the
      string 'Token invalid' in its body, and raises any other exceptions.
    
    """
    if not test_uri:
      raise Exception('No uri to test token with!' +
                      '(was is_token_valid extended?)')
    try:
      self.Get(test_uri)
    except gdata.service.RequestError, err:
      if err.args[0]['body'].find('Token invalid') != -1:
        return False
      else:
        raise
    else:
      return True

  IsTokenValid = is_token_valid

  def request_access(self):
    """Do all the steps involved with getting an OAuth access token.
    
    Return:
      True if access token was succesfully retrieved and set, otherwise False.
    
    """
    import ConfigParser
    import os
    import subprocess
    # Installed applications do not have a pre-registration and so follow
    # directions for unregistered applications
    self.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                 consumer_key='anonymous',
                                 consumer_secret='anonymous')
    try:
      request_token = self.FetchOAuthRequestToken()
    except gdata.service.FetchingOAuthRequestTokenFailed, err:
      print err[0]['body'].strip() + '; Request token retrieval failed!'
      return False
    auth_url = self.GenerateOAuthAuthorizationURL(request_token=request_token)
    try:
      browser = googlecl.CONFIG.get('GENERAL', 'auth_browser')
    except ConfigParser.NoOptionError:
      browser = os.getenv('BROWSER')
    message = 'Please log in and/or grant access via your browser at ' +\
              auth_url + ' then hit enter.'
    if browser:
      try:
        subprocess.call([browser, auth_url])
      except OSError, err:
        print 'Error using browser "' + browser + '": ' + str(err)
    else:
      print '(Hint: You can automatically launch your browser by adding ' +\
            '"auth_browser = <browser>" to your config file under the ' +\
            'GENERAL section, or define the BROWSER environment variable.)'
    raw_input(message)
    # This upgrades the token, and if successful, sets the access token
    try:
      self.UpgradeToOAuthAccessToken(request_token)
    except gdata.service.TokenUpgradeFailed:
      print 'Token upgrade failed! Could not get OAuth access token.'
      return False
    else:
      return True

  RequestAccess = request_access


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
      required: Required options for the task. (Default None)
      optional: Optional options for the task. (Default None)
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
      opt_str = ' Optional: ' + str(self.optional)[1:-1].replace("'", '')
    else:
      opt_str = ''
    if args_desc:
      args_desc = ' Arguments: ' + args_desc
    self.usage = 'Requires: ' + req_str + opt_str + args_desc
    
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
      True if the attribute is always required.
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
    from googlecl.calendar.service import get_datetimes
    import time
    """Figure out the string to return that matches the requested style."""
    # We can access attributes willy-nilly, and catch the NoneTypes later.
    value = ''
    if style == 'title' or style == 'name':
      value = entry.title.text
    elif style[:3] == 'url':
      substyle = style[4:] or googlecl.CONFIG.get('GENERAL', 'url_style')
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
        value = email_string.replace("'", '')
    elif style == 'when':
      start_time_data, end_time_data, freq = get_datetimes(entry)
      print_format = googlecl.CONFIG.get('GENERAL', 'date_print_format')
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
      except AttributeError:
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
      except AttributeError:
        # Blogger uses categories.
        value = join_string.join([c.term for c in entry.category if c.term])
    else:
      raise ValueError("'Unknown listing style: '" + style + "'")
    return value

  return_string = ''
  missing_field_value = missing_field_value or googlecl.CONFIG.get('GENERAL',
                                                          'missing_field_value')
  if not delimiter:
    delimiter = ','
  if delimiter.strip() == ',':
    join_string = ';'
  else:
    join_string = ','
  for style in style_list:
    val = ''
    try:
      # Get the value, replacing NoneTypes and empty strings
      # with the missing field value.
      val = _string_for_style(style, entry, join_string) or missing_field_value
    except ValueError, err:
      print err.args[0] + ' (Did not add value for style ' + style + ')'
    except AttributeError, err:
      if err.args[0].find("'NoneType' object has no attribute") != -1:
        return_string += missing_field_value
      else:
        raise
    # Ensure the delimiter won't appear in a non-delineation role.
    return_string += val.replace(delimiter, ' ') + delimiter
  
  return return_string.rstrip(delimiter)


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
