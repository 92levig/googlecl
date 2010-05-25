"""
Created on May 3, 2010

Unit tests for the Picasa portion of the GoogleCL project.
@author: Tom Miller
"""
#TODO: Make tests more rigorous.
import os
import picasa.service
import unittest
import util
import shutil


_test_dir = 'phototest_tmp'
_download_path = os.path.join(_test_dir, 'albums')
_test_entry_names = ['test_album1', 'test_album2']


class PhotoBaseTest(unittest.TestCase):
  """Base test case for Picasa. Defines setup and teardown."""
  def setUp(self):
    """Create the PhotosServiceCL client and create the test directory."""
    util.load_preferences()
    regex = True
    tags_prompt = False
    delete_prompt = False
    self.client = picasa.service.PhotosServiceCL(regex,
                                                 tags_prompt,
                                                 delete_prompt)
    if not os.path.exists(_test_dir):
      os.makedirs(_test_dir)
    
  def tearDown(self):
    """Remove any downloads."""
    if os.path.exists(_download_path):
      shutil.rmtree(_download_path)


class PhotoTest(PhotoBaseTest):
  """Test the PhotosServiceCL functions that do not require logging in."""
  
  def test_GetAlbum(self):
    """Retrieve test albums."""
    entries = self.client.GetAlbum(user='tom.h.miller', title='test_album[0-9]')
    for album in entries:
      self.assertTrue(album.title.text in _test_entry_names)
  
  def test_DownloadAlbum(self):
    """Download the test albums (e.g. test_album1)."""
    self.client.DownloadAlbum(_download_path,
                              user='tom.h.miller',
                              title='test_album[0-9]')
    for name in _test_entry_names:
      self.assertTrue(os.path.exists(os.path.join(_download_path, name)))

  def suite(self=None):
    """Return a test suite of all the unauthenticated tests."""
    return unittest.TestLoader().loadTestsFromTestCase(PhotoTest)    


class PhotoLoginTest(PhotoBaseTest):
  """Test the PhotosServiceCL functions that require logging in."""
  
  def setUp(self):
    """Uses PhotoBaseTest's setup, then logs in with credentials file."""
    PhotoBaseTest.setUp(self)
    util.try_login(self.client)
    self.assertTrue(self.client.logged_in)
      
  def test_InsertPhotoList(self):
    """Inserts a photo into test_album_post."""
    albums = self.client.GetAlbum(title='test_album_post')
    photos_to_post = [os.path.join(_test_dir, 'test_photo.jpg')]
    failures = self.client.InsertPhotoList(albums[0],
                                           photos_to_post,
                                           tags='test tag 1, testtag2')
    self.assertFalse(failures)

  def suite(self=None):
    """Return a test suite of all the log in tests."""
    return unittest.TestLoader().loadTestsFromTestCase(PhotoLoginTest)


if __name__ == "__main__":
  unittest.TextTestRunner(verbosity=2).run(PhotoTest.suite())
  unittest.TextTestRunner(verbosity=2).run(PhotoLoginTest.suite())
  unittest.main()