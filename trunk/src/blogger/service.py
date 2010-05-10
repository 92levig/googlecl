"""
Service details and instances for the Blogger service.

Created on May 5, 2010

@author: Tom Miller
"""
import atom
import gdata
import os
import re
import util


tasks = {'delete': util.Task('title'),
         'post': util.Task('title', 'tags')}


class BloggerServiceCL(util.BaseServiceCL):
  """Wrapper for the Blogger Service.
  
  This is merely a wrapper, since there doesn't seem to be an actual class for
  Blogger. Code is based off gdata/samples/blogger/BloggerExampleV1.py
  
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
      content: String to get posted.
      is_draft: If this content is a draft post or not. (Default False)
    
    Returns:
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
    """Delete a post based on its title."""
    f = self.GetFeed('/feeds/' + self.blog_id + '/posts/default')
    if self.use_regex:
      to_delete = [post for post in f.entry if re.match(title, post.title.text)]
    else:
      to_delete = [post for post in f.entry if title == post.title.text]
    if not to_delete:
      print 'No matches found for title ' + title
    else: 
      util.BaseServiceCL.Delete(self, to_delete, 
                                entry_type='post',
                                delete_default=delete_default)
    
  def Login(self, email, password):
    """Try to use programmatic login to log into Blogger.
    
    Keyword arguments:
      email: Email account to log in with. If no domain is specified, gmail.com
             is inferred.
      password: Un-encrypted password to log in with.
    
    Returns:
      Sets self.logged_in to True if login was a success. Otherwise, sets it
      to False.
    
    """
    util.BaseServiceCL.Login(self, email, password)
    
    if self.logged_in:
      feed = self.Get('/feeds/default/blogs')
      self_link = feed.entry[0].GetSelfLink()
      if self_link:
        self.blog_id = self_link.href.split('/')[-1]

    
def run_task(client, task_name, options, args):
  if task_name == 'post':
    for content_string in args:
      if os.path.exists(content_string):
        with open(content_string, 'r') as content_file:
          content = content_file.read()
      else:
        content = content_string
      client.AddPost(options.title, content)
  
  elif task_name == 'delete':
    client.DeletePost(title=options.title)