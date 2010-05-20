"""
Service details and instances for the YouTube service.

Created on May 3, 2010

@author: Tom Miller
"""
from gdata.youtube.service import YouTubeService
import gdata.youtube
import os
import util


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

  def build_category(self, category):
    """Build a single-item list of a YouTube category.
    
    This refers to the Category of a video entry, such as "Film" or "Comedy",
    not the atom/gdata element. This does not check if the category provided
    is valid.
    
    Keyword arguments:
      category: String representing the category.
    
    Returns:
      A single-item list of a YouTube category (type gdata.media.Category).
      
    """
    from gdata.media import Category
    return [Category(
                  text=category,
                  scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
                  label=category)]

  def CategorizeVideos(self, video_entries, category):
    """Change the categories of a list of videos to a single category.
    
    If the update fails with a request error, a message is printed to screen.
    Usually, valid category strings are the first word of the category as seen
    on YouTube (e.g. "Film" for "Film & Animation")
    
    Keyword arguments:
      video_entries: List of YouTubeVideoEntry objects. 
      category: String representation of category.
    
    """
    for video in video_entries:
      video.media.category = self.build_category(category)
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

  def IsTokenValid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self, '/feeds/api/users/default')

  def Login(self, email, password):
    """Try to use programmatic login to log into YouTube.
    
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
    util.BaseServiceCL.Login(self, email, password)

  def PostVideos(self, paths, category, title=None, desc=None, tags=None,
                 devtags=None):
    """Post video(s) to YouTube.
    
    Keyword arguments:
      paths: List of paths to videos.
      category: YouTube category for the video.
      title: Title of the video. (Default is the filename of the video).
      desc: Video summary (Default None).
      tags: Tags of the video as a string, separated by commas (Default None).
      devtags: Developer tags for the video (Default None).
      
    """
    from gdata.media import Group, Title, Description, Keywords
    for path in paths:
      filename = os.path.basename(path).split('.')[0]
      my_media_group = Group(title=Title(text=title or filename),
                             description=Description(text=desc),
                             keywords=Keywords(text=tags),
                             category=self.build_category(category))
  
      video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)
      if devtags:
        taglist = devtags.replace(', ', ',')
        taglist = taglist.split(',')
        video_entry.AddDeveloperTags(taglist)
            
      print 'Loading ' + path
      self.InsertVideoEntry(video_entry, path)

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


service_class = YouTubeServiceCL


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
  entries = client.GetVideos(title=options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.config.get('GENERAL', 'default_list_style').split(',')
  for vid in entries:
    print util.entry_to_string(vid, style_list)


def _run_post(client, options, args):
  if not args:
    print 'Must provide path to video to post!'
    return
  client.PostVideos(args, title=options.title, desc=options.summary,
                   keywords=options.tags, category=options.category)


def _run_tag(client, options, args):
  video_entries = client.GetVideos(title=options.title)
  if options.category:
    client.CategorizeVideos(video_entries, options.category)
  if options.tags:
    client.TagVideos(video_entries, options.tags)


tasks = {'post': util.Task('Post a video', callback=_run_post,
                           required='category',
                           optional=['title', 'summary', 'tags'],
                           args_desc='PATH_TO_VIDEO'),
         'list': util.Task('List videos by user', callback=_run_list,
                           optional='user'),
         'tag': util.Task('Add tags to a video', callback=_run_tag,
                          required=['title', ['category', 'tags']])}  