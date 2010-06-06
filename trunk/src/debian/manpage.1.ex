.\"                                      Hey, EMACS: -*- nroff -*-
.\" First parameter, NAME, should be all caps
.\" Second parameter, SECTION, should be 1-8, maybe w/ subsection
.\" other parameters are allowed: see man(7), man(1)
.TH GOOGLE 1 "June  5, 2010"
.\" Please adjust this date whenever revising the manpage.
.\"
.\" Some roff macros, for reference:
.\" .nh        disable hyphenation
.\" .hy        enable hyphenation
.\" .ad l      left justify
.\" .ad b      justify to both left and right margins
.\" .nf        disable filling
.\" .fi        enable filling
.\" .br        insert line break
.\" .sp <n>    insert n+1 empty lines
.\" for manpage-specific macros, see man(7)
.SH NAME
google \- command\-line access to (some) Google services
.SH SYNOPSIS
.B google
.RI " service task" [ options ] ...
.br
.SH DESCRIPTION
.B google
is a command\-line tool for accessing (a subset of) Google\'s gdata APIs.
Run it without arguments to use an interactive session.
.\" .PP
.\" TeX users may be more comfortable with the \fB<whatever>\fP and
.\" \fI<whatever>\fP escape sequences to invode bold face and italics, 
.\" respectively.
\." \fBgooglecl\fP is a program that...
.SH OPTIONS
These programs follow the usual GNU command line syntax, with long
options starting with two dashes (`-').
A summary of options is included below.
.TP
.B \-h, \-\-help
Show summary of options.
.TP
.B \-u, \-\-user
Specify a Google account to use for this operation.
.\" .SH SEE ALSO
.\" .BR bar (1),
.\" .BR baz (1).
.\" .br
.\" The programs are documented fully by
.\" .IR "The Rise and Fall of a Fooish Bar" ,
.\" available via the Info system.
.SH AUTHOR
googlecl was written by Tom H. Miller <tom.h.miller@gmail.com>.
.PP
This manual page was written by Jason Holt <jholt@google.com>.
