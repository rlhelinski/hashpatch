import hashpatch

lhs = hashpatch.hashMap('/Users/ryan/Pictures/iPhoto Library/Originals')
lhs.update()
#rhs = hashpatch.hashMap(sourceFile='/Users/ryan/Pictures-revelator.sha512.bz2')
rhs = hashpatch.hashMap('/Volumes/ryan/Pictures')
# This update should be done on the remote host before-hand
#rhs.update()

#hashpatch.deleteDupsInDest(rhp, lhp)
hashpatch.checkForMissingInDest(lhs, rhs, act=False)

