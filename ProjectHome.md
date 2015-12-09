**8 June 2015: GoogleCL is currently broken due to the OAuth1 turndown, and likely to remain so.  Thanks for your support over the years, and apologies for the lack of prior notice.**

GoogleCL brings Google services to the command line.

We currently support the following Google services:<br>
<ul><li><b>Blogger</b>
<blockquote><code>$ google blogger post --title "foo" "command line posting"</code></blockquote></li></ul>

<ul><li><b>Calendar</b>
<blockquote><code>$ google calendar add "Lunch with Jim at noon tomorrow"</code></blockquote></li></ul>

<ul><li><b>Contacts</b>
<blockquote><code>$ google contacts list Bob --fields name,email &gt; the_bobs.csv</code></blockquote></li></ul>

<ul><li><b>Docs</b>
<blockquote><code>$ google docs edit "Shopping list"</code></blockquote></li></ul>

<ul><li><b>Finance</b>
<blockquote><code>$ google finance create-txn "Savings Portfolio" NASDAQ:GOOG Buy</code></blockquote></li></ul>

<ul><li><b>Picasa</b>
<blockquote><code>$ google picasa create "Cat Photos" ~/photos/cats/*.jpg</code></blockquote></li></ul>

<ul><li><b>Youtube</b>
<blockquote><code>$ google youtube post --category Education killer_robots.avi</code></blockquote></li></ul>

Check out the <a href='Manual.md'>Manual</a> and <a href='ExampleScripts.md'>ExampleScripts</a> for many more examples of what you can do, or the <a href='Install.md'>Install</a> page for simple install instructions.<br>
<br>
<h3>News</h3>
<b>3/31/11:</b> I just realized I should've waited for April 1st, and released version 1.0. Missed opportunities. The good news is, 0.9.13 contains some much needed improvements on 0.9.12, namely:<br>
<ul><li>Appropriate intermediate directories are created for authentication tokens.b<br>
</li><li>Deletion of recurring Calendar events actually deletes events, rather than crashing.<br>
</li><li>File extensions for Picasa do not have to be lowercase.</li></ul>

<b>1/21/11:</b> Keeping with the theme of inappropriate version numbers, 0.9.12 is finally out! Are the following features worth the wait?<br>
<ul><li>Google Finance support (thanks, bartosh!)<br>
</li><li>Expanded usage of --date<br>
</li><li>--access option for privacy settings<br>
</li><li>Reading options and arguments from stdin<br>
If not, you should read the changelog for the rest of the updates. And if the answer is still no... then I apologize.  You may have noticed that development has slowed drastically.  Unfortunately, GoogleCL is now a 100% free-time project for everyone involved.  We're still working on it, though, so keep those bug reports and feature requests coming!</li></ul>

<b>10/10/10:</b> .deb file is up, sorry for the delay. The Windows machine I used to make the executable was apparently 64-bit, and so it play nice on 32-bit systems. I've marked it as such in the downloads page, and a 32-bit version will be up tomorrow with any luck. Thanks for your patience!<br>
<br>
<b>10/8/10:</b> 0.9.11 makes its appearance. Don't miss our wonderful new features:<br>
<ul><li>Much better unicode support.<br>
</li><li>More natural specification of command line arguments.</li></ul>

And Windows users, rejoice: this version reintroduces the .zip file containing an executable. A .deb file should be forthcoming this weekend. In that vein, maybe someday soon I'll get GoogleCL properly situated into the various software repositories.<br>
<br>
<b>9/3/10:</b> 0.9.10 is out! Projecting off Gmail and the current rate of releases, we'll be out of "beta" with 0.9.65 or so. Be sure to check out<br>
<ul><li>v2/v3 support for Docs and Contacts. Manipulate arbitrary uploads, list many more details of your contacts.<br>
</li><li>Support for non-latin alphabets<br>
</li><li>Adheres to XDG base directory specification</li></ul>

This release may be more unstable than past ones. Be sure to (responsibly) flood the issue tracker with any oddities you encounter.<br>
<br>
<b>7/28/10:</b> Uploaded 0.9.9 tar and deb. Windows exe will be up once the Windows machine is found and unpacked.<br>
<br>
Highlights for this release include<br>
<ul><li>Download and edit of new-version Google Docs<br>
</li><li>Video upload and download for Picasa<br>
</li><li>--owner option, allowing use of Picasa collaborative albums, listing other user's YouTube uploads, etc.<br>
</li><li>Reminders for added calendar events</li></ul>

<b>6/30/10:</b> Uploaded 0.9.8 tar, deb, and zip with Windows exe.  In the most inappropriately numbered version release to date, this release includes:<br>
<ul><li>Proper login procedure for Apps users<br>
</li><li>setuptools support<br>
</li><li>Uploading directory trees to Docs<br>
</li><li>Multiple-calendar tasks<br>
and a whole lot of other stuff. Huge, huge thanks to our growing list of contributors!</li></ul>

<b>6/20/10:</b> Uploaded 0.9.7 .tar.gz and .deb packages.  Keeping fingers crossed for inclusion into debian and then ubuntu.  0.9.7 adds command history to interactive mode, changes the --date semantics for calendar, and adds list-groups, add-groups and delete-groups features to contacts.  Plus some miscellaneous bugfixes.  Thanks in particular to ericvw and aripollak who contributed patches!<br>
<br>
<b>6/19/10:</b> Wow! What an announcement! Thanks to everyone who's been checking out GoogleCL, and special thanks for the dozens upon dozens of new issues in the tracker.<br>
<br>
<b>Older</b>
You can now grab a Debian/Ubuntu/etc. package or gzipped tar archive of GoogleCL! Check the Downloads tab.<br>
<br>
<h3>Development / Contributing</h3>
The more the merrier. Check out the wiki page on <a href='Contributing.md'>contributing</a>.<br>
<br>
<h3>Dependencies</h3>
The <a href='http://code.google.com/p/gdata-python-client/'>gdata-python-client library</a>.