#!/usr/bin/python

import re, hashlib, os, base64, pickle, itertools, shutil

shaFieldSep = "  "
sha512ext = ".sha512"

numSkippedFiles = 0

class hashMap:
	# Variables declared here are class-static

	def __init__(self, rootPath="", source=None):
		self.rootPath = ""
		self.hashDict = dict()
		self.reverseDict = dict()
		self.savePath = ""

		if (rootPath != "" and os.path.isdir(rootPath)):
			self.rootPath = rootPath
		else: 
			raise NameError("Root path given is not a directory")

		if (os.path.isfile(source)):
			self.load(source)

	def __len__(self):
		# this is the number of unique hashes. With a reverse map, I could easily list the number of files
		#return (len(self.hashDict))
		return (len(self.reverseDict))

	# This function finds the hash of a file based on its path
	def findByPath (self, searchPath):
		if (searchPath not in self.reverseDict):
			return False
		else:
			return self.reverseDict[searchPath]

		# This is not a very efficient solution---a reverse map could be built
		#for key, pathList in self.hashDict.items():
			#for path in pathList:
				#if (searchPath == path):
					#return key
		#return False

	# This function builds a hash dict object for a files in a path
	def update(self, pattern=".*", verbose=False):
		global numSkippedFiles

		expanding = len(self.hashDict) > 0
	
		fileMatcher = re.compile(pattern, re.IGNORECASE)
	
		for root, dirs, files in os.walk(self.rootPath):
			#for filename in fnmatch.filter(files, pattern):
			for filename in files:
				if (fileMatcher.match(filename)):
					mypath = os.path.join(root, filename)
	
					# If we are expanding and this path is anywhere in the dictionary,
					# do not update the hash
					#if (expand and (mypath in list(itertools.chain(hashDict.values())))):
					if (expanding and (self.findByPath(mypath) != False)):
						numSkippedFiles += 1
						if (verbose and ((numSkippedFiles % 100) == 0)):
							print ".",
						continue

					try:
						# Open the file and compute the hash
						f = open (mypath, 'r')
						myhash = hashlib.sha512(f.read())
						f.close()
						#print myhash.hexdigest() + "  \"" + mypath + "\""
	
						if (myhash.digest() not in self.hashDict):
							# map the binary hash (digest) to the file path
							self.hashDict[myhash.digest()] = [mypath]
						else: 
							# Duplicate file found
							# This hash is already associated with a list
							self.hashDict[myhash.digest()].append( mypath )
						# also map the path to the hash
						self.reverseDict[mypath] = myhash.digest()
							
						if (verbose):
							print myhash.hexdigest() + shaFieldSep + repr(self.hashDict[myhash.digest()]) 
	
					except IOError as error:
						print error
	
		print "Ended with %d files, %d unique hashes" % (len(self.reverseDict), len(self.hashDict))
	
		return self

	def load(self, filePath):
		self.savePath = filePath
		f = open(filePath, 'r')
		for line in f.readlines():
			line = line.rstrip()
	
			(lineHash, mypath) = line.split('  ', 1)
	
			myhash = base64.b16decode(lineHash.upper())
	
			#print lineHash
			#print linePath
			if (myhash not in self.hashDict):
				# map the binary hash (digest) to the file path
				self.hashDict[myhash] = [mypath]
			else: 
				# This hash is already associated with a list
				self.hashDict[myhash].append( mypath )
			# also map the path to the hash
			self.reverseDict[mypath] = myhash
								
			#print lineHash + shaFieldSep + repr(hashDict[myhash])

		f.close()

		return self

	def save(self, filePath=None):
		if (filePath == None):
			filePath = self.savePath

		f = open(filePath, 'w')

		for key, val in self.hashDict.items():
			for path in val:
				f.write(base64.b16encode(key).lower() + shaFieldSep + path + "\n")

		f.close()
	
	def buildAndSave (self, variableName):
		global sha512ext

		self.update (self.rootPath)
		sha512filename = "hashpatch." + variableName + sha512ext
		self.save(sha512filename)
		#pickleFilename = "hashpatch." + variableName + ".pickle"
		#pickleFile = open(pickleFilename, "w")
		#pickle.dump(hashDict, pickleFile)
		#pickleFile.close()
	
		return self






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
				
				#shutil.copy2(val[0], destSubDir)


	print "Found %d missing files in destination" % foundMissing
	rf.close()

def deleteInDest (sourceMap, destMap, act=False):
	foundDup = 0

	rf = open('hashpatch.report', 'a')

	for key, val in destMap.hashDict.items():
		if (key in sourceMap.hashDict):
			foundDup += 1
		
			if act:
				for path in val:
					print "Removing '%s'" % path
					os.remove(path)
					# delete the parent directory if it is empty
					if (not os.listdir(os.path.dirname(path))):
						# This is a function that recursively removes empty directories
						os.removedirs(os.path.dirname(path))

	print "%s %d duplicate files in destination" % ("Deleted" if act else "Found", foundDup)
	rf.close()
	
def deleteBrokenLinks (path, act=False):
	
	for root, dirs, files in os.walk(path):
		for filename in files:
			#print filename
			if (os.path.islink(os.path.join(root, filename))):
				#print "Link at %s/%s" % (root, filename)
				if(not os.path.exists(os.path.join(root, filename))):
					if (act):
						os.remove(os.path.join(root, filename))
						if (not os.listdir(root)):
							# This is a function that recursively removes empty directories
							os.removedirs(root)
					print "%s broken link at %s/%s" % ("Deleted" if act else "Found", root, filename)
					
def deleteEmptyDirs (path, act=False):		

	for root, dirs, files in os.walk(path):
		#for dir in dirs:
		if (not os.listdir(root)):
			# This is a function that recursively removes empty directories
			if (act):
				os.removedirs(root)
			print "%s empty directory at %s" % ("Deleted" if act else "Found", root)


