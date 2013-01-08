This semi-automatic test suite for Linux tries a variety of googlecl
commands on a variety of different python gdata versions, since a lot
of our bugs have historically come from changes in python gdata over time.

- Automatically download and install (locally) all the python gdata 2.*
versions:

# creates test_suite/gdata_tarballs with packed versions of
# all the gdata files.
 $ ./gdata_downloader.sh

# creates test_suite/gdata_installs with unpacked gdata directories.
 $ ./gdata_install_script.sh


- Create a gmail account just for testing, since these tests add and remove
files on various google services.

- Log into the test account in your browser, visit blogger.com and create a
blog.

- Run ./test_blogger.sh <username> <blog name>

To run the tests, first you have to download all the gdata versions. For this you have to run the gdata_downloader.sh script, and then the gdata_install_script.sh script. 

!!! WARNING !!!
All the scripts delete some data. Don't run it on your account with important data. Just create a special Google account for that.

All the scripts start with some dummy command which is called with --force-auth. This way you will have to authorize the app each time you run the script.

The tests are semi-automatical, all commands which delete something requires pressing 'y' key to accept deleting data.

All tests require providing your username as the first script parameter.

Docs Tests

Doc tests are stored in three files:

- test_docs_upload_2.0.10_2.0.12-2.0.17.sh
- test_docs_upload_2.0.1-2.0.4.sh
- test_docs_upload_2.0.5-2.0.9_2.0.11.sh

The version numbers in the file names describe the gdata versions which are tested using this file.

The file for versions just informs that googlecl doesn't work with these versions of gdata: 2.0.5-2.0.9_2.0.11.


Blogger Tests

Blogger tests are in the file test_blogger.sh.
For running the blogger tests you need to provide the real blog name as the second parameter.

Calendar Tests

Calendar tests are in the file test_calendar.sh.

To use the calendar tests, you need to have access to the calendar service.

Contacts Tests

Contacts tests are in the file test_contacts.sh.

Known bug: sometimes the test contact is placed in 'Other Contacts' category, then the google service returns error that it cannot add another contact with the same name. But GoogleCL cannot list this contact and throws an error.

Fix: Delete the contact manually using the web interface.


Picasa Tests

Picasa tests are in the file: test_picasa.sh.

