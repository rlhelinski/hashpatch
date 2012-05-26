from hashfuncs import *

################################################################################
sourceDir = "Compress-1260381162"
destDir = "Compress"

#>>> myhash = hashlib.sha512("Hello, World!")
#>>> myhash.hexdigest()
#'374d794a95cdcfd8b35993185fef9ba368f160d8daf432d08ba9f1ed1e5abe6cc69291e0fa2fe0006a52570ef18c19def4e617c33ce52ef0a6e5fbe318cb0387'
#>>> myhash.digest()
#'7MyJ\x95\xcd\xcf\xd8\xb3Y\x93\x18_\xef\x9b\xa3h\xf1`\xd8\xda\xf42\xd0\x8b\xa9\xf1\xed\x1eZ\xbel\xc6\x92\x91\xe0\xfa/\xe0\x00jRW\x0e\xf1\x8c\x19\xde\xf4\xe6\x17\xc3<\xe5.\xf0\xa6\xe5\xfb\xe3\x18\xcb\x03\x87'
#>>> base64.b16encode(myhash.digest())
#'374D794A95CDCFD8B35993185FEF9BA368F160D8DAF432D08BA9F1ED1E5ABE6CC69291E0FA2FE0006A52570EF18C19DEF4E617C33CE52EF0A6E5FBE318CB0387'
# base64.b16decode()
#
		
sourceHashDict = openOrBuildHashDict ("sourceHashDict", sourceDir)

#sourcePickleFilename = "hashpatch.source.pickle"

#destHashDict = buildHashDict (destDir)
destHashDict = openOrBuildHashDict ("destHashDict", destDir)


# It should also be trivial to convert a checksum file (format: "<hash> <path>") into a HashDict

# Now what I wanted to do when I woke up this morning: 
# Go through all the files in the source, check if it already exists in the destination,
# and copy it there if it does not. 


