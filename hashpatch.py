#!/usr/bin/python

import re, hashlib, os, base64, pickle, itertools, shutil

sourceDir = "/Users/ryan/Pictures/iPhoto Library/Originals"
destDir = "/Volumes/ryan/Pictures"

pattern = ".*\.jp[e]?g$" 

shaFieldSep = "  "
sha512ext = ".sha512"

numSkippedFiles = 0

def loadFromFile(filepath):
	hashDict = dict()

	f = open(filepath, 'r')
	for line in f.readlines():
		line = line.rstrip()

		(lineHash, mypath) = line.split('  ', 1)

		myhash = base64.b16decode(lineHash.upper())

		#print lineHash
		#print linePath
		if (myhash not in hashDict):
			# map the binary hash (digest) to the file path
			hashDict[myhash] = [mypath]
		else: 
			# This hash is already associated with a list
			hashDict[myhash].append( mypath )
							
		#print lineHash + shaFieldSep + repr(hashDict[myhash])

	f.close()

	return hashDict

def saveToFile(hashDict, filePath):

	f = open(filePath, 'w')

	for key, val in hashDict.items():

		for path in val:

			f.write(base64.b16encode(key).lower() + shaFieldSep + path + "\n")

	f.close()

def hashDictFindPath (hashDict, searchPath):
	# This is not a very efficient algorithm
	for key, pathList in hashDict.items():
		for path in pathList:
			if (searchPath == path):
				return key

	return False

def buildHashDict (path, hashDict = dict()):
	global numSkippedFiles

	expand = len(hashDict) > 0
	
	fileMatcher = re.compile(pattern, re.IGNORECASE)
	
	for root, dirs, files in os.walk(path):
		#for filename in fnmatch.filter(files, pattern):
		for filename in files:
			if (fileMatcher.match(filename)):
				mypath = os.path.join(root, filename)

				# If we are expanding and this path is anywhere in the dictionary:
				#if (expand and (mypath in list(itertools.chain(hashDict.values())))):
				if (expand and (hashDictFindPath(hashDict, mypath) != False)):
					numSkippedFiles += 1
					if ((numSkippedFiles % 100) == 0):
						print ".",
					continue

				try:
					f = open (mypath, 'r')
					myhash = hashlib.sha512(f.read())
					f.close()
					#print myhash.hexdigest() + "  \"" + mypath + "\""

					if (myhash.digest() not in hashDict):
						# map the binary hash (digest) to the file path
						hashDict[myhash.digest()] = [mypath]
					else: 
						# Duplicate file found
						#print "^^^ A duplicate file ^^^"
						#print hashDict[myhash.digest()]
						#if (type(hashDict[myhash.digest()]) == type(str())):
							## This is the first duplicate
							#hashDict[myhash.digest()] = [ hashDict[myhash.digest()], mypath ]
						#else:

						# This hash is already associated with a list
						hashDict[myhash.digest()].append( mypath )
							
					print myhash.hexdigest() + shaFieldSep + repr(hashDict[myhash.digest()]) 

				except IOError as error:
					print error

	print "Ended with %d unique hashes" % len(hashDict)

	return hashDict

def buildAndSaveHashDict (variableName, searchPath, hashDict=dict()):
	global sha512ext

	hashDict = buildHashDict (searchPath, hashDict)
	sha512filename = "hashpatch." + variableName + sha512ext
	saveToFile(hashDict, sha512filename)
	#pickleFilename = "hashpatch." + variableName + ".pickle"
	#pickleFile = open(pickleFilename, "w")
	#pickle.dump(hashDict, pickleFile)
	#pickleFile.close()
	
	return hashDict

def openOrBuildHashDict (variableName, searchPath):
	global sha512ext
	
	sourceFilename = "hashpatch." + variableName + sha512ext

	if (os.path.exists(sourceFilename)):
		print "Loading from file '%s'" % sourceFilename, 
		#sourcePickle = open(sourcePickleFilename, "r")
		#hashDict = pickle.load(sourcePickle)
		#sourcePickle.close()	
		hashDict = loadFromFile(sourceFilename)
	else:
		hashDict = buildAndSaveHashDict(variableName, searchPath)

	print "%d unique hashes" % len(hashDict)

	return hashDict

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

def checkForMissingInDest(sourceHashDict, destHashDict):
	global destDir

	foundMissing = 0 

	rf = open('hashpatch.report', 'w')

	for key, val in sourceHashDict.items():
		if (key not in destHashDict):
			foundMissing += 1
			print base64.b16encode(key) + shaFieldSep + str(val) + " does not exist in destination"
			rf.write(base64.b16encode(key) + shaFieldSep + str(val) + "\n")

			if True:
				sourcePathParts = val[0].split('/')
				destSubDir = '/'.join([destDir, 'iPhoto', sourcePathParts[-3], sourcePathParts[-2]])
				print "Copying " + val[0] + " -> " + destSubDir

				if (not os.path.exists(destSubDir)):
					os.makedirs(destSubDir)
				
				shutil.copy2(val[0], destSubDir)


	print "Found %d missing files in destination" % foundMissing
	rf.close()


