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


"""Service details and instances for the Picasa service."""


from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import logging
import os
import urllib
import googlecl
import googlecl.base
import googlecl.service
from googlecl.picasa import SECTION_HEADER
from gdata.photos.service import PhotosService, GooglePhotosException
import gdata.photos

LOG = logging.getLogger(googlecl.picasa.LOGGER_NAME)
SUPPORTED_VIDEO_TYPES = {'wmv': 'video/x-ms-wmv',
                         'avi': 'video/avi',
                         '3gp': 'video/3gpp',
                         'mov': 'video/quicktime',
                         'qt': 'video/quicktime',
                         'mp4': 'video/mp4',
                         'mpa': 'video/mpeg',
                         'mpe': 'video/mpeg',
                         'mpeg': 'video/mpeg',
                         'mpg': 'video/mpeg',
                         'mpv2': 'video/mpeg',
                         'mpeg4': 'video/mpeg4',}
# XXX gdata.photos.service contains a very strange check against (outdated)
# allowed MIME types. This is a hack to allow videos to be uploaded.
# We're creating a list of the allowed video types stripped of the initial
# 'video/', eliminating duplicates via set(), then converting to tuple()
# since that's what gdata.photos.service uses.
gdata.photos.service.SUPPORTED_UPLOAD_TYPES += \
     tuple(set([type.split('/')[1] for type in SUPPORTED_VIDEO_TYPES.values()]))
DOWNLOAD_VIDEO_TYPES = {'swf': 'application/x-shockwave-flash',
                        'mp4': 'video/mpeg4',}

class PhotosServiceCL(PhotosService, googlecl.service.BaseServiceCL):

  """Extends gdata.photos.service.PhotosService for the command line.

  This class adds some features focused on using Picasa via an installed app
  with a command line interface.

  """

  def __init__(self):
    """Constructor."""
    PhotosService.__init__(self)
    googlecl.service.BaseServiceCL.__init__(self, SECTION_HEADER)

  def build_entry_list(self, user='default', title=None, query=None,
                       force_photos=False):
    """Build a list of entries of either photos or albums.

    If no title is specified, entries will be of photos matching the query.
    If no query is specified, entries will be of albums matching the title.
    If both title and query are specified, entries will be of photos matching
      the query that are also in albums matching the title.

    Keyword arguments:
      user: Username of the owner of the albums / photos (Default 'default').
      title: Title of the album (Default None).
      query: Query for photos, url-encoded (Default None).
      force_photos: If true, returns photo entries, even if album entries would
                    typically be returned. The entries will be for all photos
                    in each album.

    Returns:
      A list of entries, as specified above.

    """
    album_entry = []
    if title or not(title or query):
      album_entry = self.GetAlbum(user=user, title=title)
    if query or force_photos:
      uri = '/data/feed/api/user/' + user
      if query and not album_entry:
        entries = self.GetFeed(uri + '?kind=photo&q=' + query).entry
      else:
        entries = []
        uri += '/albumid/%s?kind=photo'
        if query:
          uri += '&q=' + query
        for album in album_entry:
          photo_feed = self.GetFeed(uri % album.gphoto_id.text)
          entries.extend(photo_feed.entry)
    else:
      entries = album_entry

    return entries

  def download_album(self, base_path, user, video_format='mp4', title=None):
    """Download an album to the local host.

    Keyword arguments:
      base_path: Path on the filesystem to copy albums to. Each album will
                 be stored in base_path/<album title>. If base_path does not
                 exist, it and each non-existent parent directory will be
                 created.
      user: User whose albums are being retrieved. (Default 'default')
      title: Title that the album should have. (Default None, for all albums)

    """
    def _get_download_info(photo_or_video, video_format):
      """Get download link and extension for photo or video.

      video_format must be in DOWNLOAD_VIDEO_TYPES.

      Returns:
        (url, extension)
      """
      wanted_content = None
      for content in photo_or_video.media.content:
        if content.medium == 'image' and not wanted_content:
          wanted_content = content
        elif content.type == DOWNLOAD_VIDEO_TYPES[video_format]:
          wanted_content = content
      if not wanted_content:
        LOG.error('Did not find desired medium!')
        LOG.debug('photo_or_video.media:\n' + photo_or_video.media)
        return None
      elif wanted_content.medium == 'image':
        url = photo_or_video.content.src
        url = url[:url.rfind('/')+1]+'d'+url[url.rfind('/'):]
        mimetype = photo_or_video.content.type
        extension = mimetype.split('/')[1]
      else:
        url = wanted_content.url
        extension = video_format
      return (url, extension)
    # End _get_download_info

    if not user:
      user = 'default'
    entries = self.GetAlbum(user=user, title=title)
    if video_format not in DOWNLOAD_VIDEO_TYPES.keys():
      LOG.error('Unsupported video format: ' + video_format)
      LOG.info('Try one of the following video formats: ' +
               str(DOWNLOAD_VIDEO_TYPES.keys())[1:-1])
      video_format = 'mp4'
      LOG.info('Downloading videos as ' + video_format)

    for album in entries:
      album_path = os.path.join(base_path, album.title.text)
      album_concat = 1
      if os.path.exists(album_path):
        base_album_path = album_path
        while os.path.exists(album_path):
          album_path = base_album_path + '-%i' % album_concat
          album_concat += 1
      os.makedirs(album_path)

      photo_feed = self.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' %
                                (user, album.gphoto_id.text))

      for photo_or_video in photo_feed.entry:
        #TODO: Test on Windows (upload from one OS, download from another)
        photo_or_video_name = photo_or_video.title.text.split(os.extsep)[0]
        url, extension = _get_download_info(photo_or_video, video_format)
        path = os.path.join(album_path,
                            photo_or_video_name + os.extsep + extension)
        # Check for a file extension, add it if it does not exist.
        if os.path.exists(path):
          base_path = path
          photo_concat = 1
          while os.path.exists(path):
            path = base_path + '-%i' % photo_concat
            photo_concat += 1
        LOG.info('Downloading %s to %s' % (photo_or_video.title.text, path))
        urllib.urlretrieve(url, path)

  DownloadAlbum = download_album

  def get_album(self, user='default', title=None):
    """Get albums from a user feed.

    Keyword arguments:
      user: The user whose albums are being retrieved. (Default 'default')
      title: Title that the album should have. (Default None, for all albums)

    Returns:
      List of albums that match parameters, or [] if none do.

    """
    uri = '/data/feed/api/user/' + user + '?kind=album'
    return self.GetEntries(uri, title)

  GetAlbum = get_album

  def get_single_album(self, user='default', title=None):
    """Get a single album."""
    uri = '/data/feed/api/user/' + user + '?kind=album'
    return self.GetSingleEntry(uri, title=title)

  GetSingleAlbum = get_single_album

  def insert_media_list(self, album, photo_list, tags='', user='default'):
    """Insert photos into an album.

    Keyword arguments:
      album: The album entry of the album getting the media.
      photo_list: A list of paths, each path a picture or video on
                  the local host.
      tags: Text of the tags to be added to each item, e.g. 'Islands, Vacation'
            (Default '').

    """
    album_url = ('/data/feed/api/user/%s/albumid/%s' %
                 (user, album.gphoto_id.text))
    keywords = tags
    failures = []
    for path in photo_list:
      if not tags and self.prompt_for_tags:
        keywords = raw_input('Enter tags for photo %s: ' % path)
      LOG.info('Loading file ' + path + ' to album ' + album.title.text)
      ext = googlecl.get_extension_from_path(path)
      if not ext:
        LOG.debug('No extension match on path ' + path)
        content_type = 'image/jpeg'
      else:
        try:
          content_type = SUPPORTED_VIDEO_TYPES[ext]
        except KeyError:
          content_type = 'image/' + ext
      try:
        self.InsertPhotoSimple(album_url,
                               title=os.path.split(path)[1],
                               summary='',
                               filename_or_handle=path,
                               keywords=keywords,
                               content_type=content_type)
      except GooglePhotosException, err:
        LOG.error('Failed to upload %s. (%s: %s)', path,
                                                   err.args[0],
                                                   err.args[1])
        failures.append(file)
    return failures

  InsertMediaList = insert_media_list

  def is_token_valid(self, test_uri='/data/feed/api/user/default'):
    """Check that the token being used is valid."""
    return googlecl.base.BaseCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid

  def tag_photos(self, photo_entries, tags):
    """Add or remove tags on a list of photos.

    Keyword arguments:
      photo_entries: List of photo entry objects.
      tags: String representation of tags in a comma separated list.
            For how tags are generated from the string,
            see googlecl.base.generate_tag_sets().

    """
    from gdata.media import Group, Keywords
    remove_set, add_set, replace_tags = googlecl.base.generate_tag_sets(tags)
    for photo in photo_entries:
      if not photo.media:
        photo.media = Group()
      if not photo.media.keywords:
        photo.media.keywords = Keywords()

      # No point removing tags if the photo has no keywords,
      # or we're replacing the keywords.
      if photo.media.keywords.text and remove_set and not replace_tags:
        current_tags = photo.media.keywords.text.replace(', ', ',')
        current_set = set(current_tags.split(','))
        photo.media.keywords.text = ','.join(current_set - remove_set)

      if replace_tags or not photo.media.keywords.text:
        photo.media.keywords.text = ','.join(add_set)
      elif add_set:
        photo.media.keywords.text += ',' + ','.join(add_set)

      self.UpdatePhotoMetadata(photo)

  TagPhotos = tag_photos


SERVICE_CLASS = PhotosServiceCL


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_create(client, options, args):
  if options.date:
    import time
    try:
      timestamp = time.mktime(time.strptime(options.date,
                                            googlecl.base.DATE_FORMAT))
    except ValueError, err:
      LOG.error(err)
      LOG.info('Ignoring date option, using today')
      options.date = ''
    else:
      # Timestamp needs to be in milliseconds after the epoch
      options.date = '%i' % (timestamp * 1000)

  album = client.InsertAlbum(title=options.title, summary=options.summary,
                             access=googlecl.CONFIG.get(SECTION_HEADER,
                                                        'access'),
                             timestamp=options.date)
  if args:
    client.InsertMediaList(album, photo_list=args, tags=options.tags)


def _run_delete(client, options, args):
  if options.encoded_query:
    entry_type = 'photo'
    search_string = options.query
  else:
    entry_type = 'album'
    search_string = options.title
  entries = client.build_entry_list(title=options.title,
                                    query=options.encoded_query)
  if not entries:
    LOG.info('No %ss matching %s' % (entry_type, search_string))
  else:
    client.DeleteEntryList(entries, entry_type,
                delete_default=googlecl.CONFIG.getboolean('GENERAL',
                                                          'delete_by_default'))


def _run_list(client, options, args):
  entries = client.build_entry_list(user=options.owner or options.user,
                                    title=options.title,
                                    query=options.encoded_query,
                                    force_photos=True)
  if args:
    field_list = args[0].split(',')
  else:
    field_list = googlecl.get_config_option(SECTION_HEADER,
                                            'list_fields').split(',')
  for entry in entries:
    print googlecl.base.compile_entry_string(
                               googlecl.base.BaseEntryToStringWrapper(entry),
                               field_list,
                               delimiter=options.delimiter)


def _run_list_albums(client, options, args):
  entries = client.build_entry_list(user=options.owner or options.user,
                                    title=options.title,
                                    force_photos=False)
  if args:
    field_list = args[0].split(',')
  else:
    field_list = googlecl.get_config_option(SECTION_HEADER,
                                            'list_fields').split(',')
  for entry in entries:
    print googlecl.base.compile_entry_string(
                               googlecl.base.BaseEntryToStringWrapper(entry),
                               field_list,
                               delimiter=options.delimiter)


def _run_post(client, options, args):
  if not args:
    LOG.error('Must provide photos to post!')
    return
  album = client.GetSingleAlbum(user=options.owner or options.user,
                                title=options.title)
  if album:
    client.InsertMediaList(album, args, tags=options.tags,
                           user=options.owner or options.user)
  else:
    LOG.error('No albums found that match ' + options.title)


def _run_get(client, options, args):
  if not args:
    LOG.error('Must provide destination of album(s)!')
    return
  base_path = args[0]
  client.DownloadAlbum(base_path,
                       user=options.owner or options.user,
                       video_format=options.format or 'mp4',
                       title=options.title)


def _run_tag(client, options, args):
  entries = client.build_entry_list(user=options.owner or options.user,
                                    query=options.query,
                                    title=options.title,
                                    force_photos=True)
  if entries:
    client.TagPhotos(entries, options.tags)
  else:
    LOG.error('No matches for the title and/or query you gave.')


TASKS = {'create': googlecl.base.Task('Create an album',
                                         callback=_run_create,
                                         required='title',
                                         optional=['date', 'summary', 'tags'],
                                         args_desc='PATH_TO_PHOTOS'),
         'post': googlecl.base.Task('Post photos to an album',
                                       callback=_run_post,
                                       required='title',
                                       optional=['tags', 'owner'],
                                       args_desc='PATH_TO_PHOTOS'),
         'delete': googlecl.base.Task('Delete photos or albums',
                                         callback=_run_delete,
                                         required=[['title', 'query']]),
         'list': googlecl.base.Task('List photos', callback=_run_list,
                                       required=['delimiter'],
                                       optional=['title', 'query', 'owner']),
         'list-albums': googlecl.base.Task('List albums',
                                              callback=_run_list_albums,
                                              required=['delimiter'],
                                              optional=['title', 'owner']),
         'get': googlecl.base.Task('Download albums', callback=_run_get,
                                      optional=['title', 'owner', 'format'],
                                      args_desc='LOCATION'),
         'tag': googlecl.base.Task('Tag photos', callback=_run_tag,
                                      required=['tags', ['title', 'query']],
                                      optional='owner')}
