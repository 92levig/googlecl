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
import gdata.contacts.service
import googlecl
import googlecl.service
import googlecl.base
from googlecl.contacts import SECTION_HEADER


LOG = logging.getLogger(googlecl.contacts.LOGGER_NAME)


class ContactsServiceCL(gdata.contacts.service.ContactsService,
                        googlecl.service.BaseServiceCL):
  
  """Extends gdata.contacts.service.ContactsService for the command line.

  This class adds some features focused on using Contacts via an installed
  app with a command line interface.

  """

  def __init__(self):
    """Constructor."""
    gdata.contacts.service.ContactsService.__init__(self)
    googlecl.service.BaseServiceCL.__init__(self, SECTION_HEADER)

  def add_contact(self, string_or_csv_file):
    """Add contact(s).
    
    Keyword arguments:
      string_or_csv_file: String representing a name/email address to add, or
                          a path to a csv file of such strings. Entries should
                          be of the form "name,email@server.com" (whitespace
                          before/after the comma is ignored).

    """
    import atom
    import os.path
    if os.path.exists(string_or_csv_file):
      with open(string_or_csv_file, 'r') as contacts_csv_file:
        for line in contacts_csv_file:
          if line.strip():    # filter out empty lines
            self.add_contact(line)
    else:
      try:
        name, email = string_or_csv_file.split(',')
      except ValueError:
        LOG.error(string_or_csv_file +
                  ' is neither a name,email pair nor a file.')
        return
      new_contact = gdata.contacts.ContactEntry(title=atom.Title(
                                                             text=name.strip()))
      new_contact.email.append(gdata.contacts.Email(address=email.strip()))
      try:
        self.CreateContact(new_contact)
      except gdata.service.RequestError, err:
        if err.args[0]['reason'] == 'Conflict':
          LOG.error('Already have a contact for e-mail address ' +
                    email.strip())
        else:
          raise 

  AddContact = add_contact

  def get_contacts(self, name):
    """Get all contacts that match a name."""
    uri = self.GetFeedUri()
    return self.GetEntries(uri, name,
                           converter=gdata.contacts.ContactsFeedFromString)

  GetContacts = get_contacts

  def add_group(self, name):
    """Add group."""
    import atom
    new_group = gdata.contacts.GroupEntry(title=atom.Title(text=name))
    self.CreateGroup(new_group)

  AddGroup = add_group

  def get_groups(self, name):
    """Get all groups that match a name."""
    uri = self.GetFeedUri(kind='groups')
    return self.GetEntries(uri, name,
                           converter=gdata.contacts.GroupsFeedFromString)

  GetGroups = get_groups

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid."""
    if not test_uri:
      test_uri = self.GetFeedUri()
    return googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid


SERVICE_CLASS = ContactsServiceCL


class ContactsEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  @property
  def address(self):
    """Postal addresses."""
    return self._join(self.entry.postal_address, text_attribute='text')

  @property
  def company(self):
    """Name of company."""
    return self.entry.organization.org_name.text
  org_name = company

  @property
  def email(self):
    """Email addresses."""
    return self._join(self.entry.email, text_attribute='address')

  @property
  def im(self):
    """Instant messanger handles."""
    return self._join(self.entry.im, text_attribute='address',
                      label_attribute='protocol')

  @property
  def notes(self):
    """Additional notes."""
    return self.entry.content.text

  @property
  def phone_number(self):
    """Phone numbers."""
    return self._join(self.entry.phone_number, text_attribute='text')
  phone = phone_number

  @property
  # Overrides Base's title. "name" will still give name of contact.
  def title(self):
    """Title of contact in organization."""
    return self.entry.organization.org_title.text
  org_title = title


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#  
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_list(client, options, args):
  # XXX: see issue 89, use --fields instead of args, use args instead of --title
  # but support --title for backward compatibility, as in _run_delete
  entries = client.GetContacts(options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = googlecl.get_config_option(SECTION_HEADER,
                                            'list_style').split(',')
  for entry in entries:
    print googlecl.base.compile_entry_string(
                                            ContactsEntryToStringWrapper(entry),
                                            style_list,
                                            delimiter=options.delimiter)

def _run_add(client, options, args):
  for contact in args:
    client.add_contact(contact)


def _run_delete(client, options, args):
  # Supporting --title for backward compatibility
  if options.title is not None:
    args.append(options.title)
  if len(args) == 0:
    LOG.error('No contacts specified. Try: google contacts delete "John Doe"')
    return
  for name in args:
    entries = client.GetContacts(name)
    client.DeleteEntryList(entries, 'contact',
                  googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


def _run_add_groups(client, options, args):
  for group in args:
    client.AddGroup(group)


def _run_delete_groups(client, options, args):
  if len(args) == 0:
    LOG.error('No groups specified. Try: ' +
              'google contacts delete-groups "In-laws"')
    return
  for group in args:
    entries = client.GetGroups(group)
    client.DeleteEntryList(entries, 'group',
                  googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


def _run_list_groups(client, options, args):
  if len(args) == 0:
    args.append(None)

  for group in args:
    entries = client.GetGroups(group)
    for entry in entries:
      print googlecl.base.compile_entry_string(
                                           ContactsEntryToStringWrapper(entry),
                                           ['title'],
                                           delimiter=options.delimiter)


TASKS = {'list': googlecl.base.Task('List contacts', callback=_run_list,
             args_desc='Fields to show (example: name,email)'),
         'add': googlecl.base.Task('Add contacts', callback=_run_add,
             args_desc='"name,email" pair or CSV filename'),
         'delete': googlecl.base.Task('Delete contacts',
             callback=_run_delete,
        args_desc='names of contact(s) to delete (e.g. "John Doe" "Jane Doe")'),
         'add-groups': googlecl.base.Task('Add contact group(s)',
                                             callback=_run_add_groups,
                                             args_desc='Group name(s)'),
         'delete-groups': googlecl.base.Task('Delete contact group(s)',
                                                callback=_run_delete_groups,
                                                args_desc='Group name(s)'),
         'list-groups': googlecl.base.Task('List contact groups',
             callback=_run_list_groups,
             args_desc='Specific groups to list (if any)')}

