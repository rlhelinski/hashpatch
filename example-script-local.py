import hashpatch

localHashMap = hashpatch.hashMap('/Users/ryan/Pictures/iPhoto Library/Originals')
localHashMap.update()

remoteHashMap = hashpatch.hashMap('/Volumes/ryan/Pictures')


#hashpatch.deleteDupsInDest(remoteHashMap, localHashMap)
hashpatch.checkForMissingInDest(localHashMap, remoteHashMap, destSubDir='iPhoto', act=False)

