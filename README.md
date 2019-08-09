# SyncFTP

1) clone the repository
2) setup the settings in script : scanpath, virtualpath, filename, ftpUsername, ftpPassword, ftpURL or you can create a
settings.py
```python
ftpUsername = "ftpuser"
ftpPassword = "ftppassword"
ftpURL = 'ftp.service.com'
scanpath = "C:/Users/app/publish/"
virtualpath = '/app/dev/'
filename = 'app.dictionary'
```

3) run the file

How it works?
------
running for the first time it will checksum scanpath, assuming it has been mapped to your ftp as virtualpath creating file info database with filename.
next time you run, it will look for changes in directory, files for add/delete/modifications.
* for settings.py and filename to work you will need to make sure you run with same current working dir 
