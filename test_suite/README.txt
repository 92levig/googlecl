Welcome to GoogleCL's brand new test suite!

So far, we've got the downloader and installers committed. 
(Tip: download first, then install.) 

We're working to provide test suites that allow you to test against any or all
python-gdata libraries from 2.0.1 through 2.0.17.

To run the tests, first you have to download all the gdata versions. For this you have to run the gdata_downloader.sh script, and then the gdata_install_script.sh script. 

This gdata_downloader.sh script should create directory test_suite/gdata_tarballs with packed versions of all the gdata files.

The gdata_install_script.sh should create test_suite/gdata_installs with unpacked gdata directories.

!!! WARNING !!!
All the scripts delete some data. Don't run it on your account with important data. Just create a special Google account for that.

All the scripts start with some dummy command which is called with --force-auth. This way you will have to authorize the app each time you run the script.

The tests are semi-automatical, all commands which delete something requires pressing 'y' key to accept deleting data.

Docs Tests

Doc tests are stored in three files:

- test_docs_upload_2.0.10_2.0.12-2.0.17.sh
- test_docs_upload_2.0.1-2.0.4.sh
- test_docs_upload_2.0.5-2.0.9_2.0.11.sh

The version numbers in the file names describe the gdata versions which are tested using this file.

The file for versions just informs that googlecl doesn't work with these versions of gdata: 2.0.5-2.0.9_2.0.11.


Blogger Tests

Blogger tests are in the file test_blogger.sh.

Calendar Tests

Calendar tests are in the file test_calendar.sh.

Contacts Tests

Contacts tests are in the file test_contacts.sh.

Picasa Tests

Picasa tests are in the file: test_picasa.sh.
















