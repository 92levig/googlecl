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


"""Service details and instances for the Blogger service."""


from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import atom
import gdata
import logging
import os
import googlecl
import googlecl.base
import googlecl.service
from googlecl.blogger import SECTION_HEADER


LOG = logging.getLogger(googlecl.blogger.LOGGER_NAME)


class BlogNotFound(googlecl.base.Error):
  """Specified blog is not found."""
  def __str__(self):
    if len(self.args) == 2:
      return str(self.args[0]) + ': ' + str(self.args[1])
    else:
      return self.args


class BloggerServiceCL(gdata.service.GDataService,
                       googlecl.service.BaseServiceCL):

  """Command-line-friendly service for the Blogger API.

  Some of this is based off gdata/samples/blogger/BloggerExampleV1.py

  """

  def __init__(self):
    """Constructor."""
    gdata.service.GDataService.__init__(self, service='blogger',
                                        server='www.blogger.com',
                                        account_type='GOOGLE')
    googlecl.service.BaseServiceCL.__init__(self, SECTION_HEADER)

  def add_post(self, post_title, content, blog_title=None, is_draft=False):
    """Add a post.

    Keyword arguments:
      blog_title: Title of the blog to post to.
      title: Title to give the post.
      content: String to get posted. This may be contents from a file, but NOT
               the path itself!
      is_draft: If this content is a draft post or not. (Default False)

    Returns:
      Entry of post. (Returns same results as self.Post())

    """
    blog_id = self._get_blog_id(blog_title)
    if not blog_id:
      return None
    entry = gdata.GDataEntry()
    entry.title = atom.Title(title_type='xhtml', text=post_title)
    entry.content = atom.Content(content_type='html', text=content)
    if is_draft:
      control = atom.Control()
      control.draft = atom.Draft(text='yes')
      entry.control = control
    return self.Post(entry, '/feeds/' + blog_id + '/posts/default')

  AddPost = add_post

  def _get_blog_id(self, blog_title=None, user_id='default'):
    """Return the blog ID of the blog that matches blog_title.

    Keyword arguments:
      blog_title: Name or title of the blog.
      user_id: Profile ID of blog's owner as seen in the profile view URL.
              Default 'default' for the authenticated user.

    Returns:
      Blog ID (blog_entry.GetSelfLink().href.split('/')[-1]) if a blog is
      found matching the user and blog_title. None otherwise.

    """
    blog_entry = self.GetSingleEntry('/feeds/' + user_id + '/blogs', blog_title)
    if blog_entry:
      return blog_entry.GetSelfLink().href.split('/')[-1]
    else:
      raise BlogNotFound('No blogs returned matching', blog_title)

  def is_token_valid(self, test_uri='/feeds/default/blogs'):
    """Check that the token being used is valid."""
    return googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid

  def get_posts(self, blog_title=None, post_title=None, user_id='default'):
    """Get entries for posts that match a title.

    Keyword arguments:
      blog_title: Name or title of the blog the post is in. (Default None)
      post_title: Title that the post should have. (Default None, for all posts)
      user_id: Profile ID of blog's owner as seen in the profile view URL.
              (Default 'default' for authenticated user)

    Returns:
      List of posts that match parameters, or [] if none do.

    """
    blog_id = self._get_blog_id(blog_title, user_id)
    if blog_id:
      uri = '/feeds/' + blog_id + '/posts/default'
      return self.GetEntries(uri, post_title)
    else:
      return []

  GetPosts = get_posts

  def label_posts(self, post_entries, tags):
    """Add or remove labels on a list of posts.

    Keyword arguments:
      post_entries: List of post entry objects.
      tags: String representation of tags in a comma separated list.
            For how tags are generated from the string,
            see googlecl.base.generate_tag_sets().

    """
    from atom import Category
    scheme = 'http://www.blogger.com/atom/ns#'
    remove_set, add_set, replace_tags = googlecl.base.generate_tag_sets(tags)
    for post in post_entries:
      # No point removing tags if we're replacing all of them.
      if remove_set and not replace_tags:
        # Keep categories if they meet one of two criteria:
        # 1) Are of a different scheme than the one we're looking at, or
        # 2) Are of the same scheme, but the term is in the 'remove' set
        post.category = [c for c in post.category \
                          if c.scheme != scheme or \
                          (c.scheme == scheme and c.term not in remove_set)]

      if replace_tags:
        # Remove categories that match the scheme we are updating.
        post.category = [c for c in post.category if c.scheme != scheme]
      if add_set:
        new_tags = [Category(term=tag, scheme=scheme) for tag in add_set]
        post.category.extend(new_tags)

      self.Put(post, post.GetEditLink().href)

  LabelPosts = label_posts


SERVICE_CLASS = BloggerServiceCL


class BloggerEntryToStringWrapper(googlecl.base.BaseEntryToStringWrapper):
  @property
  def author(self):
    """Author."""
    # Name of author 'x' name is in entry.author[x].name.text
    text_extractor = lambda entry: getattr(getattr(entry, 'name'), 'text')
    return self._join(self.entry.author, text_extractor=text_extractor)


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_post(client, options, args):
  max_size = 500000
  if not args:
    LOG.error('Must provide paths to files and/or string content to post')
    return
  if not options.blog:
    options.blog = googlecl.get_config_option(SECTION_HEADER, 'blog')
  for content_string in args:
    if os.path.exists(content_string):
      with open(content_string, 'r') as content_file:
        content = content_file.read(max_size)
        if content_file.read(1):
          LOG.warning('Only read first ' + str(max_size) + ' bytes of file ' +
                      content_string)
      title = os.path.basename(content_string).split('.')[0]
    else:
      if not options.title:
        title = 'New post'
      content = content_string
    try:
      entry = client.AddPost(options.title or title, content,
                             blog_title=options.blog,
                             is_draft=options.draft)
    except gdata.service.RequestError, err:
      LOG.error('Failed to post: ' + str(err))
    else:
      if entry and options.tags:
        client.LabelPosts([entry], options.tags)


def _run_delete(client, options, args):
  if not options.blog:
    options.blog = googlecl.get_config_option(SECTION_HEADER, 'blog')
  try:
    post_entries = client.GetPosts(blog_title=options.blog,
                                   post_title=options.title)
  except BlogNotFound, err:
    LOG.error(err)
    return
  client.DeleteEntryList(post_entries, entry_type = 'post',
                delete_default=googlecl.CONFIG.getboolean('GENERAL',
                                                      'delete_by_default'))


def _run_list(client, options, args):
  if not options.blog:
    options.blog = googlecl.get_config_option(SECTION_HEADER, 'blog')
  try:
    entries = client.GetPosts(options.blog, options.title,
                              user_id=options.owner or 'default')
  except BlogNotFound, err:
    LOG.error(err)
    return
  for entry in entries:
    print googlecl.base.compile_entry_string(
                                             BloggerEntryToStringWrapper(entry),
                                             options.fields.split(','),
                                             delimiter=options.delimiter)


def _run_tag(client, options, args):
  if not options.blog:
    options.blog = googlecl.get_config_option(SECTION_HEADER, 'blog')
  try:
    entries = client.GetPosts(options.blog, options.title)
  except BlogNotFound, err:
    LOG.error(err)
    return
  client.LabelPosts(entries, options.tags)


TASKS = {'delete': googlecl.base.Task('Delete a post.', callback=_run_delete,
                                      required=['title'],
                                      optional='blog'),
         'post': googlecl.base.Task('Post content.', callback=_run_post,
                                    optional=['blog', 'title', 'tags', 'draft'],
                                    args_desc='PATH_TO_CONTENT or CONTENT'),
         'list': googlecl.base.Task('List posts in a blog',
                                    callback=_run_list,
                                    required=['fields', 'delimiter'],
                                    optional=['blog', 'title', 'owner']),
         'tag': googlecl.base.Task('Label posts', callback=_run_tag,
                                   required=['title', 'tags'],
                                   optional=['blog'])}
