hashpatch
=========

A Python module to update a remote copy, rearrange files to a new structure, and delete duplicates, using simple sha1sum files as storage

Examples
--------

Imagine the following situation: you are ready to delete photos on your portable electronic device and you first want to make sure that each one is backed up on a remote system. However, they have been organized into directories on the remote system.

Hashpatch can help you efficiently verify that all the photos are backed up. The first step is to compute the hashes for the files on the remote host.
```
import hashpatch

remoteHashMap = hashpatch.hashMap('/home/ryan/Pictures')
remoteHashMap.update()
```

Then, you can take at least two paths. First, you can mount the remote filesystem on the local host. 

Load a hash map for local and a remote (mounted) directories and delete all duplicates in the local directory.

```
import hashpatch

localHashMap = hashpatch.hashMap('/Users/ryan/Pictures/iPhoto Library/Originals')
localHashMap.update()

remoteHashMap = hashpatch.hashMap('/Volumes/ryan/Pictures')

hashpatch.deleteDupsInDest(remoteHashMap, localHashMap)
hashpatch.checkForMissingInDest(localHashMap, remoteHashMap, destSubDir='iPhoto', act=True)
```

