"""
Service details and instances for the Blogger service.

Created on May 5, 2010

@author: Tom Miller
"""
from gdata.service import BadAuthentication, CaptchaRequired
import gdata.service
import re
import os
import atom
import util


tasks = {'delete': util.Task('title'),
         'post': util.Task('title', 'tags')}


class BloggerServiceCL():
  """Wrapper for the Blogger Service.
  
  This is merely a wrapper, since there doesn't seem to be an actual class for
  Blogger. Code is based off gdata/samples/blogger/BloggerExampleV1.py
  
  """
  
  def __init__(self, regex=False):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as post titles. (Default False)
              
    """ 
    self.use_regex = regex
    
  def Login(self, email, password):
    """Try to use programmatic login to log into Blogger.
    
    Keyword arguments:
      email: Email account to log in with. If no domain is specified, gmail.com
             is inferred.
      password: Un-encrypted password to log in with.
    
    Returns:
      Nothing, but sets self.logged_in to True if login was a success.
    
    """
    if not (email and password):
      print ('You must give an email/password combo to log in with, '
             'or a file where they can be found!')
      self.logged_in = False
    
    self.service = gdata.service.GDataService(email, password)
    self.service.source = 'Blogger_Python_Sample-1.0'
    self.service.service = 'blogger'
    self.service.server = 'www.blogger.com'
    
    try:
      self.service.ProgrammaticLogin()
    except BadAuthentication as e:
      print e
      self.logged_in = False
    except CaptchaRequired:
      print 'Too many false logins; Captcha required.'
      self.logged_in = False
    else:
      self.logged_in = True
      feed = self.service.Get('/feeds/default/blogs')
      self_link = feed.entry[0].GetSelfLink()
      if self_link:
        self.blog_id = self_link.href.split('/')[-1]

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
    self.service.Post(entry, '/feeds/' + self.blog_id + '/posts/default')
  
  def DeletePost(self, title):
    """Delete a post based on its title."""
    f = self.service.GetFeed('/feeds/' + self.blog_id + '/posts/default')
    if self.use_regex:
      to_delete = [post for post in f.entry if re.match(title, post.title.text)]
    else:
      to_delete = [post for post in f.entry if title == post.title.text]
    for post in to_delete:
      print 'Deleting "%s"' % post.title.text
      self.service.Delete(post.GetEditLink().href)
    
    
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