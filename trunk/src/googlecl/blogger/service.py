"""
Service details and instances for the Blogger service.

Created on May 5, 2010

@author: Tom Miller

"""
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
    util.BaseServiceCL.__init__(self)
    self.service = 'blogger'
    self.server = 'www.blogger.com'
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)
    
  def add_post(self, title, content, is_draft=False):
    """Add a post.
    
    Keyword arguments:
      title: Title to give the post.
      content: String to get posted. This may be contents from a file, but NOT
               the path itself!
      is_draft: If this content is a draft post or not. (Default False)
    
    """
    entry = gdata.GDataEntry()
    entry.title = atom.Title(title_type='xhtml', text=title)
    entry.content = atom.Content(content_type='html', text=content)
    if is_draft:
      control = atom.Control()
      control.draft = atom.Draft(text='yes')
      entry.control = control
    return self.Post(entry, '/feeds/' + self.blog_id + '/posts/default')

  AddPost = add_post

  def is_token_valid(self):
    """Check that the token being used is valid."""
    if util.BaseServiceCL.IsTokenValid(self, '/feeds/default/blogs'):
      feed = self.Get('/feeds/default/blogs')
      self_link = feed.entry[0].GetSelfLink()
      if self_link:
        self.blog_id = self_link.href.split('/')[-1]
      return True
    else:
      return False

  IsTokenValid = is_token_valid

  def delete_post(self, title, delete_default=False):
    """Delete post(s) based on a title."""
    to_delete = self.GetPosts(title)
    if not to_delete:
      print 'No matches found for title ' + title
    else: 
      util.BaseServiceCL.Delete(self, to_delete, 
                                entry_type='post',
                                delete_default=delete_default)

  DeletePost = delete_post
    
  def get_posts(self, title=None):
    """Get entries for posts that match a title.
    
    This will only get posts for the user that has logged in. It's apparently
    very difficult to obtain the profile ID that Blogger uses unless you have
    logged in.
    
    Keyword arguments:
      title: Title that the post should have. (Default None, for all posts)
         
    Returns:
      List of posts that match parameters, or [] if none do.
      
    """
    uri = '/feeds/' + self.blog_id + '/posts/default'
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

  def login(self, email, password):
    """Extends util.BaseServiceCL.Login to also set the blog ID."""
    util.BaseServiceCL.Login(self, email, password)
    
    if self.logged_in:
      feed = self.Get('/feeds/default/blogs')    
      self_link = feed.entry[0].GetSelfLink()
      if self_link:
        self.blog_id = self_link.href.split('/')[-1]

  Login = login


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
    entry = client.AddPost(options.title or title, content)
    client.LabelPosts([entry], options.tags)


def _run_delete(client, options, args):
  client.DeletePost(title=options.title,
                    delete_default=util.config.getboolean('GENERAL',
                                                          'delete_by_default'))


def _run_list(client, options, args):
  entries = client.GetPosts(options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for entry in entries:
    print util.entry_to_string(entry, style_list, delimiter=options.delimiter)


def _run_tag(client, options, args):
  entries = client.GetPosts(options.title)
  client.LabelPosts(entries, options.tags)


tasks = {'delete': util.Task('Delete a post.', callback=_run_delete,
                             required='title'),
         'post': util.Task('Post content.', callback=_run_post,
                           optional='tags',
                           args_desc='PATH_TO_CONTENT or CONTENT'),
         'list': util.Task('List posts in your blog', callback=_run_list,
                           required='delimiter', optional='title'),
         'tag': util.Task('Label posts', callback=_run_tag,
                          required=['tags', 'title'])}