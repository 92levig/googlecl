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
import ConfigParser
import logging
import os
import shutil
import googlecl
from googlecl.docs import SECTION_HEADER


LOG = logging.getLogger(googlecl.docs.LOGGER_NAME + '.base')


# gdata 1.2.4 doesn't have these defined, but uses them along with
# a namespace definition.
try:
  from gdata.docs.data import DOCUMENT_LABEL, SPREADSHEET_LABEL, \
                              PRESENTATION_LABEL, FOLDER_LABEL, PDF_LABEL
except ImportError:
  DOCUMENT_LABEL = 'document'
  SPREADSHEET_LABEL = 'spreadsheet'
  PRESENTATION_LABEL = 'presentation'
  FOLDER_LABEL = 'folder'
  PDF_LABEL = 'pdf'


class DocsError(googlecl.base.Error):
  """Base error for Docs errors."""
  pass

class UnexpectedExtension(DocsError):
  """Found an unexpected filename extension."""
  def __str__(self):
    if len(self.args) == 1:
      return 'Unexpected extension: ' + str(self.args[0])
    else:
      return str(self.args)

class UnknownDoctype(DocsError):
  """Document type / label is unknown."""
  def __str__(self):
    if len(self.args) == 1:
      return 'Unknown document type: ' + str(self.args[0])
    else:
      return str(self.args)


# Read size is 128*20 for no good reason.
# Just want to avoid reading in the whole file, and read in a multiple of 128.
def _md5_hash_file(path, read_size=2560):
  """Return a binary md5 checksum of file at path."""
  import hashlib
  hash_function = hashlib.md5()
  with open(path, 'r') as my_file:
    data = my_file.read(read_size)
    while data:
      hash_function.update(data)
      data = my_file.read(read_size)
  return hash_function.digest()


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


def get_extension_from_doctype(doctype_label):
  """Return file extension based on document type and preferences file."""
  LOG.debug('In get_extension_from_doctype, doctype_label: ' +
             str(doctype_label))
  try:
    if doctype_label == SPREADSHEET_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'spreadsheet_format')
    elif doctype_label == DOCUMENT_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'document_format')
    elif doctype_label == PDF_LABEL:
      return 'pdf'
    elif doctype_label == PRESENTATION_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'presentation_format')
    else:
      raise UnknownDoctype(doctype_label)
  except ConfigParser.NoOptionError, err:
    LOG.error(err)
  except UnknownDoctype, err:
    if doctype_label is not None:
      LOG.error(err)

  try:
    return googlecl.CONFIG.get(SECTION_HEADER, 'format')
  except ConfigParser.NoOptionError, err:
    LOG.error(err)
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
  LOG.debug('In get_editor, doctype_label: ' + str(doctype_label))
  try:
    if doctype_label == SPREADSHEET_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'spreadsheet_editor')
    elif doctype_label == DOCUMENT_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'document_editor')
    elif doctype_label == PDF_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'pdf_editor')
    elif doctype_label == PRESENTATION_LABEL:
      return googlecl.CONFIG.get(SECTION_HEADER, 'presentation_editor')
    else:
      raise UnknownDoctype(doctype_label)
  except ConfigParser.NoOptionError, err:
    LOG.error(err)
  except UnknownDoctype, err:
    if doctype_label is not None:
      LOG.error(err)

  try:
    return googlecl.CONFIG.get(SECTION_HEADER, 'editor')
  except ConfigParser.NoOptionError, err:
    LOG.error(err)
  return os.getenv('EDITOR')


def safe_move(src, dst):
  """Move file from src to dst.

  If file with same name already exists at dst, rename the new file
  while preserving the extension.

  Returns:
    path to new file.

  """
  new_dir = os.path.abspath(dst)
  ext = googlecl.get_extension_from_path(src)
  if not ext:
    dotted_ext = ''
  else:
    dotted_ext = '.' + ext
  filename = os.path.basename(src).rstrip(dotted_ext)
  rename_num = 1
  new_path = os.path.join(new_dir, filename + dotted_ext)
  while os.path.exists(new_path):
    new_filename = filename + '-' + str(rename_num) + dotted_ext
    new_path = os.path.join(new_dir, new_filename) 
  shutil.move(src, new_path)
  return new_path
