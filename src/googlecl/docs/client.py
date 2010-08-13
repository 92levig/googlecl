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
                   googlecl.docs.base.DocsBaseCL,
                   googlecl.client.BaseClientCL):
  
  """Extends gdata.docs.client.DocsClient for the command line.
  
  This class adds some features focused on using Google Docs via an installed
  app with a command line interface.
  
  """

  def __init__(self):
    """Constructor.""" 
    gdata.docs.client.DocsClient.__init__(self, source='GoogleCL')
    googlecl.client.BaseClientCL.__init__(self, section=SECTION_HEADER)

  def _create_folder(self, title, folder_or_uri):
    """Wrapper function to mesh with DocsBaseCL.upload_docs()."""
    return self.create(gdata.docs.data.FOLDER_LABEL, title,
                       folder_or_uri)

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
    if googlecl.docs.base.can_export(uri) and\
       googlecl.get_config_option(SECTION_HEADER, 'decode_utf_8', False, bool):
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

  def _modify_entry(self, doc_entry, path_to_new_content, file_ext):
    """Replace content of a DocEntry.

    Args:
      doc_entry: DocEntry whose content will be replaced.
      path_to_new_content: str Path to file that has new content.
      file_ext: str Extension to use to determine MIME type of upload
                (e.g. 'txt', 'doc')

    """
    from gdata.docs.data import MIMETYPES
    try:
      content_type = MIMETYPES[file_ext.upper()]
    except KeyError:
      print 'Could not find mimetype for ' + file_ext
      while file_ext not in MIMETYPES.keys():
        file_ext = raw_input('Please enter one of ' +
                                MIMETYPES.keys() + 
                                ' to determine the content type to upload as.')
      content_type = MIMETYPES[file_ext.upper()]
    mediasource = gdata.data.MediaSource(file_path=path_to_new_content,
                                         content_type=content_type)
    self.Update(doc_entry, media_source=mediasource)

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

  def upload_single_doc(self, path, title=None, folder_entry=None,
                        file_ext=None, **kwargs):
    """Upload one file to Google Docs.
    
    Args:
      path: str Path to file to upload.
      title: str (optional) Title to give the upload. Defaults to the filename.
      folder_entry: DocsEntry (optional) (sub)Folder to upload into.
      file_ext: str (optional) Extension used to determine MIME type of
                upload. If not specified, uses mimetypes module to guess it.
      kwargs: Should contain value for 'convert', either True or False.
              Indicates if upload should be converted. Only Apps Premier
              users can specify False.

    Returns:
      str Link to the document on Google Docs

    """
    import mimetypes
    try:
      convert = kwargs['convert']
    except KeyError:
      convert = True

    filename = os.path.basename(path)
    content_type = None
    if file_ext:
      from gdata.docs.data import MIMETYPES
      try:
        content_type = MIMETYPES[file_ext.upper()]
      except KeyError:
        LOG.info('No supported filetype found for extension ' + file_ext +
                 ', letting mimetypes module guess mime type')
    if not content_type:
      content_type = mimetypes.guess_type(path)[0]
      if not content_type:
        if convert:
          content_type = 'text/plain'
        else:
          content_type = 'application/octet-stream'
        LOG.debug('mimetypes could not figure out type for ' + path +
                  ', setting to ' + content_type)
    LOG.debug('Uploading with MIME type: ' + content_type)
    LOG.info('Loading ' + path)
    entry_title = title or filename.split('.')[0]

    if not folder_entry:
      post_uri = gdata.docs.client.DOCLIST_FEED_URI
    else:
      post_uri = folder_entry.content.src
    if not convert:
      post_uri += '?convert=false'

    try:
      new_entry = self.upload(path, entry_title, post_uri, content_type)
    except gdata.client.RequestError, err:
      LOG.error('Failed to upload ' + path + ': ' + str(err))
      if err.args[0].find('ServiceForbiddenException') != -1:
        if convert:
          LOG.info('You may have to specify a format with --format. Try ' +
                   '--format=txt')
        else:
          LOG.info('Only Apps Premier users can upload arbitrary file types ' +
                   'without using the Google Docs web uploader.')
      return None
    else:
      LOG.info('Upload success! Direct link: ' +
               new_entry.GetAlternateLink().href)
    return new_entry.GetAlternateLink().href

  UploadSingleDoc = upload_single_doc


SERVICE_CLASS = DocsClientCL


TASKS = googlecl.docs.base.TASKS
