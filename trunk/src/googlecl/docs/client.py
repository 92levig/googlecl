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


"""Service details and instances for the Docs service.

COMPATABILTIY NOTE: This is one of the few Python modules that uses the 2.0
client library (v3 of the gdata protocol), 
and is still in labs. It's likely that this will break often.
The code in this file tries to follow the style found in gdata.client and
gdata.docs.client, instead of the rest of the GoogleCL project. The idea is
that the other services/clients will also be updated to look like the 2.0
compatible code in the near future.
 
Some use cases:
Upload a document:
  docs upload --folder "Some folder" path_to_doc
  
Edit a document in your word editor:
  docs edit --title "Grocery List" --editor vim (editor also set in prefs)
  
Download docs:
  docs get --folder "Some folder"

"""
__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import ConfigParser
import gdata.docs.client
import re
import os
import urllib
import googlecl.util as util
from gdata.client import BadAuthentication, CaptchaChallenge
from googlecl.docs import SECTION_HEADER

class DocsClientCL(gdata.docs.client.DocsClient):
  
  """Extends gdata.docs.client.DocsClient for the command line.
  
  This class adds some features focused on using Google Docs via an installed
  app with a command line interface.
  
  """
  
  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as document names. (Default False)
      tags_prompt: Indicates if while inserting docs, instance should prompt
                   for tags for each doc. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting a document. (Default True)
              
    """ 
    gdata.docs.client.DocsClient.__init__(self, source='GoogleCL')
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
        gdata.docs.client.DocsClient.Delete(self, item)

  Delete = delete

  def edit_doc(self, doc_entry, editor, format):
    """Edit a document.
    
    Keyword arguments:
      doc_entry: DocEntry of the document to edit.
      editor: Name of the editor to use. Should be executable from the user's
              working directory.
      format: Suffix of the file to download. For example, "txt", "csv", "xcl".
    
    """ 
    import subprocess
    import tempfile
    import shutil
    from gdata.docs.data import MIMETYPES
    from gdata.data import MediaSource
    
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, doc_entry.title.text + '.' + format)
    self.export(doc_entry, path)
    create_time = os.stat(path).st_mtime
    subprocess.call([editor, path])
    if create_time == os.stat(path).st_mtime:
      print 'No modifications to file, not uploading.'
      return
    else:
      try:
        content_type = MIMETYPES[format.upper()]
      except KeyError:
        print 'Could not find mimetype for ' + format
        while format not in MIMETYPES.keys():
          format = raw_input('Please enter one of ' + MIMETYPES.keys() + 
                             ' for a content type to upload as.')
        content_type = MIMETYPES[format]
      mediasource = MediaSource(file_path=path, content_type=content_type)
      self.Update(doc_entry, media_source=mediasource)
    try:
      # Good faith effort to keep the temp directory clean.
      shutil.rmtree(temp_dir)
    except OSError:
      # Only seen errors on Windows, but catch the more general OSError.
      pass

  EditDoc = edit_doc

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
      format = get_extension(entry.GetDocumentType())
      path = os.path.join(base_path, entry.title.text + '.' + format)
      print 'Downloading ' + entry.title.text + ' to ' + path
      try:
        self.export(entry, path)
      except Exception, e:
        print e
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

  def get_single_doc(self, title=None, folder=None):
    """Return exactly one file.
    
    Uses GetEntries to retrieve the entries, then asks the user to select one of
    them by entering a number.
    
    Keyword arguments:
      title: Title to match on. See get_doclist. (Default None).
      folder: Folders to look in. See get_doclist. (Default None).
    
    Returns:
      None if there were no matches, or one entry matching the given title.
    
    """
    entries = self.get_doclist(title, folder)
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

  GetSingleDoc = get_single_doc

  def is_token_valid(self):
    """Check that the token being used is valid."""
    try:
      self.Get('/feeds/default/private/full')
    except gdata.service.RequestError, e:
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
    except BadAuthentication, e:
      print e
    except CaptchaChallenge:
      print 'Too many failed logins; Captcha required.'
    else:
      self.logged_in = True

  Login = login

  def upload_docs(self, paths, title=None, folder=None, convert=True):
    """Upload a document.
    
    Keyword arguments:
      paths: Paths of files to upload.
      title: Title to give the files once uploaded.
             (Default None for the names of the files).
      folder: Folder to put the files in. (Default None for the root folder).
      convert: If True, converts the files to the native Google Docs format.
               Otherwise, leaves as arbitrary file type. Only Google Apps
               Premier users can specify a value other than True. (Default True)

    Returns:
      Dictionary mapping filenames to where they can be accessed online.
    
    """
    from gdata.docs.data import MIMETYPES
    uri = ''
    if folder:
      folder_feed = self.GetDocList(uri='/feeds/default/private/full/-/folder')
      folder_entry = None
      for f in folder_feed.entry:
        if f.title.text == folder:
          folder_entry = f
          break
      if not folder_entry:
        create_folder = raw_input('Folder ' + folder + 
                                  ' not found. Create it? (y/N): ')
        if create_folder.lower() == 'y':
          folder_entry = self.create(gdata.docs.data.FOLDER_LABEL, folder)
      if folder_entry:
        uri = (gdata.docs.client.FOLDERS_FEED_TEMPLATE % 
               urllib.quote_plus(folder_entry.resource_id.text))
    if not uri:
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
      except Exception, e:
        print 'Failed to upload ' + path
        print e
      else:
        print 'Upload success! Direct link: ' + entry.GetAlternateLink().href
        url_locs[filename] = entry.GetAlternateLink().href
    return url_locs

  UploadDocs = upload_docs


service_class = DocsClientCL


def get_extension(doctype_label):
  """Return file extension based on document type and preferences file."""
  try:
    if doctype_label == gdata.docs.data.SPREADSHEET_LABEL:
      return util.config.get(SECTION_HEADER, 'spreadsheet_format')
    elif doctype_label == gdata.docs.data.DOCUMENT_LABEL:
      return util.config.get(SECTION_HEADER, 'document_format')
    elif doctype_label == gdata.docs.data.PDF_LABEL:
      return 'pdf'
    elif doctype_label == gdata.docs.data.PRESENTATION_LABEL:
      return util.config.get(SECTION_HEADER, 'presentation_format')
  except ConfigParser.NoOptionError:
    try:
      return util.config.get(SECTION_HEADER, 'format')
    except:
      return None


def get_editor(doctype_label):
  """Return editor for file based on entry type and preferences file.
  
  Editor is determined in an order of preference:
  1) Try to load the editor for the specific type (spreadsheet, document, etc.)
  2) If no specification, try to load the "default_editor" option.
  3) If no default_editor, try to load the EDITOR environment variable.
  4) If no EDITOR variable, return None.
  
  Keyword arguments:
    doctype_label: A string representing the type of document to edit. Should
                   be defined in gdata.docs.data, e.g. SPREADSHEET_LABEL.
  
  """
  try:
    if doctype_label == gdata.docs.data.SPREADSHEET_LABEL:
      return util.config.get(SECTION_HEADER, 'spreadsheet_editor')
    elif doctype_label == gdata.docs.data.DOCUMENT_LABEL:
      return util.config.get(SECTION_HEADER, 'document_editor')
    elif doctype_label == gdata.docs.data.PDF_LABEL:
      return util.config.get(SECTION_HEADER, 'pdf_editor')
    elif doctype_label == gdata.docs.data.PRESENTATION_LABEL:
      return util.config.get(SECTION_HEADER, 'presentation_editor')
  except ConfigParser.NoOptionError:
    try:
      return util.config.get(SECTION_HEADER, 'editor')
    except ConfigParser.NoOptionError:
      return os.getenv('EDITOR')
  
    
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
  print 'Removing spreadsheets from list of documents...'
  print '(Downloading spreadsheets through the API is currently broken, sorry).'
  entries = [e for e in entries
             if e.GetDocumentType() != gdata.docs.data.SPREADSHEET_LABEL]
  client.get_docs(path, entries)


def _run_list(client, options, args):
  entries = client.get_doclist(options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for e in entries:
    print util.entry_to_string(e, style_list, delimiter=options.delimiter)


def _run_upload(client, options, args):
  if not args:
    print 'Need to tell me what to upload!'
    return
  client.upload_docs(args, options.title, options.folder, options.convert)


def _run_edit(client, options, args):
  doc_entry = client.get_single_doc(options.title, options.folder)
  if not doc_entry:
    print 'No matching documents found!'
    return
  doc_type = doc_entry.GetDocumentType()
  # Spreadsheet exporting is still broken (on the client library side)
  # so we can't let users specify spreadsheets.
  if doc_type == gdata.docs.data.SPREADSHEET_LABEL:
    print 'Sorry, cannot edit or download spreadsheets.'
    return
  else:
    format = options.format or get_extension(doc_type)
    editor = options.editor or get_editor(doc_type)
    if not editor:
      print 'No editor defined!'
      print 'Define an "editor" option in your config file, set the ' +\
            'EDITOR environment variable, or pass an editor in with --editor.'
      return
    client.edit_doc(doc_entry, editor, format)


def _run_delete(client, options, args):
  entries = client.get_doclist(options.title)
  client.delete(entries, 'document',
                util.config.getboolean('GENERAL', 'delete_by_default'))


tasks = {'upload': util.Task('Upload a document', callback=_run_upload,
                             optional=['title', 'folder', 'no-convert'],
                             args_desc='PATH_TO_FILE'),
         'edit': util.Task('Edit a document', callback=_run_edit,
                           required=['title'],
                           optional=['format', 'editor']),
         'get': util.Task('Download a document', callback=_run_get,
                          required=[['title', 'folder']],
                          args_desc='LOCATION'),
         'list': util.Task('List documents', callback=_run_list,
                           required='delimiter', optional='title'),
         'delete': util.Task('Delete documents', callback=_run_delete,
                             optional='title')}
