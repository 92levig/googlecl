"""
Service details and instances for the YouTube service.

Created on May 3, 2010

@author: Tom Miller
"""
from gdata.youtube.service import YouTubeService
import gdata.media
import gdata.youtube
import os
import util


tasks = {'post': util.Task('category', ['title', 'summary', 'tags']),
         'list': util.Task(),
         'tag': util.Task(['title', ['category', 'tags']])}


class YouTubeServiceCL(YouTubeService, util.BaseServiceCL):
  
  """Extends gdata.youtube.service.YouTubeService for the command line.
  
  This class adds some features focused on using YouTube via an installed app
  with a command line interface.
  
  """
  
  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as movie titles. (Default False)
      tags_prompt: Indicates if while inserting items, instance should prompt
                   for tags for each item. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting an item. (Default True)
              
    """ 
    YouTubeService.__init__(self)
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)
    
  def CategorizeVideos(self, video_entries, category):
    """Change the categories of a list of videos to a single category.
    
    Keyword arguments:
      video_entries: List of YouTubeVideoEntry objects. 
      category: String representation of category.
    
    """
    scheme = 'http://gdata.youtube.com/schemas/2007/categories.cat'
    for video in video_entries:
      video.media.category = [gdata.media.Category(text=category,
                                                   scheme=scheme,
                                                   label=category)]
      try:
        self.UpdateVideoEntry(video)
      except gdata.service.RequestError as e:
        print ('Category update failed, probably because ' + category +
               ' is not a category.') 

  def GetVideos(self, user='default', title=None):
    """Get entries for videos uploaded by a user.
    
    Keyword arguments:
      user: The user whose videos are being retrieved. (Default 'default')
      title: Title that the videos should have. (Default None, for all videos)
         
    Returns:
      List of videos that match parameters, or [] if none do.
    
    """
    uri = 'http://gdata.youtube.com/feeds/api/users/' + user + '/uploads'
    return self.GetEntries(uri,
                           title,
                           converter=gdata.youtube.YouTubeVideoFeedFromString)
  
  def Login(self, email, password):
    """Try to use programmatic login to log into Picasa.
    
    Keyword arguments:
      email: Email account to log in with. If no domain is specified, gmail.com
             is inferred.
      password: Un-encrypted password to log in with.
    
    Returns:
      Nothing, but sets self.logged_in to True if login was a success.
    
    """
    #Developer keys can only be gained via request, but should be secret...
    #a problem for the open-source program.
    #If you would like the devkey, e-mail me at tom.h.miller (gmail)
    with open(os.path.expanduser('~/google/devkey'), 'r') as devkey_file:
      #Strip the !*&!@# newline character
      devkey = devkey_file.read().strip()
     
    self.developer_key = devkey
    self.client_id = 'GoogleCL'
    
    util.BaseServiceCL.Login(self, email, password)

  def TagVideos(self, video_entries, tags):
    """Add or remove tags on a list of videos.
    
    Keyword arguments:
      video_entries: List of YouTubeVideoEntry objects. 
      tags: String representation of tags in a comma separated list. For how 
            tags are generated from the string, see util.generate_tag_sets().
    
    """
    from gdata.media import Group, Keywords
    remove_set, add_set, replace_tags = util.generate_tag_sets(tags)
    for video in video_entries:
      if not video.media:
        video.media = Group()
      if not video.media.keywords:
        video.media.keywords = Keywords()
  
      # No point removing tags if the video has no keywords,
      # or we're replacing the keywords.
      if video.media.keywords.text and remove_set and not replace_tags:
        current_tags = video.media.keywords.text.replace(', ', ',')
        current_set = set(current_tags.split(','))
        video.media.keywords.text = ','.join(current_set - remove_set)
      
      if replace_tags or not video.media.keywords.text:
        video.media.keywords.text = ','.join(add_set)
      elif add_set: 
        video.media.keywords.text += ',' + ','.join(add_set)
 
      self.UpdateVideoEntry(video)

def run_task(client, task_name, options, args):
  """Execute a particular task.
  
  Keyword arguments:
    client: Client to the service being used.
    task_name: String of the task (e.g. 'post', 'delete').
    options: Contains all attributes required to perform a task
    args: Additional arguments passed in on the command line
    
  """
  if task_name == 'list':
    entries = client.GetVideos(title=options.title)
    for vid in entries:
      print vid.title.text
  elif task_name == 'post':
    if not args:
      print 'Must provide path to video to post!'
      return
    
    filename = os.path.basename(args[0]).split('.')[0]
    my_media_group = gdata.media.Group(
      title=gdata.media.Title(text=options.title or filename),
      description=gdata.media.Description(text=options.summary),
      keywords=gdata.media.Keywords(text=options.tags),
      category=[gdata.media.Category(
                  text=options.category,
                  scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
                  label=options.category)])

    video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)
    if options.devtags:
      taglist = options.devtags.replace(', ', ',')
      taglist = taglist.split(',')
      video_entry.AddDeveloperTags(taglist)
          
    print 'Loading ' + args[0]
    client.InsertVideoEntry(video_entry, args[0])
  elif task_name == 'tag':
    video_entries = client.GetVideos(title=options.title)
    if options.category:
      client.CategorizeVideos(video_entries, options.category)
    if options.tags:
      client.TagVideos(video_entries, options.tags)
    