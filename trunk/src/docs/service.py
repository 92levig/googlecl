"""
Service details and instances for the Docs service.

COMPATABILTIY NOTE: This is one of the few Python modules that uses the 2.0
gdata API, and is still in labs. It's likely that this will break often.
The code in this file tries to follow the style found in gdata.client and
gdata.docs.client, instead of the rest of the GoogleCL project. The idea is
that the other services/clients will also be updated to look like the 2.0
compatable code in the near future.
 
Some use cases:
Upload a document:
  docs upload --folder "Some folder" path_to_doc
  
Edit a document in your word editor:
  docs edit --title "Grocery List" --editor vim (editor also set in prefs
  
Download docs:
  docs get --folder "Some folder"
  
Created on May 13, 2010

@author: Tom Miller
"""

import gdata.docs.client
import re
import util
from gdata.client import BadAuthentication, CaptchaChallenge


class DocsClientCL(gdata.docs.client.DocsClient, util.BaseServiceCL):
  
  """Extends gdata.docs.client.DocsClient for the command line.
  
  This class adds some features focused on using Google Docs via an installed
  app with a command line interface.
  
  """
  
  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as album titles. (Default False)
      tags_prompt: Indicates if while inserting photos, instance should prompt
                   for tags for each photo. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting an album or photo. (Default True)
              
    """ 
    # Seems like a bug to need this. But it stops "No attribute <blah>"
    # exceptions.
    util.BaseServiceCL.__init__(self)
    gdata.docs.client.DocsClient.__init__(self, source='GoogleCL')
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)
  
  def get_doclist(self, title=None):
    """Get a list of document entries from a feed.
    
    Keyword arguments:
      title: String to use when looking for entries to return. Will be compared
             to entry.title.text, using regular expressions if self.use_regex.
             (Default None for all entries from feed)
                 
    Returns:
      List of entries.
      
    """
    f = gdata.docs.client.DocsClient.get_doclist(self)
    if not title:
      return f.entry
    if self.use_regex:
      entries = [entry for entry in f.entry if re.match(title,entry.title.text)]
    else:
      entries = [entry for entry in f.entry if title == entry.title.text]
    return entries
  
  def login(self, email, password):
    """Log in to the docs service.
    
    Keyword arguments:
      email: Email account to use.
      password: Password associated with said account.
    
    Returns:
      Nothing, but sets self.logged_in to true on success.
    
    """
    self.logged_in = False
    if not (email and password):
      print ('You must give an email/password combo to log in with.')
      return
    
    try:
      self.client_login(email, password, 'GoogleCL')
    except BadAuthentication as e:
      print e
    except CaptchaChallenge:
      print 'Too many failed logins; Captcha required.'
    else:
      self.logged_in = True

  Login = login


service_class = DocsClientCL


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#  
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_list(client, options, args):
  entries = client.get_doclist(options.title)
  for e in entries:
    print e.title.text, '('+e.GetDocumentType()+')' 


tasks = {'upload': util.Task('Upload a document',
                             optional=['title', 'folder'],
                             args_desc='PATH_TO_FILE'),
         'edit': util.Task('Edit a document',
                           required='title',
                           optional=['editor']),
         'get': util.Task('Download a document',
                          required=['title', 'folder'],
                          args_desc='LOCATION'),
         'list': util.Task('List documents', callback=_run_list,
                           optional='title')}