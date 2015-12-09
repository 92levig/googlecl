**8 June 2015: GoogleCL is currently broken due to the OAuth1 turndown, and likely to remain so. Thanks for your support over the years, and apologies for the lack of prior notice.**

#summary Frequently asked questions and troubleshooting



# FAQ #

## Will you support XXX? ##
We're building on top of [gdata-python-client](http://code.google.com/p/gdata-python-client/), so if you don't see it supported there, we won't be supporting it in the foreseeable future.

If you want a service that isn't supported by gdata-python-client, check their [issue tracker](http://code.google.com/p/gdata-python-client/issues/list) for a request to support said service. If the issue exists, star it. If not, submit a new issue asking for them to support it.

To request a feature for a service that we do support, file an issue on our [issue tracker](http://code.google.com/p/googlecl/issues/list), following the same steps as above.

## How do I use the most recent version? / How do I run the code from the repository or trunk? ##
The svn repository always has the most recent patches already applied, though it may also have new and exciting bugs. If you're not familiar with subversion, you may want to read up on it [here](http://svnbook.red-bean.com/nightly/en/svn.intro.quickstart.html).
  * Install svn if you don't have it. For Windows, try [TortoiseSVN](http://tortoisesvn.tigris.org/)
  * Checkout the trunk with `svn checkout http://googlecl.googlecode.com/svn/trunk/ googlecl`
  * Navigate to googlecl/src
  * Run the file named "google.py" either by passing it as an argument to your python executable (`$ python google.py`) or making it executable.

Provided Python can find the gdata libraries, that's it. Isn't Python great?

## How do I install a newer version of gdata? ##
**Note:** After following the instructions below, you should probably re-run any recent commands with `--force-auth` to ensure you're not using an outdated data model for the access tokens. You can also just remove the stored tokens, typically stored in ~/.local/share/googlecl/

### All systems ###
Grab the latest version from [the gdata homepage](http://code.google.com/p/gdata-python-client/) and follow the install instructions in the download. Try to remove the previous version that you have installed (if any). If you've upgraded and an earlier version seems to be lurking, see the [troubleshooting](http://code.google.com/p/googlecl/wiki/FAQ#GoogleCL_behaves_as_if_an_earlier_version_of_gdata_is_installed) section.

### Debian/Ubuntu ###
Debian/Ubuntu users can use their package manager to remove the old version installed:

`sudo dpkg -r python-gdata`

You may also be able to install the 2.0.8 deb file from the upcoming Ubuntu release:

`sudo dpkg -i https://launchpad.net/ubuntu/+archive/primary/+files/python-gdata_2.0.8-1.1_all.deb`

## How do I apply patches? ##
If you're as impatient as I am (not recommended), and on some flavor of Linux, try this:

```
$ cd /path/to/python/libraries
$ sudo patch -p0 -i /path/to/patch_file
```

I **really** recommend reading a proper tutorial on the `patch` command first, though. How about [this one](http://www.linuxtutorialblog.com/post/introduction-using-diff-and-patch-tutorial)?

The path used in the `cd` command depends on your operating system and how GoogleCL was installed. For me (Ubuntu 9.10, using setup.py) it is `/usr/local/lib/python2.6/dist-packages`

For Windows, you need to download a patch tool. You could also check out the svn repository by downloading an svn tool (try TortoiseSVN) and following the instructions [here](http://code.google.com/p/googlecl/source/checkout). The repository will have all patches from issues marked "fixed", but has the potential to be more unstable than the releases in the Downloads section.

## How do I uninstall GoogleCL? ##
Why would I tell you that? :P

Installing from source with `python setup.py install` means you probably need to remove files by hand. [This](http://stackoverflow.com/questions/1550226/python-setup-py-uninstall) provides some helpful instructions on how to do that.

If you used the .deb, try `sudo dpkg -r /path/to/deb_file`. Replacing the -r with -P will also remove configuration files.

## Why isn't GoogleCL showing up in my "Authorized websites" list? ##
This process apparently takes a while for installed applications. If nothing has shown up after 3 hours, please file an issue.

## How do I make calendar events with numerical titles? ##
Add single quotes and double quotes around the name. For example:
`$ google calendar add '"12345"'`

## How do I convert new-version documents to work with GoogleCL? ##
The client libraries still have a few issues with the new document version that Google just rolled out. Here's how to convert those pesky docs using the version of GoogleCL in the repository (or, if I haven't updated this yet, whatever version is after 0.9.8)
  * Disable new-version documents. To do this, go to Settings->Documents settings->Editing, then uncheck the box that says "New version of Google documents." Settings should be a link in the upper right corner of the window.
  * IF you haven't already tried to update the document, download the new-style document. (`google docs get -n "name of document"`)
  * Upload the document. (`google docs upload path/to/document -n "name of document"`)
  * If you're cautious, verify the document looks good using the web browser.
  * Delete the old document (optional, but recommended).

## Why can't I upload XXX to Docs? ##
For all users, the version of gdata that you are using limits the types of documents you can upload. The list of extension: MIME content types are given below.

gdata-1.2.4:
  * CSV: text/csv
  * TSV: text/tab-separated-values
  * TAB: text/tab-separated-values
  * DOC: application/msword
  * ODS: application/x-vnd.oasis.opendocument.spreadsheet
  * ODT: application/vnd.oasis.opendocument.text
  * RTF: application/rtf
  * SXW: application/vnd.sun.xml.writer
  * TXT: text/plain
  * XLS: application/vnd.ms-excel
  * PPT: application/vnd.ms-powerpoint
  * PPS: application/vnd.ms-powerpoint
  * HTM: text/html
  * HTML: text/html

As of gdata-2.0.10, the following were added:
  * DOCX: (application/vnd.openxmlformats-officedocument, wordprocessingml.document)
  * XLSX: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  * PDF: application/pdf
  * PNG: image/png
  * ZIP: application/zip
  * SWF: application/x-shockwave-flash

# Troubleshooting #

## ImportError: no module named gdata.xxx.xxx ##
You either (1) do not have gdata installed, or (2) the gdata location isn't known by Python.

To solve (1), follow the instructions given above on installing newer versions of gdata.

To solve (2), if you know the gdata library is installed, you can set the PYTHONPATH environment variable to include the library's location.

## Known issues with gdata 1.2.4 ##
The latest version of the gdata python client that comes with Ubuntu < 10.10 (Maverick Meerkat) is 1.2.4, which causes the following known problems:
  * Cannot upload documents with non-ascii characters ([Issue 195](https://code.google.com/p/googlecl/issues/detail?id=195), comment 23)
  * Apps Premium users cannot use the --no-convert option ([Issue 185](https://code.google.com/p/googlecl/issues/detail?id=185), comment 27)
  * Docs 'get' and 'edit' tasks will not work.

Other flavors of GNU/Linux may have outdated versions of python-gdata in their package managers, and experience similar problems.

## no attribute 'SetOAuthInputParameters' ##
You need a later version of the [gdata python library](http://code.google.com/p/gdata-python-client/). The earliest version we tested with was 1.2.4.

## "ValueError: Invalid resource id" when using Docs ##
Upgrading to gdata 2.0.12 seems to fix this. It has been seen in versions as late as 2.0.2.

## Timestamp too far from current time ##
It's very likely that your system clock is out of sync with reality. Your best option is probably to sync with a time server. I recommend Googling around for the way to do this for your system, but the following tips MAY help.

This issue was originally tracked by [Issue 55](https://code.google.com/p/googlecl/issues/detail?id=55).

### POSIX systems and their ilk ###
(almost everything but Windows)
You can sync from the command line with `sudo ntpdate -s ntp.time.ca` with the following caveats:
  * Gentoo and maybe others use htpdate, not ntpdate, and the options are probably different.
  * ntp.time.ca is a time server in Canada. [See here](http://tf.nist.gov/tf-cgi/servers.cgi) for a list of servers.
  * This will not touch your timezone setting, so the date may still look wrong.

If your system clock is always off when you boot up, your hardware clock is probably off and your OS isn't copying the (now correct) system clock to it. You can use `sudo hwclock --systohc` to set the hardware clock off the system clock, but READ THE MANUAL. Use `--utc` as appropriate.

### Windows ###
[These instructions](http://www.microsoft.com/windowsxp/using/setup/maintain/setclock.mspx) are written for XP, but the steps should be very similar for all versions of Windows.

## Won't work from behind a proxy ##
The short answer seems to be "Make sure http:// and https:// are included in your proxy settings." Using just myproxy:portnumber may work for other programs, but gdata requires the protocol as well.

You may want to check out [these steps](http://code.google.com/p/gdatacopier/wiki/ProxySupport), which claim to be generic to the gdata-api.

If you're seeing a stack trace ending in
```
File "/usr/lib/python2.6/site-packages/atom/http.py", line 240, in _prepare_connection
    p_sock.connect((proxy_url.host, int(proxy_url.port)))
  File "<string>", line 1, in connect
TypeError: coercing to Unicode: need string or buffer, NoneType found
```

upgrading to gdata-python-client 2.0.10 works for most or all users.

[Issue 44](https://code.google.com/p/googlecl/issues/detail?id=44) and [Issue 220](https://code.google.com/p/googlecl/issues/detail?id=220) tracked these issues

### Invalid literal for int() with base 10 ###
If you have your proxy settings defined in the style `user:password@host:port` you are probably seeing a stack trace ending in:

```
File "/usr/local/lib/python2.6/dist-packages/atom/http.py", line 278, in _prepare_connection
    return httplib.HTTPConnection(proxy_url.host, int(proxy_url.port))
ValueError: invalid literal for int() with base 10: 'password@host'
```

You need to remove the username and password information from the `http_proxy` and `https_proxy` environment variables and put them into `proxy_username` and `proxy_password`.

There is a patch to gdata-python-client to allow proxy authentication info in `http_proxy` and `https_proxy` [here](http://codereview.appspot.com/2915041), the gdata issue is [here](http://code.google.com/p/gdata-python-client/issues/detail?id=414).

[Issue 117](https://code.google.com/p/googlecl/issues/detail?id=117) originally tracked this issue.

## GoogleCL behaves as if an earlier version of gdata is installed ##
If you have installed version 2.0.x but are still getting bugs/issues tied to earlier versions of gdata, the older version may still be lurking on your machine. Ubuntu/Debian users can use
```
$ dpkg --list | grep gdata
... snipped ...
ii  python-gdata                               1.2.4-0ubuntu2                             Google Data Python client library
```

If you see that, then an early version (1.2.4, in fact) is still installed. You can get rid of it with `dpkg -r python-gdata`

Also check the directories in your PYTHONPATH:
```
$ echo $PYTHONPATH
:/usr/local/lib/python2.6/site-packages:/usr/local/lib/python2.6/dist-packages
$ ls /usr/local/lib/python2.6/site-packages gdata*
```

If PYTHONPATH is not set for you, or its directories do not contain the new gdata, set it to point at the directory where your newer version of gdata resides (`export PYTHONPATH=$PYTHONPATH:/path/to/directory`)

After successfully removing the old version of gdata, you'll probably have to get new authorization tokens. You can force re-authentication by adding `--force-auth` to a command, which will discard the old token upon successfully authenticating.

## Calendar adds events at the wrong time ##
This is probably because you have not set up a time zone for your calendar. At [the Calendar home page](https://www.google.com/calendar), in the panel of calendars to the left, click on the arrow to the right of the calendar name. Go to Calendar Settings, and change the setting under Calendar Time Zone.