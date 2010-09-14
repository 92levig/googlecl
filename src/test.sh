#!/bin/bash

TOUCH_PREFIX="tested_"
GOOGLE_SH=./google.py

# List of commands to set by each function
declare -a commands

# Commands to run for cleaning up test account
#declare -a cleanup_commands

function blogger {
	echo 'This is my post from a file\nIt contains a few line breaks, but not much else.' > test_post.txt
  commands[0]='blogger post --tags delete test_post.txt'
	commands[1]='blogger list title,author'
	commands[2]='blogger post -n CL_post_test "This is my post from a command line"'
	commands[3]='blogger tag -t delete -n CL_post_*'
	rm test_post.txt
}

function calendar {
	commands[0]='calendar add "test event at 5pm on 10/10/10"'
	commands[1]='calendar add "test event at midnight on 10/10/10"'
	commands[2]='calendar add "test event today at 3" --reminder 1h'
	commands[3]='calendar today'
	commands[4]='calendar list --date 2010-10-10'
}

function contacts {
	echo -e 'contacts csv1, test_csv1@eh.com\ncontacts csv2, test_csv2@eh.com' > contacts.csv
	commands[0]='contacts add "contacts test1,test_email1@nowhere.com" "contacts test2,test_email2@nowhere.com"'
	commands[1]='contacts add contacts.csv'
	commands[2]='contacts add "contacts test1,test_email1@nowhere.com"'
	commands[3]='contacts list -n contacts'
  commands[4]='contacts add-groups test_group'
  commands[5]='contacts list-groups'
	rm contacts.csv
}

function docs {
	echo -e 'This is a document that I am about to upload.' > test_doc.txt
	commands[0]='docs upload test_doc.txt'
	commands[1]='docs get --title test_doc test_download.txt'
	commands[2]='docs list title,url-direct --delimiter ": "'
	commands[3]='docs edit --title test_doc'
}

function picasa {
	commands[0]='picasa create --title "test_album" --tags "test, Disney World, florida, vacation" ~/Photos/Disney/dscn211*.jpg'
	commands[1]='picasa create --title "test_album"'
	commands[2]='picasa list title,url-site -q test'
	commands[3]='picasa list-albums title,url-site'
	commands[4]='picasa delete --title "nosuchalbumexists"'
	commands[5]='picasa delete --title delete_album'
	commands[6]='picasa get -n "Disney trip" ./'
	commands[7]='picasa post -n "Disney trip" --tags "Disney World, florida, vacation" ~/Photos/Disney/dscn212*.jpg'
	commands[8]='picasa tag -n "nosuchalbumexists" -t tag1,tag2'
	commands[9]='picasa tag -n "Disney trip" -t tag1,tag2'
}

function youtube {
	commands[0]='youtube post ~/Downloads/fighting_cats4.wmv -n "Test cat movie" -s "More cats on youtube" --category Education --tags test,cats'
	commands[1]='youtube list'
	commands[2]='youtube tag -n "cat" -t "cats, currency of the internet"'
	commands[3]='youtube tag -n "D_N_E" -t wontgothrough'
	commands[4]='youtube post ~/D_N_E -n failure -c Education'
}

function goog_help {
	commands[0]="help"
}

prompt_quit() {
	echo Hit Ctrl-C again to exit, enter to skip current command
	read junk
}

trap prompt_quit INT
clear

if [ ${#@} -eq 1 ] && [ $@ == all ]; then
	TASKS=( blogger calendar contacts docs picasa youtube )
else
	TASKS=$@
fi

for task in ${TASKS[*]}
do
	unset commands
	echo -e "\n"
	echo ===$task===
	if [ $task == blogger ]; then
		blogger
	fi
	if [ $task == calendar ]; then
		calendar
	fi
	if [ $task == contacts ]; then
		contacts
	fi
	if [ $task == docs ]; then
		docs
	fi
	if [ $task == picasa ]; then
		picasa
	fi
	if [ $task == youtube ]; then
		youtube
	fi
	if [ $task == help ]; then
		goog_help
	fi
  # Make note of which tasks have been run, for cleanup later
	eval touch "$TOUCH_PREFIX$task"
	for index in ${!commands[*]}; do
		echo -e "\n===${commands[$index]}"
		eval $GOOGLE_SH ${commands[$index]}
	done
done
