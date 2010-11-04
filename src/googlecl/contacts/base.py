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


"""Service details and instances for the Contacts service.

Some use cases:
Add contacts:
  contacts add "Bob Smith, bob@smith.com" "Jim Raynor, jimmy@noreaster.com"

List contacts:
  contacts list title,email

"""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import logging
import googlecl.contacts
import os.path


LOG = logging.getLogger(googlecl.contacts.LOGGER_NAME)

class ContactsBaseCL(object):
  """Class inherited by either ContactsServiceCL or ContactsClientCL. """

  def add_contact_string(self, string_or_csv_file):
    """Add contact(s).

    Keyword arguments:
      string_or_csv_file: String representing a name/email address to add, or
                          a path to a csv file of such strings. Entries should
                          be of the form "name,email@server.com" (whitespace
                          before/after the comma is ignored).
    """
    if os.path.exists(string_or_csv_file):
      with open(string_or_csv_file, 'r') as contacts_csv_file:
        for line in contacts_csv_file:
          if line.strip():    # filter out empty lines
            self.add_contact_string(line)
    else:
      contact_entry = self.parse_contact_string(string_or_csv_file)
      if contact_entry:
        try:
          self.CreateContact(contact_entry)
        except self.request_error, err:
          LOG.error(err)

  AddContactString = add_contact_string
