#!/usr/bin/env python3

from ftplib import FTP_TLS
import os
import hashlib
import json
import pickle
import logging

class SyncFile(object):
    def __init__(self, root, path, name, checksum):
        self.isDirectory = False
        self.root = root
        self.path = path
        self.name = name
        self.checksum = checksum

class SyncDirectory(object):
    def __init__(self, root, name, directories, files):
        self.isDirectory = True
        self.root = root
        self.directories = directories
        self.name = name
        self.files = files

class FTP2(FTP_TLS):
    def __init__(self, host):
        super().__init__(host)

    def ftpFileStore(self, filepath, name):
        with open(filepath, 'rb') as localfile:
            self.storbinary('STOR ' + name, localfile)

    def ftpFileRetrevie(self, filepath, name):
        with open(filepath, 'wb') as localfile:
            self.retrbinary('RETR ' + name, localfile.write, 1024)

class DelException(Exception):
    def __init__(self, message):
        super().__init__(message)

def enum(**enums):
    return type('Enum', (), enums)

# https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096*16), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# create a settings.py file and put all this inside:
# path to local directory where sync should monitor
scanpath = ""

# server path where data should be pushed
virtualpath = ""

# database name where file checksums are stored
filename = ""

# ftp server info
ftpUsername = ''
ftpPassword = ''
ftpURL = ''

HistoryFiles = {}
SyncFiles = {}

if os.path.exists('settings.py'):
    from settings import *

lwd = None
Sync = True

# loading previous sync info, folder lists, file lists with their checksum
try:
    with open(filename, 'rb') as stream:
        HistoryFiles = pickle.load(stream)

except FileNotFoundError as ex:
    print("Sync history not found!")
    Sync = False

try:
    if Sync:
        ftps = FTP2(ftpURL)
        ftps.login(user=ftpUsername, passwd=ftpPassword, secure=True)
        print(ftps.getwelcome())

    # scanning directory for folders, files, changes
    for root, directories, files in os.walk(scanpath):
        froot = root.replace('\\', '/')

        # new files, modified files
        for fname in files:
            fpath = os.path.join(root, fname)
            fpath = fpath.replace('\\', '/')
            fmd5 = md5(fpath)
            
            if fpath not in HistoryFiles:
                push = True
            elif HistoryFiles[fpath].checksum != fmd5:
                push = True
            else:
                push = False

            if push:
                cwd = virtualpath + froot[len(scanpath):]
                cwd = cwd.replace('\\', '/')
                
                if Sync:
                    cwd = cwd.replace('\\', '/')
                    ftps.cwd(cwd)              
                    ftps.ftpFileStore(fpath, fname)

                print('NEWFLE ', fpath, '>', cwd)

            SyncFiles[fpath] = HistoryFiles[fpath] = SyncFile(froot, fpath, fname, fmd5)

        # new directories
        for dname in directories:
            dpath = os.path.join(froot, dname)
            dpath = dpath.replace('\\', '/')

            if dpath not in HistoryFiles:
                push = True
            else:
                push = False

            if push:
                cwd = virtualpath + froot[len(scanpath):]
                cwd = cwd.replace('\\', '/')

                if Sync:
                    ftps.cwd(cwd)              
                    ftps.mkd(dname)

                SyncFiles[dpath] = HistoryFiles[dpath] = SyncDirectory(dpath, dname, None, None)
                print('NEWDIR ', dname, '>', cwd)

        SyncFiles[froot] = HistoryFiles[froot] = SyncDirectory(froot,os.path.basename(froot), directories, files)

    def DirectoryDelete(path, syncobj):
        # call on subdirectories
        for d in syncobj.directories:
            i =  os.path.join(path, d)
            DirectoryDelete(i, HistoryFiles[i])

        # delete files in i
        for f in syncobj.files:
            fpath = os.path.join(path, f)
            fpath = fpath.replace('\\', '/')  
            cwd = virtualpath + syncobj.root[len(scanpath):]
            cwd = cwd.replace('\\', '/')            

            if Sync:
                ftps.cwd(cwd)       
                ftps.delete(f)

            del HistoryFiles[fpath]
            print('DELFLE', fpath)

        # delete directories
        cwd = virtualpath + syncobj.root[len(scanpath):]
        cwd = cwd[:len(cwd) - len(syncobj.name)]
        cwd = cwd.replace('\\', '/')

        if Sync:
            ftps.cwd(cwd)
            ftps.rmd(syncobj.name)

        del HistoryFiles[path]
        print('DELDIR', path)

    # delete
    delete = None
    while 1:
        try:
            for i in HistoryFiles:
                if i not in SyncFiles:
                    if HistoryFiles[i].isDirectory:
                        if HistoryFiles[i].root == scanpath:
                            continue

                    delete = HistoryFiles[i]
                    break
                    
            if delete:
                raise Exception
            else:
                break
        except:
                # first candidate for delete
                if delete.isDirectory:
                    DirectoryDelete(i, delete)
                else:
                    if Sync:
                        cwd = virtualpath + delete.root[len(scanpath):]
                        cwd = cwd.replace('\\', '/')
                        ftps.cwd(cwd)       
                        ftps.delete(delete.name)
                    del HistoryFiles[delete.path]
                    print('DELFLE', delete.path)
                
                delete = None

except Exception as ex:
    print(ex)

finally:
    # updating sync info
    with open(filename, 'wb') as stream:
        pickle.dump(HistoryFiles, stream)
    
    if Sync:
        ftps.quit()
