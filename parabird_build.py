#!/usr/bin/env python
# encoding: utf-8 

import argparse
import ConfigParser
import codecs
import urllib
import subprocess
import sys
import os
import tempfile
import shlex
import shutil
import tarfile
import zipfile
from utils import detect_stick
import logging
from utils import *
from sys import exit

# PLATFORM SPECIFIC SHIT
# http://docs.python.org/2/library/sys.html#sys.platform
# There exists another path to the truecrypt binary, also tc 
# is NOT in the path. We don't support Win32.
if (sys.platform=="darwin"):
    parser.set('truecrypting','tc_binary',parser.get('truecrypting','tc_mac_binary'))
    extract_dmg = extract_dmg_mac
elif (sys.platform=="win32"):
    mainLogger.error("parabirdy does'nt run on windows. by us a windows license (and some gifts) or reboot in linux. virtualisation might also work")
    exit()

# Removed, because there is no verbosity support, could be reimplemented later.
# see the logging module for built in verbosity support
#if args.verbose:
#   mainLogger.info("verbosity turned on")

print "%" * 30, "\nChecking Dependencies and Configure\n", "%" * 30

print "Tempdir is:", tempdir

mainLogger.info("Checking all Dependencies...")

try:
    mainLogger.debug("truerypt binary is {}".format(parser.get('truecrypting', 'tc_binary')))
    dependency_check([parser.get('truecrypting', 'tc_binary'), "--text", "--version"])
    dependency_check("7z")
    if (sys.platform=="darwin"):
        dependency_check(["hdiutil", "info"])
    else:
        dependency_check("dmg2img")
except: 
    mainLogger.error("Dependency Checks failed large scale, exiting...")
    mainLogger.exception("Dependency Checks failed large scale, exiting...")
    raise
    exit()



mainLogger.info("[INFO] Configuring...")

# Setting Parameters given from argparse

try:
    update_config("DEFAULT", "device", args.device)
    #update_config("thunderbird", "version", args.thunder)
    #update_config("torbirdy", "version", args.torbirdy)
    #update_config("enigmail", "version", args.enigmail)
    #update_config("vidalia", "version", args.vidalia)
    update_config("DEFAULT", "container_name", args.container_name)
    update_config("truecrypting", "size", args.container_size)

except NameError: 
    mainLogger.error("[ERROR] Hier ist was ganz arg schiefgelaufen")
    mainLogger.exception("[ERROR] Hier ist was ganz arg schiefgelaufen")


# Setting Path Parameters given by tempfile
#tempdir = os.path.realpath(tempfile.mkdtemp())
#tc_mountpoint = os.path.realpath(tempfile.mkdtemp())

print "%" * 30, "\nMounting and Truecrypting\n", "%" * 30

# Use an USB-Stick given by a Parameter or a detected one:
if args.device:
    try:
        mountpoint = os.path.realpath(tempfile.mkdtemp())
        update_config("DEFAULT", "device", args.device)
	
    except NameError:
        mainLogger.error("[ERROR] Hier ist was ganz arg schiefgelaufen")
        mainLogger.exception("[ERROR] Hier ist was ganz arg schiefgelaufen")
else: 
    stick = detect_stick()
    #print stick

    #did autodetection work? and can we write?
    #if we can write to the mountpoint of the stick, no need to re-mount it
    if stick['mountpoint'] and (not(os.access(str(stick['mountpoint']), os.W_OK))): 
        #aka we cant write or stick detection did not work
        #question is: does it make sense to continue at this point?
        #which scenarios are possible (except detection not working)
        mountpoint = os.path.realpath(tempfile.mkdtemp())
        mainLogger.error("Stick detection did not work, try to run with what you specified")
        mainLogger.info('[INFO] Mounting USB Stick to' + mountpoint)

        try:
            subprocess.check_call(["mount", parser.get('DEFAULT', 'device'), mountpoint])
        except:
            mainLogger.error("Mounting {} to {} failed".format(parser.get('DEFAULT', 'device', mountpoint)))
            mainLogger.exception("Mounting {} to {} failed".format(parser.get('DEFAULT', 'device', mountpoint)))
            raise

    #ok, we can write to the stick        
    else:
        parser.set('DEFAULT', "device", stick['device'])
        mountpoint = stick['mountpoint']

# Setting the Path for Truecrypt
parser.set('DEFAULT', 'container_path', mountpoint+"/"+parser.get('DEFAULT', 'container_name'))
mainLogger.debug("Container Path is: {}".format(parser.get('DEFAULT', 'container_path')))

parser.set('DEFAULT', 'tc_mountpoint', tc_mountpoint)
mainLogger.debug("TC Mountpoint is: {}".format(parser.get('DEFAULT', 'tc_mountpoint')))


#Multiple Variables like this, because the logger only takes 1 argument:
mainLogger.info("[INFO] Creating Container " + parser.get('DEFAULT', 'container_name') + " on USB-Stick: " + parser.get('DEFAULT', 'device'))

# Exit if the container already exists
if os.path.exists(parser.get('DEFAULT', 'container_path')):
    mainLogger.info("The Container given ("+ parser.get('DEFAULT', 'container_path')+") already exists. Exiting...")
    exit()

# Create Container
mainLogger.info('Truecrypting create: '+ parser.get('truecrypting', 'create'))
subprocess.check_call(shlex.split(parser.get('truecrypting', 'create')))

# Mount Container
mainLogger.info("[INFO] Mounting Truecrypt Container")
subprocess.check_call(shlex.split(parser.get('truecrypting', 'mount')))

# Create Folders
mainLogger.info("[INFO] Creating Folders in Truecrypt Container:")

try:
    os.makedirs(parser.get('thunderbird_linux', 'path'))
    os.makedirs(parser.get('vidalia_linux', 'path'))

    os.makedirs(parser.get('thunderbird_windows', 'path'))
    os.makedirs(parser.get('vidalia_windows', 'path'))

#    os.makedirs(parser.get('thunderbird_mac', 'path'))
    os.makedirs(parser.get('vidalia_mac', 'path'))

    os.makedirs(parser.get('enigmail', 'path'))
    os.makedirs(parser.get('torbirdy', 'path'))	

    # for extracting tb for mac os, we need to mount a dmg
    # i create an subfolder in tempdir for doing this
    os.makedirs(tempdir+"/dmg")

except OSError:
    mainLogger.error("[ERROR] Folder already exists")
    mainLogger.exception("[ERROR] Folder already exists")


# Download Applications	
mainLogger.info('[INFO] Starting to download Applications to: ' + tempdir)

download_application("Thunderbird [Linux]", parser.get('thunderbird_linux', 'url'), parser.get('thunderbird_linux', 'file'))
download_application("Thunderbird [Windows]", parser.get('thunderbird_windows', 'url'), parser.get('thunderbird_windows', 'file'))
download_application("Thunderbird [Mac OS]", parser.get('thunderbird_mac', 'url'), parser.get('thunderbird_mac', 'file'))
download_application("Torbirdy", parser.get('torbirdy', 'url'), parser.get('torbirdy', 'file'))
download_application("Enigmail", parser.get('enigmail', 'url'), parser.get('enigmail', 'file'))
download_application("Vidalia [Linux]", parser.get('vidalia_linux', 'url'), parser.get('vidalia_linux', 'file'))
download_application("Vidalia [Windows]", parser.get('vidalia_windows', 'url'), parser.get('vidalia_windows', 'file'))
download_application("Vidalia [Mac OS]", parser.get('vidalia_mac', 'url'), parser.get('vidalia_mac', 'file'))
download_application("GPG 4 Thunderbird [Windows]", parser.get('gpg4tb', 'url'), parser.get('gpg4tb', 'file'))
download_application("GPG 4 USB [Linux]", parser.get('gpg4usb', 'url'), parser.get('gpg4usb', 'file'))
download_application("GPG Tools [Mac OS]", parser.get('gpg4mac', 'url'), parser.get('gpg4mac', 'file'))

extract_tarfile("Thunderbird [Linux]", tempdir+"/"+parser.get('thunderbird_linux', 'file'), parser.get('thunderbird_linux', 'path'))

#mainLogger.info("[INFO] Extracting Thunderbird [Windows]")

# extract_dmg("Thunderbird [Mac OS]", dmg , img, path)

mainLogger.info("[INFO] Extracting Thunderbird [Mac OS]")
extract_dmg("Thunderbird [Mac OS]",os.path.join(tempdir, parser.get('thunderbird_mac', 'file')), parser.get('thunderbird_mac', 'path') )

extract_tarfile("Vidalia [Linux]", tempdir+"/"+parser.get('vidalia_linux', 'file'), parser.get('vidalia_linux', 'path'))

#mainLogger.info("[INFO] Extracting Vidalia [Windows"]
# extract_7zfile("Vidalia [Windows]", ..., ...)

extract_zipfile("Vidalia [Mac OS]", tempdir+"/"+parser.get('vidalia_mac', 'file'), parser.get('vidalia_mac', 'path'))
extract_zipfile("Torbirdy", tempdir+"/"+parser.get('torbirdy', 'file'), parser.get('torbirdy', 'path'))
extract_zipfile("Enigmail", tempdir+"/"+parser.get('enigmail', 'file'), parser.get('enigmail', 'path'))

# extract_zip("GPG 4 USB [Linux]", ..., ...)
# extract_7z("GPG 4 Thunderbird [Windows]", ..., ...)
# extract_dmg("GPG Tools [Mac OS]", ..., ...)

# Unmounting Truecrypt
mainLogger.info("[INFO] Unmounting Truecrypt Container")
mainLogger.debug('UNMOUNT COMMAND: ' + parser.get('truecrypting', 'unmount'))
subprocess.check_call(shlex.split(parser.get('truecrypting', 'unmount')))

# Unmounting USB-Stick
mainLogger.info("[INFO] Unmounting USB-Stick")

try:
    subprocess.check_call(["umount", mountpoint])

except:
    
    if (sys.platform=="darwin"):
       mainLogger.info("[INFO] please unmount your stick via the finder.")
    else:
        mainLogger.error("[Error] Unmounting", + mountpoint, + "failed")
        

# Removing Temporary folders
mainLogger.info("[INFO] Cleaning up Temporary Directories")

try:
    if args.device:
        os.removedirs(mountpoint)
    os.removedirs(tempdir)
    os.removedirs(tc_mountpoint)
except OSError:
    mainLogger.error("Some temporary Directories could not be removed")
    mainLogger.exception("Some temporary Directories could not be removed")
