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


"""Service details and instances for the YouTube service."""


__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import gdata.youtube
import logging
import os
import googlecl
import googlecl.base
import googlecl.service
from googlecl.youtube import SECTION_HEADER
from gdata.youtube.service import YouTubeService


LOG = logging.getLogger(googlecl.youtube.LOGGER_NAME)


class YouTubeServiceCL(YouTubeService, googlecl.service.BaseServiceCL):
  
  """Extends gdata.youtube.service.YouTubeService for the command line.
  
  This class adds some features focused on using YouTube via an installed app
  with a command line interface.
  
  """
  
  def __init__(self):
    """Constructor."""
    YouTubeService.__init__(self)
    googlecl.service.BaseServiceCL.__init__(self, SECTION_HEADER)
  
  def categorize_videos(self, video_entries, category):
    """Change the categories of a list of videos to a single category.
    
    If the update fails with a request error, a message is printed to screen.
    Usually, valid category strings are the first word of the category as seen
    on YouTube (e.g. "Film" for "Film & Animation")
    
    Keyword arguments:
      video_entries: List of YouTubeVideoEntry objects. 
      category: String representation of category.
    
    """
    for video in video_entries:
      video.media.category = build_category(category)
      try:
        self.UpdateVideoEntry(video)
      except gdata.service.RequestError, err:
        if err.args[0]['body'].find('invalid_value') != -1:
          LOG.error('Category update failed, ' + category +
                    ' is not a category.')
        else:
          raise

  CategorizeVideos = categorize_videos

  def get_videos(self, user='default', title=None):
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

  GetVideos = get_videos

  def is_token_valid(self, test_uri='/feeds/api/users/default/uploads'):
    """Check that the token being used is valid."""
    return googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid

  def post_videos(self, paths, category, title=None, desc=None, tags=None,
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
                             description=Description(text=desc or 'A video'),
                             keywords=Keywords(text=tags),
                             category=build_category(category))
  
      video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)
      if devtags:
        taglist = devtags.replace(', ', ',')
        taglist = taglist.split(',')
        video_entry.AddDeveloperTags(taglist)
      LOG.info('Loading ' + path)
      try:
        self.InsertVideoEntry(video_entry, path)
      except gdata.service.RequestError, err:
        if err.args[0]['body'].find('invalid_value') != -1:
          err_str = 'Invalid category name'
        else:
          err_str = str(err)
        LOG.error('Failed to upload video: ' + err_str)

  PostVideos = post_videos

  def tag_videos(self, video_entries, tags):
    """Add or remove tags on a list of videos.
    
    Keyword arguments:
      video_entries: List of YouTubeVideoEntry objects. 
      tags: String representation of tags in a comma separated list. For how 
            tags are generated from the string, see googlecl.base.generate_tag_sets().
    
    """
    from gdata.media import Group, Keywords
    remove_set, add_set, replace_tags = googlecl.base.generate_tag_sets(tags)
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

  TagVideos = tag_videos


SERVICE_CLASS = YouTubeServiceCL


def build_category(category):
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
  entries = client.GetVideos(user=options.owner or 'default',
                             title=options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = googlecl.get_config_option(SECTION_HEADER,
                                            'list_style').split(',')
  for vid in entries:
    print googlecl.base.compile_entry_string(
                                 googlecl.base.BaseEntryToStringWrapper(vid),
                                 style_list,
                                 delimiter=options.delimiter)


def _run_post(client, options, args):
  if not args:
    LOG.error('Must provide path to video to post!')
    return
  client.PostVideos(args, title=options.title, desc=options.summary,
                    tags=options.tags, category=options.category)


def _run_tag(client, options, args):
  video_entries = client.GetVideos(title=options.title)
  if options.category:
    client.CategorizeVideos(video_entries, options.category)
  if options.tags:
    client.TagVideos(video_entries, options.tags)


def _run_delete(client, options, args):
  entries = client.GetVideos(title=options.title)
  client.DeleteEntryList(entries, 'video',
                googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


TASKS = {'post': googlecl.base.Task('Post a video.', callback=_run_post,
                                     required=['category', 'devkey'],
                                     optional=['title', 'summary', 'tags'],
                                     args_desc='PATH_TO_VIDEO'),
         'list': googlecl.base.Task('List videos by user.',
                                     callback=_run_list,
                                     required='delimiter',
                                     optional=['title', 'owner']),
         'tag': googlecl.base.Task('Add tags to a video and/or ' +\
                                    'change its category.',
                                    callback=_run_tag,
                                    required=['devkey', 'title',
                                                ['category', 'tags']]),
         'delete': googlecl.base.Task('Delete videos.', callback=_run_delete,
                                       required='devkey', optional='title')}
