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
import os
import googlecl
import googlecl.service
import warnings
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
DOCUMENTS_NAMESPACE = 'http://schemas.google.com/docs/2007'

class DocsServiceCL(gdata.docs.service.DocsService,
                    googlecl.service.BaseServiceCL):
  
  """Extends gdata.docs.service.DocsClient for the command line.
  
  This class adds some features focused on using Google Docs via an installed
  app with a command line interface.
  
  """
  
  def __init__(self):
    """Constructor.""" 
    gdata.docs.service.DocsService.__init__(self, source='GoogleCL')
    self._set_params(SECTION_HEADER)

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
    self.Export(doc_entry.content.src, path)
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

  def get_docs(self, base_path, entries, file_format=None):
    """Download documents.
    
    Keyword arguments:
      base_path: The path to download files to. This plus an entry's title plus
                 its format-specific extension will form the complete path.
      entries: List of DocEntry items representing the files to download.
      file_format: Suffix to give the file when downloading.
                   For example, "txt", "csv", "xcl". Default None to let
                   get_extension decide the extension.

    """
    default_format = 'txt'
    for entry in entries:
      if not file_format:
        file_format = get_extension(get_document_type(entry)) or default_format
      path = os.path.join(base_path, entry.title.text + '.' + file_format)
      print 'Downloading ' + entry.title.text + ' to ' + path
      try:
        self.Export(entry, path)
      except gdata.service.RequestError, err:
        print err
        print 'Download of ' + entry.title.text + ' failed'

  GetDocs = get_docs

  def get_doclist(self, title=None, folder_entry_list=None):
    """Get a list of document entries from a feed.
    
    Keyword arguments:
      title: String to use when looking for entries to return. Will be compared
             to entry.title.text, using regular expressions if self.use_regex.
             Default None for all entries from feed.
      folder_entry_list: List of GDataEntry's of folders to get from.
             Only files found in these folders will be returned.
             Default None for all folders.
                 
    Returns:
      List of entries.
      
    """
    if folder_entry_list:
      entries = []
      for folder in folder_entry_list:
        # folder.content.src is the uri to query for documents in that folder.
        entries.extend(self.GetEntries(folder.content.src,
                                       title,
                               converter=gdata.docs.DocumentListFeedFromString))
    else:
      query = gdata.docs.service.DocumentQuery()
      entries = self.GetEntries(query.ToUri(),
                                title,
                                converter=gdata.docs.DocumentListFeedFromString)
    return entries

  def get_single_doc(self, title=None, folder_entry_list=None):
    """Return exactly one doc_entry.
    
    Keyword arguments:
      title: Title to match on for document. Default None for any title.
      folder_entry_list: GDataEntry of folders to look in.
                         Default None for any folder.
    
    Returns:
      None if there were no matches, or one entry matching the given title.
    
    """
    if folder_entry_list:
      if len(folder_entry_list) == 1:
        return self.GetSingleEntry(folder_entry_list[0].content.src,
                                   title,
                                converter=gdata.docs.DocumentListFeedFromString)
      else:
        entries = self.get_doclist(title, folder_entry_list)
        # Technically don't need the converter for this call
        # because we have the entries.
        return self.GetSingleEntry(entries, title)
    else:
      return self.GetSingleEntry(gdata.docs.service.DocumentQuery().ToUri(),
                                 title,
                                converter=gdata.docs.DocumentListFeedFromString)

  GetSingleDoc = get_single_doc

  def get_folder(self, title):
    """Return entries for one or more folders.

    Keyword arguments:
      title: Title of the folder.

    Returns:
      GDataEntry representing a folder, or None of title is None.

    """
    if title:
      query = gdata.docs.service.DocumentQuery(categories=['folder'],
                                               params={'showfolders': 'true'})
      folder_entries = self.GetEntries(query.ToUri(), title=title)
      if not folder_entries:
        warnings.warn('No folder found that matches ' + title, stacklevel=2)
      return folder_entries
    else:
      return None

  GetFolder = get_folder

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid."""
    if not test_uri:
      docs_uri = gdata.docs.service.DocumentQuery().ToUri()
      sheets_uri = \
               'https://spreadsheets.google.com/feeds/spreadsheets/private/full'
    docs_test = googlecl.service.BaseServiceCL.IsTokenValid(self, docs_uri)
    sheets_test = googlecl.service.BaseServiceCL.IsTokenValid(self, sheets_uri)
    return docs_test and sheets_test

  IsTokenValid = is_token_valid

  def request_access(self, scopes=None):
    """Request access as in BaseServiceCL, but specify scopes."""
    # When people use docs (writely), they expect access to
    # spreadsheets as well (wise).
    if not scopes:
      scopes = gdata.service.CLIENT_LOGIN_SCOPES['writely'] +\
               gdata.service.CLIENT_LOGIN_SCOPES['wise']
    return googlecl.service.BaseServiceCL.request_access(self, scopes=scopes)

  RequestAccess = request_access

  def upload_docs(self, paths, title=None, folder_entry=None,
                  file_format=None):
    """Upload a document.
    
    Keyword arguments:
      paths: Paths of files to upload.
      title: Title to give the files once uploaded.
             Default None for the names of the files.
      folder_entry: GDataEntry of the folder to upload into. 
                    Default None for no folder.
      file_format: Replace (or specify) the extension on the file when figuring
              out the upload format. For example, 'txt' will upload the
              file as if it was plain text. Default None for the file's
              extension (which defaults to 'txt' if there is none).

    Returns:
      Dictionary mapping filenames to where they can be accessed online.
    
    """
    import atom
    from gdata.docs.service import SUPPORTED_FILETYPES
    url_locs = {}
    if folder_entry:
      post_uri = folder_entry.content.src
    else:
      post_uri = '/feeds/documents/private/full'
    for path in paths:
      filename = os.path.basename(path)
      if file_format:
        extension = file_format
      else:
        try:
          extension = filename.split('.')[1]
        except IndexError:
          default_ext = 'txt'
          print 'No extension on filename! Treating as ' + default_ext
          extension = default_ext
      try:
        content_type = SUPPORTED_FILETYPES[extension.upper()]
      except KeyError:
        print 'No supported filetype found for extension ' + extension
        content_type = 'text/plain'
        print 'Uploading as ' + content_type
      print 'Loading ' + path
      try:
        media = gdata.MediaSource(file_path=path, content_type=content_type)
      except IOError, err:
        print err
        continue
      entry_title = title or filename.split('.')[0]
      # Upload() wasn't added until later versions of DocsService, so
      # we may not have it. To support uploading to folders for earlier
      # versions of the API, expose the lower-level Post
      entry = gdata.docs.DocumentListEntry()
      entry.title = atom.Title(text=entry_title)
      if extension.lower() in ['csv', 'tsv', 'tab', 'ods', 'xls']:
        category = _make_kind_category(SPREADSHEET_LABEL)
      elif extension.lower() in ['ppt', 'pps']:
        category = _make_kind_category(PRESENTATION_LABEL)
      elif extension.lower() in ['pdf']:
        category = _make_kind_category(PDF_LABEL)
      # Treat everything else as a document
      else:
        category = _make_kind_category(DOCUMENT_LABEL)
      entry.category.append(category)
      try:
        new_entry = self.Post(entry, post_uri, media_source=media,
                              extra_headers={'Slug': media.file_name},
                              converter=gdata.docs.DocumentListEntryFromString)
      except (gdata.service.RequestError, UnexpectedExtension), err:
        print 'Failed to upload ' + path
        print err
      else:
        print 'Upload success! Direct link: ' +\
              new_entry.GetAlternateLink().href
        url_locs[filename] = new_entry.GetAlternateLink().href
    return url_locs

  UploadDocs = upload_docs


SERVICE_CLASS = DocsServiceCL


def _make_kind_category(label):
  """Stolen from gdata-2.0.10 docs.service."""
  import atom
  if label is None:
    return None
  return atom.Category(scheme=gdata.docs.service.DATA_KIND_SCHEME,
                       term=DOCUMENTS_NAMESPACE + '#' + label, label=label)


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
  folder_entries = client.get_folder(options.folder)
  entries = client.get_doclist(options.title, folder_entries)
  client.get_docs(path, entries, file_format=options.format)


def _run_list(client, options, args):
  folder_entries = client.get_folder(options.folder)
  entries = client.get_doclist(options.title, folder_entries)
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
  folder_entries = client.get_folder(options.folder)
  folder_entry = client.get_single_entry(folder_entries)
  client.upload_docs(args, title=options.title, folder_entry=folder_entry,
                     file_format=options.format)


def _run_edit(client, options, args):
  if not hasattr(client, 'Export'):
    print 'Editing documents is not supported' +\
          ' for gdata-python-client < 2.0'
    return
  folder_entry_list = client.get_folder(options.folder)
  doc_entry = client.get_single_doc(options.title, folder_entry_list)
  if not doc_entry:
    print 'No matching documents found! Creating it.'
    new_entry = gdata.docs.DocumentListEntry()
    new_entry.title = gdata.atom.Title(text=options.title or 'GoogleCL doc')
    category = _make_kind_category(DOCUMENT_LABEL)
    new_entry.category.append(category)
    folder_entries = client.get_folder(options.folder)
    folder_entry = client.get_single_entry(folder_entries)
    if folder_entry:
      post_uri = folder_entry.content.src
    else:
      post_uri = '/feeds/documents/private/full'
    doc_entry = client.Post(new_entry, post_uri)
  doc_type = get_document_type(doc_entry)
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
                                         optional=['title', 'folder', 'format'],
                                         args_desc='PATH_TO_FILE'),
         'edit': googlecl.service.Task('Edit a document', callback=_run_edit,
                                       required=['title'],
                                       optional=['format', 'editor', 'folder']),
         'get': googlecl.service.Task('Download a document', callback=_run_get,
                                      required=[['title', 'folder']],
                                      optional='format',
                                      args_desc='LOCATION'),
         'list': googlecl.service.Task('List documents', callback=_run_list,
                                       required='delimiter',
                                       optional=['title', 'folder']),
         'delete': googlecl.service.Task('Delete documents',
                                         callback=_run_delete,
                                         optional='title')}
