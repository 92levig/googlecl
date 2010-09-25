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
    import os.path
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


class ContactsEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  @property
  def address(self):
    """Postal addresses."""
    if self.entry.postal_address:
      # For v1 of gdata ("service" modules)?
      return self._join(self.entry.postal_address, text_attribute='text')
    else:
      # For v3 of gdata ("client" modules)?
      get_address_text = \
          lambda address: getattr(getattr(address, 'formatted_address'), 'text')
      return self._join(self.entry.structured_postal_address,
                        text_extractor=get_address_text)
  where = address

  @property
  def birthday(self):
    """Birthday."""
    return self.entry.birthday.when
  bday=birthday

  @property
  def email(self):
    """Email addresses."""
    return self._join(self.entry.email, text_attribute='address')

  @property
  def event(self):
    """Events such as anniversaries and birthdays."""
    get_start_time = lambda event: getattr(getattr(event, 'when'), 'start')
    events = self._join(self.entry.event, text_extractor=get_start_time,
                        label_attribute='rel')
    # Birthdays are technically their own element, but add them in here because
    # that policy is silly (as far as the end user is concerned).
    if self.label_delimiter is None:
      return events + ' ' + self.birthday
    else:
      label = ' birthday%s' % self.label_delimiter
      return events + self.intra_property_delimiter + label + self.birthday
  events = event
  dates = event
  when = event

  @property
  def im(self):
    """Instant messanger handles."""
    return self._join(self.entry.im, text_attribute='address',
                      label_attribute='protocol')

  @property
  def job(self):
    return self.title + ' at '  + self.organization

  @property
  def notes(self):
    """Additional notes."""
    return self.entry.content.text

  @property
  def nickname(self):
    return self.entry.nickname.text

  @property
  def organization(self):
    """Name of the organization/employer."""
    try:
      # For v1 of gdata ("service" modules)?
      return self.entry.organization.org_name.text
    except AttributeError:
      # For v3 of gdata ("client" modules)?
      return self.entry.organization.name.text
  company = organization

  @property
  def phone_number(self):
    """Phone numbers."""
    return self._join(self.entry.phone_number, text_attribute='text')
  phone = phone_number

  @property
  def relation(self):
    """Relationships."""
    return self._join(self.entry.relation, text_attribute='text')
  relations = relation

  @property
  # Overrides Base's title. "name" will still give name of contact.
  def title(self):
    """Title of contact in organization."""
    try:
      # For v1 of gdata ("service" modules)?
      return self.entry.organization.org_title.text
    except AttributeError:
      # For v3 of gdata ("client" modules)?
      return self.entry.organization.title.text
  org_title = title

  @property
  def user_defined(self):
    """User defined fields."""
    return self._join(self.entry.user_defined_field, text_attribute='value',
                      label_attribute='key')
  other = user_defined

  @property
  def website(self):
    """Websites."""
    return self._join(self.entry.website, text_attribute='href')
  links = website


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
  entries = client.GetContacts(options.title)
  for entry in entries:
    print googlecl.base.compile_entry_string(
                                            ContactsEntryToStringWrapper(entry),
                                            options.fields.split(','),
                                            delimiter=options.delimiter)


def _run_add(client, options, args):
  for contact in options.src:
    client.add_contact_string(contact)


def _run_delete(client, options, args):
  # XXX: This will change soon, but for right now, only accept the title
  # (of which there can only be one. That's the part that will change)
  for name in [options.title]:
    entries = client.GetContacts(name)
    client.DeleteEntryList(entries, 'contact',
                  googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


def _run_add_groups(client, options, args):
  # XXX: This will change soon, but for right now, only accept the title
  # (of which there can only be one. That's the part that will change)
  for group in [options.title]:
    client.AddGroup(group)


def _run_delete_groups(client, options, args):
  # XXX: This will change soon, but for right now, only accept the title
  # (of which there can only be one. That's the part that will change)
  for group in [options.title]:
    entries = client.GetGroups(group)
    client.DeleteEntryList(entries, 'group',
                  googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


def _run_list_groups(client, options, args):
  for group in [options.title]:
    entries = client.GetGroups(group)
    for entry in entries:
      print googlecl.base.compile_entry_string(
                                           ContactsEntryToStringWrapper(entry),
                                           ['name'],
                                           delimiter=options.delimiter)


TASKS = {'list': googlecl.base.Task('List contacts', callback=_run_list,
                                    required=['fields', 'title', 'delimiter']),
         'add': googlecl.base.Task('Add contacts', callback=_run_add,
                                   required='src'),
         'delete': googlecl.base.Task('Delete contacts', callback=_run_delete,
                                      required='title'),
         'add-groups': googlecl.base.Task('Add contact group(s)',
                                          callback=_run_add_groups,
                                          required='title'),
         'delete-groups': googlecl.base.Task('Delete contact group(s)',
                                             callback=_run_delete_groups,
                                             required='title'),
         'list-groups': googlecl.base.Task('List contact groups',
                                           callback=_run_list_groups,
                                           required='title')}
