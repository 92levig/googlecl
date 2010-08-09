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


"""Service details and instances for the Docs service using GData 3.0.
 
Some use cases:
Upload a document:
  docs upload --folder "Some folder" path_to_doc
  
Edit a document in your word editor:
  docs edit --title "Grocery List" --editor vim (editor also set in prefs)
  
Download docs:
  docs get --folder "Some folder"

"""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import gdata.docs.client
import logging
import os
import shutil
import googlecl
import googlecl.client
from googlecl.docs import SECTION_HEADER
import googlecl.docs.base


LOG = logging.getLogger(googlecl.docs.LOGGER_NAME + '.client')


class DocsClientCL(gdata.docs.client.DocsClient,
                   googlecl.client.BaseClientCL):
  
  """Extends gdata.docs.client.DocsClient for the command line.
  
  This class adds some features focused on using Google Docs via an installed
  app with a command line interface.
  
  """

  def __init__(self):
    """Constructor.""" 
    gdata.docs.client.DocsClient.__init__(self, source='GoogleCL')
    googlecl.client.BaseClientCL.__init__(self, section=SECTION_HEADER)

  def _download_file(self, uri, file_path, auth_token=None, **kwargs):
    """Downloads a file, optionally decoding from UTF-8.

    Overridden from gdata.docs.client to support decoding.

    Args:
      uri: string The full Export URL to download the file from.
      file_path: string The full path to save the file to.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      decode: bool (default False) Whether or not to decode UTF-8.
      kwargs: Other parameters to pass to self.get_file_content().

    Raises:
      RequestError: on error response from server.

    """
    response_string = self.get_file_content(uri, auth_token=auth_token)
    if googlecl.get_config_option(SECTION_HEADER, 'decode_utf_8', False, bool):
      try:
        file_string = response_string.decode('utf-8-sig')
      except UnicodeError, err:
        LOG.error('Could not decode: ' + str(err))
        file_string = response_string
    else:
      file_string = response_string
    with open(file_path, 'wb') as download_file:
      download_file.write(file_string)
      download_file.flush()

  def edit_doc(self, doc_entry_or_title, editor, file_format,
               folder_entry_or_path=None):
    """Edit a document.
    
    Keyword arguments:
      doc_entry_or_title: DocEntry of the existing document to edit,
                          or title of the document to create.
      editor: Name of the editor to use. Should be executable from the user's
              working directory.
      file_format: Suffix of the file to download.
                   For example, "txt", "csv", "xcl".
      folder_entry_or_path: Entry or string representing folder to upload into.
                   If a string, a new set of folders will ALWAYS be created.
                   For example, 'my_folder' to upload to my_folder,
                   'foo/bar' to upload into subfolder bar under folder foo.
                   Default None for root folder.
    
    """ 
    import subprocess
    import tempfile
    from gdata.docs.data import MIMETYPES
    
    try:
      doc_title = doc_entry_or_title.title.text
      new_doc = False
    except AttributeError:
      doc_title = doc_entry_or_title
      new_doc = True

    temp_dir = tempfile.mkdtemp()
    # If we're creating a new document and not given a folder entry
    if new_doc and isinstance(folder_entry_or_path, basestring):
      folder_path = os.path.normpath(folder_entry_or_path)
      # Some systems allow more than one path separator
      if os.altsep:
        folder_path.replace(os.altsep, os.sep)
      base_folder = folder_path.split(os.sep)[0]
      # Define the base path such that upload_docs will create a folder
      # named base_folder
      base_path = os.path.join(temp_dir, base_folder)
      total_basename = os.path.join(temp_dir, folder_path)
      os.makedirs(total_basename)
      path = os.path.join(total_basename, doc_title + '.' + file_format)
    else:
      path = os.path.join(temp_dir, doc_title + '.' + file_format)
      base_path = path

    if not new_doc:
      self.export(doc_entry_or_title.content.src, path)
      file_hash = googlecl.docs.base._md5_hash_file(path)
    else:
      file_hash = None

    subprocess.call([editor, path])
    if file_hash and file_hash == googlecl.docs.base._md5_hash_file(path):
      LOG.info('No modifications to file, not uploading.')
      return
    elif not os.path.exists(path):
      LOG.info('No file written, not uploading.')
      return
    
    if new_doc:
      if isinstance(folder_entry_or_path, basestring):
        # Let code in upload_docs handle the creation of new folder(s)
        self.upload_docs([base_path])
      else:
        # folder_entry_or_path is None or a GDataEntry.
        self.upload_single_doc(path, folder_entry=folder_entry_or_path)
    else:
      try:
        content_type = MIMETYPES[file_format.upper()]
      except KeyError:
        print 'Could not find mimetype for ' + file_format
        while file_format not in MIMETYPES.keys():
          file_format = raw_input('Please enter one of ' +
                                  SUPPORTED_FILETYPES.keys() + 
                                  ' for a content type to upload as.')
        content_type = MIMETYPES[file_format]
      mediasource = gdata.data.MediaSource(file_path=path,
                                           content_type=content_type)
      try:
        self.Update(doc_entry_or_title, media_source=mediasource)
      except gdata.client.RequestError, err:
        LOG.error(err)
        new_path = googlecl.docs.base.safe_move(path, '.')
        LOG.info('Moved edited document to ' + new_path)

    try:
      # Good faith effort to keep the temp directory clean.
      shutil.rmtree(temp_dir)
    except OSError:
      # Only seen errors on Windows, but catch the more general OSError.
      pass

  EditDoc = edit_doc

  def export(self, entry_or_id_or_url, file_path, gid=None, auth_token=None,
             **kwargs):
    """Exports a document from the Document List in a different format.

    Overloaded from docs.client.DocsClient to fix "always-download-as-pdf"
    issue

    Args:
      entry_or_id_or_url: gdata.docs.data.DocsEntry or string representing a
          resource id or URL to download the document from (such as the content
          src link).
      file_path: str The full path to save the file to.  The export
          format is inferred from the the file extension.
      gid: str (optional) grid id for downloading a single grid of a
          spreadsheet. The param should only be used for .csv and .tsv
          spreadsheet exports.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.download().

    Raises:
      gdata.client.RequestError if the download URL is malformed or the server's
      response was not successful.
    """
    extra_params = {}

    match = gdata.docs.data.FILE_EXT_PATTERN.match(file_path)
    if match:
      extra_params['exportFormat'] = match.group(1)
      # Fix issue with new-style docs always downloading to PDF
      # (gdata-issues Issue 2157)
      extra_params['format'] = match.group(1)

    if gid is not None:
      extra_params['gid'] = gid

    self.download(entry_or_id_or_url, file_path, extra_params,
                  auth_token=auth_token, **kwargs)

  Export = export

  def get_docs(self, base_path, entries, file_format=None):
    """Download documents.
    
    Keyword arguments:
      base_path: The path to download files to. This plus an entry's title plus
                 its format-specific extension will form the complete path.
      entries: List of DocEntry items representing the files to download.
      file_format: Suffix to give the file when downloading.
                   For example, "txt", "csv", "xcl". Default None to let
                   get_extension_from_doctype decide the extension.

    """
    if not os.path.isdir(base_path):
      if len(entries) > 1:
        raise googlecl.docs.base.DocsError('Target "' + base_path + 
                                           '" is not a directory')
      format_from_filename = googlecl.get_extension_from_path(base_path)
      if format_from_filename:
        # Strip the extension off here if it exists. Don't want to double up
        # on extension in for loop. (+1 for '.')
        base_path = base_path[:-(len(format_from_filename)+1)]
    else:
      format_from_filename = None
    default_format = 'txt'
    for entry in entries:
      if not file_format:
        file_format = format_from_filename or\
                      googlecl.docs.base.get_extension_from_doctype(
                                googlecl.docs.base.get_document_type(entry)) or\
                      default_format
      if os.path.isdir(base_path):
        path = os.path.join(base_path, entry.title.text + '.' + file_format)
      else:
        path = base_path + '.' + file_format
      LOG.info('Downloading ' + entry.title.text + ' to ' + path)
      try:
        self.export(entry, path)
      except gdata.client.RequestError, err:
        LOG.error('Download of ' + entry.title.text + ' failed: ' + str(err))
      except IOError, err:
        LOG.error(err)
        LOG.info('Does your destination filename contain invalid characters?')

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
                                       desired_class=gdata.docs.data.DocList))
    else:
      entries = self.GetEntries(gdata.docs.client.DOCLIST_FEED_URI,
                                title,
                                desired_class=gdata.docs.data.DocList)
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
                                   desired_class=gdata.docs.data.DocList)
      else:
        entries = self.get_doclist(title, folder_entry_list)
        # Technically don't need the desired_class for this call
        # because we have the entries.
        return self.GetSingleEntry(entries, title)
    else:
      return self.GetSingleEntry(gdata.docs.client.DOCLIST_FEED_URI,
                                 title,
                                 desired_class=gdata.docs.data.DocList)

  GetSingleDoc = get_single_doc

  def get_folder(self, title):
    """Return entries for one or more folders.

    Keyword arguments:
      title: Title of the folder.

    Returns:
      GDataEntry representing a folder, or None of title is None.

    """
    if title:
      uri = gdata.docs.client.DOCLIST_FEED_URI + '-/folder'
      folder_entries = self.GetEntries(uri, title=title)
      if not folder_entries:
        LOG.warning('No folder found that matches ' + title)
      return folder_entries
    else:
      return None

  GetFolder = get_folder

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid."""
    if not test_uri:
      docs_uri = gdata.docs.client.DOCLIST_FEED_URI
      sheets_uri = \
               'https://spreadsheets.google.com/feeds/spreadsheets/private/full'
    docs_test = googlecl.client.BaseClientCL.IsTokenValid(self, docs_uri)
    sheets_test = googlecl.client.BaseClientCL.IsTokenValid(self, sheets_uri)
    return docs_test and sheets_test

  IsTokenValid = is_token_valid

  def request_access(self, domain, node, scopes=None):
    """Request access as in BaseClientCL, but specify scopes."""
    # When people use docs (writely), they expect access to
    # spreadsheets as well (wise).
    if not scopes:
      scopes = gdata.gauth.AUTH_SCOPES['writely'] +\
               gdata.gauth.AUTH_SCOPES['wise']
    return googlecl.client.BaseClientCL.request_access(self, domain, node,
                                                       scopes=scopes)

  RequestAccess = request_access

  def upload_docs(self, paths, title=None, folder_entry=None,
                  file_format=None):
    """Upload a list of documents or directories.
    
    For each item in paths:
      if item is a directory, upload all files found in the directory
        in a manner roughly equivalent to "cp -R directory/ <docs_folder>"
      if item is a file, upload that file to <docs_folder>

    Keyword arguments:
      paths: List of file paths and/or directories to upload.
      title: Title to give the files once uploaded.
             Default None for the names of the files.
      folder_entry: GDataEntry of the folder to treat as the new root for
                    directories/files.
                    Default None for no folder (the Google Docs root).
      file_format: Replace (or specify) the extension on the file when figuring
              out the upload format. For example, 'txt' will upload the
              file as if it was plain text. Default None for the file's
              extension (which defaults to 'txt' if there is none).

    Returns:
      Dictionary mapping filenames to where they can be accessed online.
    
    """
    url_locs = {}
    for path in paths:
      folder_root = folder_entry
      if os.path.isdir(path):
        folder_entries = {}
        # final '/' sets folder_name to '' which causes
        # 503 "Service Unavailable". 
        path = path.rstrip('/')
        for dirpath, dirnames, filenames in os.walk(path):
          directory = os.path.dirname(dirpath)
          folder_name = os.path.basename(dirpath)
          if directory in folder_entries:
            fentry = self.create(gdata.docs.data.FOLDER_LABEL, folder_name,
                                 folder_entries[directory])
          else:
            fentry = self.create(gdata.docs.data.FOLDER_LABEL, folder_name,
                                 folder_root)
          folder_entries[dirpath] = fentry
          LOG.debug('Created folder ' + dirpath + ' ' + folder_name)
          for fname in filenames:
            loc = self.upload_single_doc(os.path.join(dirpath, fname),
                                         folder_entry=fentry)
            if loc:
              url_locs[fname] = loc
      else:
        loc = self.upload_single_doc(path, title=title,
                                     folder_entry=folder_entry,
                                     file_format=file_format)
        if loc:
          url_locs[os.path.basename(path)] = loc
    return url_locs

  UploadDocs = upload_docs

  def upload_single_doc(self, path, title=None, folder_entry=None,
                        file_format=None):
    import mimetypes

    filename = os.path.basename(path)
    content_type = None
    if file_format:
      from gdata.docs.data import MIMETYPES
      try:
        content_type = MIMETYPES[file_format.upper()]
      except KeyError:
        LOG.info('No supported filetype found for extension ' + file_format +
                 ', letting mimetypes module guess mime type')
    if not content_type:
      content_type = mimetypes.guess_type(path)[0]
    LOG.debug('Uploading with MIME type: ' + content_type)
    LOG.info('Loading ' + path)
    entry_title = title or filename.split('.')[0]
    try:
      new_entry = self.upload(path, entry_title, folder_entry, content_type)
    except gdata.client.RequestError, err:
      LOG.error('Failed to upload ' + path + ': ' + str(err))
      if err.args[0].find('ServiceForbiddenException') != -1:
        LOG.info('You may have to specify a format with --format. Try ' +
                 '--format=txt')
      return None
    else:
      LOG.info('Upload success! Direct link: ' +
               new_entry.GetAlternateLink().href)
    return new_entry.GetAlternateLink().href

  UploadSingleDoc = upload_single_doc


SERVICE_CLASS = DocsClientCL


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
    LOG.error('Downloading documents is not supported for' +
              ' gdata-python-client < 2.0')
    return
  if not args:
    path = os.getcwd()
  else:
    path = args[0]
  folder_entries = client.get_folder(options.folder)
  entries = client.get_doclist(options.title, folder_entries)
  try:
    client.get_docs(path, entries, file_format=options.format)
  except googlecl.docs.base.DocsError, err:
    LOG.error(err)


def _run_list(client, options, args):
  folder_entries = client.get_folder(options.folder)
  entries = client.get_doclist(options.title, folder_entries)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = googlecl.get_config_option(SECTION_HEADER,
                                            'list_style').split(',')
  for entry in entries:
    print googlecl.base.compile_entry_string(
                               googlecl.base.BaseEntryToStringWrapper(entry),
                               style_list,
                               delimiter=options.delimiter)


def _run_upload(client, options, args):
  if not args:
    LOG.error('Need to tell me what to upload!')
    return
  folder_entries = client.get_folder(options.folder)
  folder_entry = client.get_single_entry(folder_entries)
  client.upload_docs(args, title=options.title, folder_entry=folder_entry,
                     file_format=options.format)


def _run_edit(client, options, args):
  if not hasattr(client, 'Export'):
    LOG.error('Editing documents is not supported' +
              ' for gdata-python-client < 2.0')
    return
  folder_entry_list = client.get_folder(options.folder)
  doc_entry = client.get_single_doc(options.title, folder_entry_list)
  if doc_entry:
    doc_entry_or_title = doc_entry
    doc_type = googlecl.docs.base.get_document_type(doc_entry)
  else:
    doc_entry_or_title = options.title
    doc_type = None
    LOG.debug('No matching documents found! Will create one.')
  folder_entry = client.get_single_entry(folder_entry_list)
  if not folder_entry and options.folder:
    # Don't tell the user no matching folders were found if they didn't
    # specify one.
    LOG.debug('No matching folders found! Will create them.')
  format_ext = options.format or\
               googlecl.docs.base.get_extension_from_doctype(doc_type)
  editor = options.editor or googlecl.docs.base.get_editor(doc_type)
  if not editor:
    LOG.error('No editor defined!')
    LOG.info('Define an "editor" option in your config file, set the ' +
             'EDITOR environment variable, or pass an editor in with --editor.')
    return
  if not format_ext:
    LOG.error('No format defined!')
    LOG.info('Define a "format" option in your config file,' +
             ' or pass in a format with --format')
    return
  LOG.debug('format_ext: ' + format_ext)
  client.edit_doc(doc_entry_or_title, editor, format_ext,
                  folder_entry_or_path=folder_entry or options.folder)


def _run_delete(client, options, args):
  entries = client.get_doclist(options.title)
  client.DeleteEntryList(entries, 'document',
                googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


TASKS = {'upload': googlecl.base.Task('Upload a document',
                                      callback=_run_upload,
                                      optional=['title', 'folder', 'format'],
                                      args_desc='PATH_TO_FILE'),
         'edit': googlecl.base.Task('Edit a document', callback=_run_edit,
                                    required=['title'],
                                    optional=['format', 'editor', 'folder']),
         'get': googlecl.base.Task('Download a document', callback=_run_get,
                                   required=[['title', 'folder']],
                                   optional='format',
                                   args_desc='LOCATION'),
         'list': googlecl.base.Task('List documents', callback=_run_list,
                                    required='delimiter',
                                    optional=['title', 'folder']),
         'delete': googlecl.base.Task('Delete documents',
                                      callback=_run_delete,
                                      optional='title')}
