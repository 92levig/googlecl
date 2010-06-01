"""
Service details and instances for the Blogger service.

Created on May 5, 2010

@author: Tom Miller

"""
__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import atom
import gdata
import os
import util
from googlecl.blogger import SECTION_HEADER


class BloggerServiceCL(util.BaseServiceCL):
  
  """Command-line-friendly service for the Blogger API. 
  
  Some of this is based off gdata/samples/blogger/BloggerExampleV1.py
  
  """
  
  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as post titles. (Default False)
      tags_prompt: Indicates if while inserting posts, instance should prompt
                   for tags for each post. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting a post. (Default True)
              
    """
    util.BaseServiceCL.__init__(self)
    self.service = 'blogger'
    self.server = 'www.blogger.com'
    self.account_type = 'GOOGLE'
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)
    
  def add_post(self, blog, title, content, is_draft=False):
    """Add a post.
    
    Keyword arguments:
      blog: Title of the blog to post to.
      title: Title to give the post.
      content: String to get posted. This may be contents from a file, but NOT
               the path itself!
      is_draft: If this content is a draft post or not. (Default False)
    
    """
    blog_id = self._get_blog_id(blog)
    entry = gdata.GDataEntry()
    entry.title = atom.Title(title_type='xhtml', text=title)
    entry.content = atom.Content(content_type='html', text=content)
    if is_draft:
      control = atom.Control()
      control.draft = atom.Draft(text='yes')
      entry.control = control
    return self.Post(entry, '/feeds/' + blog_id + '/posts/default')

  AddPost = add_post

  def _get_blog_id(self, blog_title, user='default'):
    """Return the blog ID of the blog that matches blog_title.
    
    Keyword arguments:
      blog_title: Name or title of the blog.
      user: Owner of the blog. Default 'default' for the authenticated user.
    
    """
    blog_entry = self.GetSingleEntry('/feeds/' + user + '/blogs', blog_title)
    return blog_entry.GetSelfLink().href.split('/')[-1]
    
  def is_token_valid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self, '/feeds/default/blogs')

  IsTokenValid = is_token_valid

  def delete_post(self, blog_title, title, delete_default=False):
    """Delete post(s) based on a title."""
    to_delete = self.GetPosts(blog_title, title)
    if not to_delete:
      print 'No matches found for title ' + title
    else: 
      util.BaseServiceCL.Delete(self, to_delete, 
                                entry_type='post',
                                delete_default=delete_default)

  DeletePost = delete_post
    
  def get_posts(self, blog_title, title=None):
    """Get entries for posts that match a title.
    
    This will only get posts for the user that has logged in. It's apparently
    very difficult to obtain the profile ID that Blogger uses unless you have
    logged in.
    
    Keyword arguments:
      blog_title: Name or title of the blog the post is in.
      title: Title that the post should have. (Default None, for all posts)
         
    Returns:
      List of posts that match parameters, or [] if none do.
      
    """
    blog_id = self._get_blog_id(blog_title)
    uri = '/feeds/' + blog_id + '/posts/default'
    return self.GetEntries(uri, title)

  GetPosts = get_posts

  def label_posts(self, post_entries, tags):
    """Add or remove labels on a list of posts.
    
    Keyword arguments:
      post_entries: List of post entry objects. 
      tags: String representation of tags in a comma separated list.
            For how tags are generated from the string, 
            see util.generate_tag_sets().
    
    """
    from atom import Category
    scheme = 'http://www.blogger.com/atom/ns#'
    remove_set, add_set, replace_tags = util.generate_tag_sets(tags)
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


service_class = BloggerServiceCL


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
  for content_string in args:
    if os.path.exists(content_string):
      with open(content_string, 'r') as content_file:
        content = content_file.read()
      title = os.path.basename(content_string).split('.')[0]
    else:
      if not options.title:
        title = 'New post'
      content = content_string
    entry = client.AddPost(options.blog, options.title or title, content)
    if options.tags:
      client.LabelPosts([entry], options.tags)


def _run_delete(client, options, args):
  post_entries = client.GetPosts(options.blog, options.title)
  client.Delete(post_entries, entry_type = 'post',
                delete_default=util.config.getboolean('GENERAL',
                                                      'delete_by_default'))


def _run_list(client, options, args):
  entries = client.GetPosts(options.blog, options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for entry in entries:
    print util.entry_to_string(entry, style_list, delimiter=options.delimiter)


def _run_tag(client, options, args):
  entries = client.GetPosts(options.blog, options.title)
  client.LabelPosts(entries, options.tags)


tasks = {'delete': util.Task('Delete a post.', callback=_run_delete,
                             required=['title', 'blog']),
         'post': util.Task('Post content.', callback=_run_post,
                           required='blog',
                           optional=['title', 'tags'],
                           args_desc='PATH_TO_CONTENT or CONTENT'),
         'list': util.Task('List posts in your blog', callback=_run_list,
                           required=['blog', 'delimiter'], optional='title'),
         'tag': util.Task('Label posts', callback=_run_tag,
                          required=['blog', 'tags', 'title'])}