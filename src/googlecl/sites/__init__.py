# Copyright (C) 2013 Google Inc.
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
import googlecl
import gdata.client
import googlecl.base
import logging
import os
import re
import urllib

service_name = __name__.split('.')[-1]
LOGGER_NAME = __name__
SECTION_HEADER = service_name.upper()
LOG = logging.getLogger(LOGGER_NAME)


class Error():
  pass


def _check_and_set_domain_and_site(client, options, site_optional=False):
  if options.domain:
    client.domain = options.domain
  else:
    domain = client.config.lazy_get(SECTION_HEADER, 'domain')
    if domain:
      client.domain = options.domain

  if options.site:
    site = options.site
  else:
    site = client.config.lazy_get(SECTION_HEADER, 'site')
  if site:
    client.site=urllib.quote_plus(site)
  elif not site_optional:
    LOG.error('You must specify --site for this command')
    return
  LOG.info('domain=%s, site=%s' % (client.domain, client.site))



#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================

def _run_sites(client, options, args):
  """Show top level listing of site."""
  _check_and_set_domain_and_site(client, options, site_optional=True)
  # Change default to appropriate name for sites.
  if (options.fields.count('page_name') and not
      options.fields.count('site_name')):
    options.fields = options.fields.replace('page_name', 'site_name', 1)
  sites = client.GetSiteFeed()
  for entry in sites.entry:
    print googlecl.base.compile_entry_string(
        googlecl.base.BaseEntryToStringWrapper(entry),
        options.fields.split(','),
        delimiter=options.delimiter)

def _run_list(client, options, args):
  """Return content for site.

     The max_results config parameter can be set to get more entries.
     The --query flag works here.
     We also allow optional arguments that do several kinds of search.
     https://developers.google.com/google-apps/sites/docs/1.0/reference#Parameters
     https://developers.google.com/google-apps/sites/docs/1.0/developers_guide_protocol
  """
  _check_and_set_domain_and_site(client, options)
  uri = client.MakeContentFeedUri()

  delimiter = '?'  # Need to know what delimiter to use on uri

  if options.max_results:
    max_results = options.max_results
  else:
    max_results = client.config.lazy_get(SECTION_HEADER, 'max_results')
  if max_results:
    uri += '?max-results=%s' % max_results
    delimiter = '&'

  query_args = []
  if options.query:
    query_args.append(('q', options.query))

  if args:
    # I suppose that we should try and protect this mapping somehow. But I
    # don't think it is exploitable???
    # NOTE: if user tries "-/filecabinet" syntax, it will not end well. (ValueError)
    query_args.extend([tuple(a.split('=', 1)) for a in args])

  if query_args:
    query_args = urllib.urlencode(query_args)
    uri += delimiter + query_args

  LOG.info('uri=%s' % uri)
  feed = client.GetContentFeed(uri=uri)

  for entry in feed.entry:
    #print 'entry=%s' % entry
    print googlecl.base.compile_entry_string(
        googlecl.base.BaseEntryToStringWrapper(entry),
        options.fields.split(','),
        delimiter=options.delimiter)

def _run_upload(client, options, args):
  """Upload a sites page.

     Really, we read the file and pass the contents up in the call.
     Yuck, but that's the API. We draft the doc parameters:
       title: page title. Used to create page_name. Default: filename.
       src: File to read from.
       format: Site's "kind", e.g. "webpage", "filecabinet". Default: webpage.
       folder: If given, the title of the page we want to put this page under.
  """
  _check_and_set_domain_and_site(client, options)
  # Get file src.
  try:
    with open(options.src[0], 'r') as f:
      src = f.read()
  except IOError as err:
    LOG.error(err)
    return

  if not options.title:
    options.title = options.src
  # Look for parent if folder given.
  if options.folder:
    if not options.folder.startswith('/'):
      options.folder = '/' + options.folder
    uri = client.MakeContentFeedUri() + '?path=' + options.folder
    feed = client.GetContentFeed(uri=uri)
    if not feed.entry:
      LOG.error("Couldn't find Site page %s" % options.folder)
      return
    parent = feed.entry[0]
  else:
    parent = None

  # There's no API to check kind, so we take it on faith. Default webpage.
  if not options.format:
    options.format = 'webpage'

  try:
    entry = client.CreatePage(options.format, options.title[0], html=src,
                              parent=parent)
  except gdata.client.RequestError as err:
    LOG.error('Site page creation failed: %s' % err)
    return
  LOG.info('created page %s (%s) at %s', entry.title.text,
           entry.page_name.text, entry.GetAlternateLink().href)

def _run_delete(client, options, args):
  """Delete a sites page.
       title: /path/to/page of page to delete.
  """
  _check_and_set_domain_and_site(client, options)
  if not options.title.startswith('/'):
    options.title = '/' + options.title
  uri = client.MakeContentFeedUri() + '?path=' + options.title
  feed = client.GetContentFeed(uri=uri)
  if not feed.entry:
    LOG.error("Couldn't find Site page %s" % options.title)
    return
  entry = feed.entry[0]
  LOG.info('deleting page %s (%s) at %s', entry.title.text,
           entry.page_name.text, entry.GetAlternateLink().href)
  client.Delete(entry)


TASKS = {
         'sites': googlecl.base.Task(
             'List all sites user can access (site feed)',
             callback=_run_sites,
             required=['fields', 'delimiter'],
             optional=['domain', 'site']),
         'list': googlecl.base.Task(
             "List site's contents with optional query (site content)",
             callback=_run_list,
             required=['fields', 'delimiter'],
             optional=['domain', 'site', 'max_results', 'query']),
         'upload': googlecl.base.Task(
             'Upload a Sites page',
             callback=_run_upload,
             required=['site', 'src'],
             optional=['domain', 'title', 'folder', 'format']),
         'delete': googlecl.base.Task(
             'Delete a Sites page',
             callback=_run_delete,
             required=['site', 'title'],
             optional=['domain']),
        }
