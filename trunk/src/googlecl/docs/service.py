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
import gdata.docs.service
import re
import os
from googlecl import util
from googlecl.docs import SECTION_HEADER


# These definitions are from gdata.docs.data in higher versions of gdata.
DOCUMENT_LABEL = 'document'
SPREADSHEET_LABEL = 'spreadsheet'
PRESENTATION_LABEL = 'presentation'
FOLDER_LABEL = 'folder'
PDF_LABEL = 'pdf'


class DocsServiceCL(gdata.docs.service.DocsService, util.BaseServiceCL):
  
  """Extends gdata.docs.service.DocsClient for the command line.
  
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
    gdata.docs.service.DocsService.__init__(self, source='GoogleCL')
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)

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
    from gdata.docs.service import SUPPORTED_FILETYPES
    
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, doc_entry.title.text + '.' + format)
    self.Export(doc_entry, path)
    create_time = os.stat(path).st_mtime
    subprocess.call([editor, path])
    if create_time == os.stat(path).st_mtime:
      print 'No modifications to file, not uploading.'
      return
    else:
      try:
        content_type = SUPPORTED_FILETYPES[format.upper()]
      except KeyError:
        print 'Could not find mimetype for ' + format
        while format not in SUPPORTED_FILETYPES.keys():
          format = raw_input('Please enter one of ' + SUPPORTED_FILETYPES.keys() + 
                             ' for a content type to upload as.')
        content_type = SUPPORTED_FILETYPES[format]
      mediasource = gdata.MediaSource(file_path=path, content_type=content_type)
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
      format = get_extension(get_document_type(entry))
      path = os.path.join(base_path, entry.title.text + '.' + format)
      print 'Downloading ' + entry.title.text + ' to ' + path
      try:
        self.Export(entry, path)
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
      q = gdata.docs.service.DocumentQuery(categories=['folder'],
                                           params={'showfolders': 'true'})
      feed = self.Query(q.ToUri())
      entries = []
      for f in feed.entry:
        # Skip folders that do not match the name we're looking for
        if ((self.use_regex and re.match(folder,f.title.text)) or
            (not self.use_regex and folder == f.title.text)):
          contents = self.QueryDocumentListFeed(uri=f.content.src)
          if not title:
            entries.extend(contents.entry)
          elif self.use_regex:
            entries.extend([entry for entry in contents.entry
                            if re.match(title,entry.title.text)])
          else:
            entries.extend([entry for entry in contents.entry
                            if title == entry.title.text])
    else:
      q = gdata.docs.service.DocumentQuery()
      entries = self.GetEntries(q.ToUri(),
                                title,
                                converter=gdata.docs.DocumentListFeedFromString)
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
      q = gdata.docs.service.DocumentQuery()
      self.Get(q.ToUri())
    except gdata.service.RequestError, e:
      if e.args[0]['body'].find('Token invalid') != -1:
        return False
      else:
        raise
    else:
      return True
  
  IsTokenValid = is_token_valid

  def upload_docs(self, paths, title=None):
    """Upload a document.
    
    Keyword arguments:
      paths: Paths of files to upload.
      title: Title to give the files once uploaded.
             (Default None for the names of the files).

    Returns:
      Dictionary mapping filenames to where they can be accessed online.
    
    """
    from gdata.docs.service import SUPPORTED_FILETYPES
    url_locs = {}
    for path in paths:
      filename = os.path.basename(path)
      try:
        extension = filename.split('.')[1].upper()
        content_type = SUPPORTED_FILETYPES[extension]
      except:
        content_type = 'text/plain'
      print 'Loading ' + path
      try:
        ms = gdata.MediaSource(file_path=path, content_type=content_type)
        title = title or filename.split('.')[0]
        if extension.lower() in ['csv', 'tsv', 'tab', 'ods', 'xls']:
          entry = self.UploadSpreadsheet(ms, title)
        elif extension.lower() in ['ppt', 'pps']:
          entry = self.UploadPresentation(ms, title)
        elif extension.lower() in ['doc', 'odt', 'rtf', 'sxw',
                                   'txt', 'htm', 'html']:
          entry = self.UploadDocument(ms, title)
        else:
          raise Exception('Unexpected extension: ' + extension)
      except Exception, e:
        print 'Failed to upload ' + path
        print e
      else:
        print 'Upload success! Direct link: ' + entry.GetAlternateLink().href
        url_locs[filename] = entry.GetAlternateLink().href
    return url_locs

  UploadDocs = upload_docs


service_class = DocsServiceCL


def get_document_type(entry):
  """Extracts the type of document given DocsEntry is.

  This method returns the type of document the DocsEntry represents. Possible
  values are document, presentation, spreadsheet, folder, or pdf.
  This function appears in gdata-2.x.x python client libraries, and is
  copied here for compatibility with gdata-1.2.4.

  Returns:
    A string representing the type of document.
  
  """
  data_kind_scheme = 'http://schemas.google.com/g/2005#kind'
  if entry.category:
    for category in entry.category:
      if category.scheme == data_kind_scheme:
        return category.label
  else:
    return None


def get_extension(doctype_label):
  """Return file extension based on document type and preferences file."""
  try:
    if doctype_label == SPREADSHEET_LABEL:
      return util.config.get(SECTION_HEADER, 'spreadsheet_format')
    elif doctype_label == DOCUMENT_LABEL:
      return util.config.get(SECTION_HEADER, 'document_format')
    elif doctype_label == PDF_LABEL:
      return 'pdf'
    elif doctype_label == PRESENTATION_LABEL:
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
  2) If no specification, try to load the "editor" option from config file.
  3) If no default editor, try to load the EDITOR environment variable.
  4) If no EDITOR variable, return None.
  
  Keyword arguments:
    doctype_label: A string representing the type of document to edit.
  
  Returns:
    Editor to use to edit the document.
  
  """
  try:
    if doctype_label == SPREADSHEET_LABEL:
      return util.config.get(SECTION_HEADER, 'spreadsheet_editor')
    elif doctype_label == DOCUMENT_LABEL:
      return util.config.get(SECTION_HEADER, 'document_editor')
    elif doctype_label == PDF_LABEL:
      return util.config.get(SECTION_HEADER, 'pdf_editor')
    elif doctype_label == PRESENTATION_LABEL:
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
  if not hasattr(client, 'Export'):
    print 'Downloading documents is not supported for gdata-python-client < 2.0'
    return
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
             if get_document_type(e) != SPREADSHEET_LABEL]
  client.get_docs(path, entries)


def _run_list(client, options, args):
  entries = client.get_doclist(options.title, options.folder)
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
  client.upload_docs(args, options.title)


def _run_edit(client, options, args):
  if not hasattr(client, 'Export'):
    print 'Editing documents is not supported for gdata-python-client < 2.0'
    return
  doc_entry = client.get_single_doc(options.title, options.folder)
  if not doc_entry:
    print 'No matching documents found!'
    return
  doc_type = get_document_type(doc_entry)
  # Spreadsheet exporting is still broken (on the client library side)
  # so we can't let users specify spreadsheets.
  if doc_type == SPREADSHEET_LABEL:
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
  client.Delete(entries, 'document',
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
                           required='delimiter', optional=['title', 'folder']),
         'delete': util.Task('Delete documents', callback=_run_delete,
                             optional='title')}