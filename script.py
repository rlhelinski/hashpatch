import hashpatch

lhp = hashpatch.hashMap('/Users/ryan/Pictures')
lhp.update()
rhp = hashpatch.hashMap(sourceFile='/Users/ryan/Pictures-revelator.sha512.bz2')
hashpatch.deleteDupsInDest(rhp, lhp)

