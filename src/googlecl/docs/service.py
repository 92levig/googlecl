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
import googlecl
import googlecl.service
from googlecl.docs import SECTION_HEADER


class DocsError(googlecl.service.Error):
  """Base error for Docs errors."""
  pass

class UnexpectedExtension(DocsError):
  """Found an unexpected filename extension."""
  def __str__(self):
    if len(self.args) == 1:
      return 'Unexpected extension: ' + self.args[0]
    else:
      return str(self.args)


# These definitions are from gdata.docs.data in higher versions of gdata.
DOCUMENT_LABEL = 'document'
SPREADSHEET_LABEL = 'spreadsheet'
PRESENTATION_LABEL = 'presentation'
FOLDER_LABEL = 'folder'
PDF_LABEL = 'pdf'


class DocsServiceCL(gdata.docs.service.DocsService,
                    googlecl.service.BaseServiceCL):
  
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
    googlecl.service.BaseServiceCL._set_params(self, regex,
                                               tags_prompt, delete_prompt)

  def edit_doc(self, doc_entry, editor, file_format):
    """Edit a document.
    
    Keyword arguments:
      doc_entry: DocEntry of the document to edit.
      editor: Name of the editor to use. Should be executable from the user's
              working directory.
      file_format: Suffix of the file to download.
                   For example, "txt", "csv", "xcl".
    
    """ 
    import subprocess
    import tempfile
    import shutil
    from gdata.docs.service import SUPPORTED_FILETYPES
    
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, doc_entry.title.text + '.' + file_format)
    self.Export(doc_entry, path)
    create_time = os.stat(path).st_mtime
    subprocess.call([editor, path])
    if create_time == os.stat(path).st_mtime:
      print 'No modifications to file, not uploading.'
      return
    else:
      try:
        content_type = SUPPORTED_FILETYPES[file_format.upper()]
      except KeyError:
        print 'Could not find mimetype for ' + file_format
        while file_format not in SUPPORTED_FILETYPES.keys():
          file_format = raw_input('Please enter one of ' +
                                  SUPPORTED_FILETYPES.keys() + 
                                  ' for a content type to upload as.')
        content_type = SUPPORTED_FILETYPES[file_format]
      mediasource = gdata.MediaSource(file_path=path, content_type=content_type)
      self.Put(mediasource, doc_entry.GetEditMediaLink().href)
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
      file_format = get_extension(get_document_type(entry)) or default_format
      path = os.path.join(base_path, entry.title.text + '.' + file_format)
      print 'Downloading ' + entry.title.text + ' to ' + path
      try:
        self.Export(entry, path)
      except gdata.service.RequestError, err:
        print err
        print 'Download of ' + entry.title.text + ' failed'

  GetDocs = get_docs

  def get_doclist(self, title=None, folder_name=None):
    """Get a list of document entries from a feed.
    
    Keyword arguments:
      title: String to use when looking for entries to return. Will be compared
             to entry.title.text, using regular expressions if self.use_regex.
             (Default None for all entries from feed).
      folder_name: String to match against folder titles. Only files found
                   in folders with matching titles will be returned.
                   (Default None for all folders).
                 
    Returns:
      List of entries.
      
    """
    if folder_name:
      query = gdata.docs.service.DocumentQuery(categories=['folder'],
                                               params={'showfolders': 'true'})
      feed = self.Query(query.ToUri())
      entries = []
      for folder in feed.entry:
        # Skip folders that do not match the name we're looking for
        if ((self.use_regex and re.match(folder_name, folder.title.text)) or
            (not self.use_regex and folder_name == folder.title.text)):
          contents = self.QueryDocumentListFeed(uri=folder.content.src)
          if not title:
            entries.extend(contents.entry)
          elif self.use_regex:
            entries.extend([entry for entry in contents.entry
                            if re.match(title, entry.title.text)])
          else:
            entries.extend([entry for entry in contents.entry
                            if title == entry.title.text])
    else:
      query = gdata.docs.service.DocumentQuery()
      entries = self.GetEntries(query.ToUri(),
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

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid."""
    if not test_uri:
      test_uri = gdata.docs.service.DocumentQuery().ToUri()
    return  googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

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
      content_type = ''
      try:
        extension = filename.split('.')[1].upper()
      except IndexError:
        print 'No extension on filename!'
      else:
        try:
          content_type = SUPPORTED_FILETYPES[extension]
        except KeyError:
          pass
      if not content_type:
        content_type = 'text/plain'
      print 'Loading ' + path
      try:
        media = gdata.MediaSource(file_path=path, content_type=content_type)
        title = title or filename.split('.')[0]
        if extension.lower() in ['csv', 'tsv', 'tab', 'ods', 'xls']:
          entry = self.UploadSpreadsheet(media, title)
        elif extension.lower() in ['ppt', 'pps']:
          entry = self.UploadPresentation(media, title)
        elif extension.lower() in ['doc', 'odt', 'rtf', 'sxw',
                                   'txt', 'htm', 'html']:
          entry = self.UploadDocument(media, title)
        else:
          raise UnexpectedExtension(extension)
      except (gdata.service.RequestError, UnexpectedExtension), err:
        print 'Failed to upload ' + path
        print err
      else:
        print 'Upload success! Direct link: ' + entry.GetAlternateLink().href
        url_locs[filename] = entry.GetAlternateLink().href
    return url_locs

  UploadDocs = upload_docs


SERVICE_CLASS = DocsServiceCL


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
      return googlecl.CONFIG.get(SECTION_HEADER, 'spreadsheet_format')
    elif doctype_label == DOCUMENT_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'document_format')
    elif doctype_label == PDF_LABEL:
      return 'pdf'
    elif doctype_label == PRESENTATION_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'presentation_format')
  except ConfigParser.ParsingError, err:
    print err
    try:
      return googlecl.CONFIG.get(SECTION_HEADER, 'format')
    except ConfigParser.ParsingError, err2:
      print err2
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
      return googlecl.CONFIG.get(SECTION_HEADER, 'spreadsheet_editor')
    elif doctype_label == DOCUMENT_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'document_editor')
    elif doctype_label == PDF_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'pdf_editor')
    elif doctype_label == PRESENTATION_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'presentation_editor')
  except ConfigParser.NoOptionError:
    try:
      return googlecl.CONFIG.get(SECTION_HEADER, 'editor')
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
    style_list = googlecl.get_config_option(SECTION_HEADER,
                                            'list_style').split(',')
  for entry in entries:
    print googlecl.service.entry_to_string(entry, style_list,
                                           delimiter=options.delimiter)


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
    format_ext = options.format or get_extension(doc_type)
    editor = options.editor or get_editor(doc_type)
    if not editor:
      print 'No editor defined!'
      print 'Define an "editor" option in your config file, set the ' +\
            'EDITOR environment variable, or pass an editor in with --editor.'
      return
    client.edit_doc(doc_entry, editor, format_ext)


def _run_delete(client, options, args):
  entries = client.get_doclist(options.title)
  client.Delete(entries, 'document',
                googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


TASKS = {'upload': googlecl.service.Task('Upload a document',
                                         callback=_run_upload,
                                         optional=['title', 'folder',
                                                   'no-convert'],
                                         args_desc='PATH_TO_FILE'),
         'edit': googlecl.service.Task('Edit a document', callback=_run_edit,
                                       required=['title'],
                                       optional=['format', 'editor']),
         'get': googlecl.service.Task('Download a document', callback=_run_get,
                                      required=[['title', 'folder']],
                                      args_desc='LOCATION'),
         'list': googlecl.service.Task('List documents', callback=_run_list,
                                       required='delimiter',
                                       optional=['title', 'folder']),
         'delete': googlecl.service.Task('Delete documents',
                                         callback=_run_delete,
                                         optional='title')}
