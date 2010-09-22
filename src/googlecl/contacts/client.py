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
import atom
import logging
import gdata.contacts.client
import googlecl.client
import googlecl.base
import googlecl.contacts.base
from googlecl.contacts import SECTION_HEADER


LOG = logging.getLogger(googlecl.contacts.LOGGER_NAME + '.client')


class ContactsClientCL(gdata.contacts.client.ContactsClient,
                       googlecl.contacts.base.ContactsBaseCL,
                       googlecl.client.BaseClientCL):

  """Extends gdata.contacts.service.ContactsService for the command line.

  This class adds some features focused on using Contacts via an installed
  app with a command line interface.

  """

  def __init__(self):
    """Constructor."""
    gdata.contacts.client.ContactsClient.__init__(self)
    googlecl.client.BaseClientCL.__init__(self, SECTION_HEADER)

  def parse_contact_string(self, contact_string):
    """Add contact(s).

    Keyword arguments:
      contact_string: String representing a name/email address to add
                      Entries should be of the form "name,email@server.com"
                      (whitespace before/after the comma is ignored).

    Returns:
      ContactEntry with at least name and email filled in.

    """
    try:
      name, email = contact_string.split(',')
    except ValueError:
      LOG.error(contact_string + ' is not a name,email pair nor a file.')
      return
    new_contact = gdata.contacts.data.ContactEntry()
    new_contact.name = gdata.data.Name()
    new_contact.name.full_name = gdata.data.FullName(text=name.strip())
    new_contact.email.append(gdata.data.Email(address=email.strip(),
                                              label='Home'))
    return new_contact

  def get_contacts(self, name):
    """Get all contacts that match a name."""
    uri = self.GetFeedUri()
    return self.GetEntries(uri, name,
                           desired_class=gdata.contacts.data.ContactsFeed)

  GetContacts = get_contacts

  def add_group(self, name):
    """Add group."""
    new_group = gdata.contacts.data.GroupEntry()
    new_group.title = atom.data.Title(text=name)
    self.CreateGroup(new_group)

  AddGroup = add_group

  def get_groups(self, name):
    """Get all groups that match a name."""
    uri = self.GetFeedUri(kind='groups')
    return self.GetEntries(uri, name,
                           desired_class=gdata.contacts.data.GroupsFeed)

  GetGroups = get_groups

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid."""
    if not test_uri:
      test_uri = self.GetFeedUri()
    return googlecl.client.BaseClientCL.is_token_valid(self, test_uri)

  IsTokenValid = is_token_valid


SERVICE_CLASS = ContactsClientCL


TASKS = googlecl.contacts.base.TASKS
