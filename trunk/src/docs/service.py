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
  docs edit --title "Grocery List" --editor vim (editor also set in prefs)
  
Download docs:
  docs get --folder "Some folder"
  
Created on May 13, 2010

@author: Tom Miller
"""
import docs
import gdata.docs.client
import re
import os
import urllib
import util
from gdata.client import BadAuthentication, CaptchaChallenge


class DocsClientCL(gdata.docs.client.DocsClient):
  
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
    gdata.docs.client.DocsClient.__init__(self, source='GoogleCL')
    self.logged_in = False
    self.use_regex = regex
    self.prompt_for_tags = tags_prompt
    self.prompt_for_delete = delete_prompt

  def get_docs(self, base_path, entries, default_format='txt'):
    """Download documents.
    
    Keyword arguments:
      base_path: The path to download files to. This plus an entry's title plus
                 its format-specific extension will form the complete path.
      entries: List of DocEntry items representing the files to download.
      default_format: The extension to use if the type of the entry is not
                      defined or unknown. (Default 'txt').
    
    """
    for entry in entries:
      format = self.get_extension(entry)
      path = os.path.join(base_path, entry.title.text + '.' + format)
      print 'Downloading ' + entry.title.text + ' to ' + path
      try:
        self.export(entry, path)
      except Exception as e:
        print e.args[0]['body']
        print 'Download of ' + entry.title.text + ' failed'

  GetDocs = get_docs

  def get_doclist(self, title=None, folder=None):
    """Get a list of document entries from a feed.
    
    Keyword arguments:
      title: String to use when looking for entries to return. Will be compared
             to entry.title.text, using regular expressions if self.use_regex.
             (Default None for all entries from feed).
      folder: String to match against folder titles. Only files found in folders
              with matching titles will be returned. (Default None for all
              folders).
                 
    Returns:
      List of entries.
      
    """
    if folder:
      feed = gdata.docs.client.DocsClient.get_doclist(self,
                                    uri='/feeds/default/private/full/-/folder')
      entries = []
      for f in feed.entry:
        # Skip folders that do not match the name we're looking for
        if ((self.use_regex and re.match(folder,f.title.text)) or
            (not self.use_regex and folder == f.title.text)):
          contents = gdata.docs.client.DocsClient.get_doclist(self,
                                                              uri=f.content.src)
          if not title:
            entries.extend(contents.entry)
          elif self.use_regex:
            entries.extend([entry for entry in contents.entry
                            if re.match(title,entry.title.text)])
          else:
            entries.extend([entry for entry in contents.entry
                            if title == entry.title.text])
    else: 
      f = gdata.docs.client.DocsClient.get_doclist(self)
      if not title:
        return f.entry
      if self.use_regex:
        entries = [entry for entry in f.entry
                   if re.match(title,entry.title.text)]
      else:
        entries = [entry for entry in f.entry
                   if title == entry.title.text]
    return entries

  def get_extension(self, entry):
    """Return file extension based on entry type and preferences file."""
    type = entry.GetDocumentType() 
    if type == gdata.docs.data.SPREADSHEET_LABEL:
      return util.config.get('DOCS', 'spreadsheet_format')
    elif type == gdata.docs.data.DOCUMENT_LABEL:
      return util.config.get('DOCS', 'document_format')
    elif type == gdata.docs.data.PDF_LABEL:
      return 'pdf'
    elif type == gdata.docs.data.PRESENTATION_LABEL:
      return util.config.get('DOCS', 'document_format')
    else:
      return util.config.get('DOCS', 'default_format')

  GetExtension = get_extension

  def is_token_valid(self):
    """Check that the token being used is valid."""
    try:
      self.Get('/feeds/default/private/full')
    except gdata.service.RequestError as e:
      if e.args[0]['body'].find('Token invalid') != -1:
        return False
      else:
        raise
    else:
      return True
  
  IsTokenValid = is_token_valid

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
    
    # Map folder titles to IDs
    if self.logged_in:
      folder_feed = self.GetDocList(uri='/feeds/default/private/full/-/folder')
      self.folder_id = {}
      for f in folder_feed.entry:
        self.folder_id[f.title.text] = f.resource_id.text
    
  Login = login

  def upload_docs(self, paths, title=None, folder=None, convert=True):
    """Upload a document.
    
    Keyword arguments:
      paths: Paths of files to upload.
      title: Title to give the files once uploaded.
             (Defaults to the names of the files).
      folder: Folder to put the files in. (Defaults to the root folder).
      convert: If True, converts the files to the native Google Docs format.
               Otherwise, leaves as arbitrary file type. Only Google Apps
               Premier users can specify a value other than True. (Default True)

    Returns:
      Dictionary mapping filenames to where they can be accessed online.
    """
    from gdata.docs.data import MIMETYPES
    if folder and self.folder_id.has_key(folder):
      folder_id = self.folder_id[folder]
      uri = (gdata.docs.client.FOLDERS_FEED_TEMPLATE % 
             urllib.quote_plus(folder_id))
    else:
      uri = gdata.docs.client.DOCLIST_FEED_URI
    uri += '?convert=' + str(convert).lower()
    url_locs = {}
    for path in paths:
      filename = os.path.basename(path)
      try:
        content_type = MIMETYPES[filename.split('.')[1].upper()]
      except:
        content_type = 'text/plain'
      print 'Loading ' + path
      try:
        entry = self.Upload(path,
                            title or filename.split('.')[0],
                            content_type=content_type,
                            folder_or_uri=uri)
      except Exception as e:
        print 'Failed to upload ' + path
        print e
      else:
        print 'Upload success! Direct link: ' + entry.GetAlternateLink().href
        url_locs[filename] = entry.GetAlternateLink().href
    return url_locs

  UploadDocs = upload_docs


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
def _run_get(client, options, args):
  if not args:
    path = os.getcwd()
  else:
    path = args[0]
    if not os.path.exists(path):
      print 'Path ' + path + ' does not exist!'
      return
  entries = client.get_doclist(options.title, options.folder)
  client.get_docs(path, entries)


def _run_list(client, options, args):
  entries = client.get_doclist(options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_list_style(docs.SECTION_HEADER)
  for e in entries:
    print util.entry_to_string(e, style_list, delimiter=options.delimiter)


def _run_upload(client, options, args):
  if not args:
    print 'Need to tell me what to upload!'
    return
  client.upload_docs(args, options.title, options.folder, options.convert)


def _run_edit(client, options, args):
  import subprocess
  from gdata.docs.data import MIMETYPES
  from gdata.data import MediaSource
  
  if not os.path.exists('/tmp/googlecl'):
    os.mkdir('/tmp/googlecl')
  entries = client.get_doclist(options.title)
  if len(entries) > 1:
    print 'More than one match, only editing the first result.'
  e = entries[0]
  format = options.format or client.get_extension(e)
  path = '/tmp/googlecl/' + e.title.text + '.' + format
  client.export(e, path)
  subprocess.call([options.editor, path])
  try:
    content_type = MIMETYPES[format.upper()]
  except KeyError:
    print 'Could not find mimetype for ' + format
    while format not in MIMETYPES.keys():
      format = raw_input('Please enter one of ' + MIMETYPES.keys() + 
                         ' for a content type to upload as.')
    content_type = MIMETYPES[format]
  mediasource = MediaSource(file_path=path, content_type=content_type)
  client.Update(e, mediasource)


tasks = {'upload': util.Task('Upload a document', callback=_run_upload,
                             optional=['title', 'folder', 'no-convert'],
                             args_desc='PATH_TO_FILE'),
         'edit': util.Task('Edit a document', callback=_run_edit,
                           required=['title', 'editor'],
                           optional=['format']),
         'get': util.Task('Download a document', callback=_run_get,
                          required=[['title', 'folder']],
                          args_desc='LOCATION'),
         'list': util.Task('List documents', callback=_run_list,
                           required='delimiter', optional='title')}