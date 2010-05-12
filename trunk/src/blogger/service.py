"""
Service details and instances for the Blogger service.

Created on May 5, 2010

@author: Tom Miller
"""
import atom
import gdata
import os
import util


tasks = {'delete': util.Task('title'),
         'post': util.Task(optional='tags'),
         'list': util.Task(),
         'tag': util.Task(['tags', 'title'])}


class BloggerServiceCL(util.BaseServiceCL):
  
  """Command-line-friendly service for the Blogger API. 
  
  Some of this is based off gdata/samples/blogger/BloggerExampleV1.py
  
  """
  
  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    util.BaseServiceCL.__init__(self)
    self.service = 'blogger'
    self.server = 'www.blogger.com'
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)
    
  def AddPost(self, title, content, is_draft=False):
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
    self.Post(entry, '/feeds/' + self.blog_id + '/posts/default')
  
  def DeletePost(self, title, delete_default=False):
    """Delete post(s) based on a title."""
    to_delete = self.GetPosts(title)
    if not to_delete:
      print 'No matches found for title ' + title
    else: 
      util.BaseServiceCL.Delete(self, to_delete, 
                                entry_type='post',
                                delete_default=delete_default)
  
  def GetPosts(self, title=None):
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
  
  def LabelPosts(self, post_entries, tags):
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

  def Login(self, email, password):
    """Extends util.BaseServiceCL.Login to also set the blog ID."""
    util.BaseServiceCL.Login(self, email, password)
    
    if self.logged_in:
      feed = self.Get('/feeds/default/blogs')    
      self_link = feed.entry[0].GetSelfLink()
      if self_link:
        self.blog_id = self_link.href.split('/')[-1]

    
def run_task(client, task_name, options, args):
  """Execute a particular task.
  
  Keyword arguments:
    client: Client to the service being used.
    task_name: String of the task (e.g. 'post', 'delete').
    options: Contains all attributes required to perform a task
    args: Additional arguments passed in on the command line
    
  """
  if task_name == 'post':
    for content_string in args:
      if os.path.exists(content_string):
        with open(content_string, 'r') as content_file:
          content = content_file.read()
        title = os.path.basename(content_string).split('.')[0]
      else:
        if not options.title:
          title = 'New post'
        content = content_string
      client.AddPost(options.title or title, content)
  elif task_name == 'delete':
    client.DeletePost(title=options.title)
  elif task_name == 'list':
    entries = client.GetPosts(options.title)
    for entry in entries:
      print entry.title.text
  elif task_name == 'tag':
    entries = client.GetPosts(options.title)
    client.LabelPosts(entries, options.tags)
  else:
    print 'Sorry, task "%s" is currently unsupported for Blogger.' % task_name