Please note that we haven't tried all of these methods, and there may be a package/port in your distribution's package manager that we're not aware of. If something seems amiss, ask around on the [mailing list](http://groups.google.com/group/googlecl-discuss), or file an issue in the [tracker](http://code.google.com/p/googlecl/issues/list).

# Dependencies #
  * [Python](http://python.org/download/releases/) 2.5 - 2.9.  (There are known issues with python 3.2 and googlecl)
  * [gdata](http://code.google.com/p/gdata-python-client/downloads/list)

While we've made efforts to be backwards compatible all the way back to  gdata 1.2.4, there are a few things that will not work.  If you're having trouble, see the [troubleshooting guide](http://code.google.com/p/googlecl/wiki/FAQ#Troubleshooting)

## Known issues with certain gdata-python-client versions ##

GoogleCL relies on gdata-python-client, or python-gdata as it's known in Ubuntu.

We've tried to be compatible with as many versions of that library as possible, but there are some versions that just don't work with some GoogleCL services.

gdata-python-client versions 2.0.14 and later work best, so if you have a choice, use one of those versions.

Google Docs commands have various incompatibilities with almost all versions before 2.0.14, so avoid 2.0.13 or older.

Google Contacts has issues with versions earlier than 2.0.7.  Versions 2.0.1 and 2.0.2 do seem to work, but use a different auth token, so we recommend avoiding them.

# All systems #
## From source ##
Fortunately, installing GoogleCL is super easy, because it's all Python. Download the latest .tar.gz, unpack it, and run setup.py to install it system wide or just run it from the src/ directory. -- Note: as of February 2, 2012, docs are broken with the .tar.gz versions of GoogleCL. If you need docs support, [checkout GoogleCL from svn](http://code.google.com/p/googlecl/source/checkout).

  * `tar xvf googlecl-x.x.x.tar.gz`<br>
<ul><li><code>cd googlecl-x.x.x</code></li></ul>

then<br>
<br>
<ul><li><code>sudo python setup.py install --record=files.txt</code> (creates a list of files installed and saves it in files.txt)</li></ul>

OR don't install it and just use it this way:<br>
<br>
<ul><li><code>cd src/</code>
</li><li><code>./google</code></li></ul>

<h2>PyPi (The Cheeseshop)</h2>
There are a few ways to access the cheeseshop:<br>
<ul><li><a href='http://pypi.python.org/pypi/setuptools'>easy_install</a>: <code>easy_install googlecl</code>
</li><li><a href='http://pypi.python.org/pypi/pip'>pip</a>: <code>pip install googlecl</code>
</li><li><a href='http://docs.activestate.com/activepython/2.6/pypm.html'>PyPM</a>: <code>pypm install googlecl</code></li></ul>

<h1>GNU/Linux</h1>
<h2>Debian and company (e.g. Ubuntu)</h2>
Installation should be very simple. Grab the .deb file from the Downloads section, cd to your downloads directory, and run<br>
<br>
<ul><li><code>sudo dpkg -i googlecl*.deb</code></li></ul>

<b>Note:</b> We've heard of problems from Hardy users and Debian Lenny (unless you've enabled backports).<br>
<br>
<h3>python-gdata version</h3>
Note that most versions of Ubuntu only come standard with gdata 1.2.4, so you may see a message like:<br>
<br>
<ul><li>"Editing documents is not supported for gdata-python-client < 2.0"</li></ul>

If you need to use tasks unsupported by gdata-1.2, you'll need to manually install a newer version of the gdata and gdata python libraries.<br>
<br>
<br>
<h1>Mac</h1>

<a href='http://www.reddit.com/r/programming/comments/cgi57/introducing_the_google_command_line_tool/c0seufq'>Someone</a> on reddit says that it's available via macports:<br>
<br>
<ul><li><code>sudo port install googlecl</code></li></ul>

If it's not there, run 'sudo port selfupdate', then try again.<br>
<br>
bodo.tasche reports that Brew has removed the googlecl package because it is part of pip. To install pip and then googlecl, use<br>
<br>
<ul><li><code>brew install pip</code>
</li><li><code>pip install googlecl</code></li></ul>

<h1>Windows</h1>
<h2>0.9.8 and up</h2>
The zip file available in the Downloads section contains an executable called "google" that you can run from inside that folder. Running it will bring up the interactive shell prompt (<code>&gt; </code>) where you can enter commands such as <code>docs list</code> or <code>blogger post "Hello World!"</code>

If it crashes, does nothing, or says "MCVCR71.dll not found" you may need a DLL from Microsoft installed via <a href='http://www.microsoft.com/downloads/details.aspx?familyid=32bc1bee-a3f9-4c13-9c99-220b62a191ee&displaylang=en'>this tool</a>.<br>
<br>
<h2>0.9.7 and earlier</h2>
Isaac Truett wrote up a HOWTO on his blog:<br>
<a href='http://publicint.blogspot.com/2010/06/setup-googlecl-on-winxp.html'>http://publicint.blogspot.com/2010/06/setup-googlecl-on-winxp.html</a>

<h1>FreeBSD</h1>
There is a FreeBSD port available under net/googlecl<br>
<br>
<h1>Other</h1>
Did we miss something? Let us know via the <a href='http://groups.google.com/group/googlecl-discuss'>mailing list</a>. (The wiki comments are rarely, if ever, checked! But we appreciate the feedback when we see it!)