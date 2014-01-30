#!/usr/bin/python
#
# TODO store directory size in HashMap class. Maintain it through add and del operations
#

import re, hashlib, os, sys, base64, pickle, itertools, shutil, sys
import progressbar

shaFieldSep = "  "
sha512ext = "sha512"
bz2ext = "bz2"

# http://stackoverflow.com/questions/7829499/using-hashlib-to-compute-md5-digest-of-a-file-in-python3
def hashChunkFile(digestFunc, filename, chunk_size = 4096):
    from functools import partial
    with open(filename, mode='r') as f:
        d = digestFunc()
        #for buf in iter(partial(f.read, chunk_size), b''):
        while True:
            buf = f.read(chunk_size)
            d.update(buf)
            if not buf:
                break
    return d

def getDirSize(path):
    dirSize = 0
    for root, dirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root,filename)
            if os.path.isfile(filepath):
                try:
                    dirSize += os.path.getsize(filepath)
                except OSError as error:
                    None # this is just an estimating phase
    return dirSize


class hashMap:
    # Variables declared here are class-static

    widgets = ["Progress: ", progressbar.Bar(marker="=", left="[", right="]"), " ", progressbar.Fraction(), " ", progressbar.Percentage(), " ", progressbar.ETA() ]

    def __init__(self, rootPath="", sourceFile="", excludePattern=".*\.svn.*"):
        self.rootPath = ""
        self.hashDict = dict()
        self.reverseDict = dict()
        self.savePath = ""

        if (rootPath != ""):
            if (os.path.isdir(rootPath)):
                self.rootPath = rootPath.rstrip("/")
                self.savePath = os.path.join(os.path.dirname(self.rootPath),
                        '.'+os.path.basename(self.rootPath)+'.'+sha512ext)
                    #'.'.join([os.path.basename(self.rootPath), int(time.time()), sha512ext]))
            else:
                raise NameError("Root path given is not a directory")

        if (sourceFile != ""):
            if (os.path.isfile(sourceFile)):
                self.load(sourceFile)
            else:
                print "Warning: Source file '%s' not found" % sourceFile
        elif (self.savePath != ""):
            # look for a .shasum.bz2 first, then a .shasum
            if (os.path.isfile('.'.join([self.savePath, bz2ext]))):
                # load() saves the new path
                self.load('.'.join([self.savePath, bz2ext]))
            elif (os.path.isfile(self.savePath)):
                self.load()
            else:
                self.build(excludePattern=excludePattern)
                self.save()

    def __len__(self):
        """Returns the number of files, including duplicates"""
        #return (len(self.hashDict))
        # should be equal to sum(map(len, self.hashDict))
        return (len(self.reverseDict))

    def __repr__(self):
        """Represent as string, format conforms to 'shasum' output"""
        repr_str = ""
        for key, val in self.hashDict.items():
            for path in val:
                repr_str += base64.b16encode(key).lower() + shaFieldSep + path + "\n"

        return(repr_str)

    def _addFile(self, fileHash, filePath):
        """Internal: Add a file and hash to the appropriate data structures"""
        if (filePath.startswith(self.rootPath)):
            filePath = os.path.relpath(filePath, self.rootPath)

        if (filePath in self.reverseDict):
            raise NameError('Path \'%s\' already exists?' % filePath)

        if (fileHash not in self.hashDict):
            # map the binary hash (digest) to the file path
            self.hashDict[fileHash] = [filePath]
        else:
            # Duplicate file found
            # This hash is already associated with a list
            self.hashDict[fileHash].append( filePath )
        # also map the path to the hash
        self.reverseDict[filePath] = fileHash

    def _delFile(self, filePath):
        """Internal: Delete a file and hash from the appropriate data structures"""
        #print len(self.reverseDict),
        fileHash=self.reverseDict[filePath]
        del self.reverseDict[filePath]
        #print len(self.reverseDict),

        index = self.hashDict[fileHash].index(filePath)
        #print len(self.hashDict[fileHash]),
        del self.hashDict[fileHash][index]
        #print len(self.hashDict[fileHash]),
        # If hashDict file list is empty
        if (not self.hashDict[fileHash]):
            # remove it from the map
            #print len(self.hashDict),
            del self.hashDict[fileHash]
            #print len(self.hashDict),
        #print ""
        return self

    def findByPattern(self, pattern, action=False, options=re.IGNORECASE):
        fileMatcher = re.compile(pattern,options)
        matchCount = 0
        for filePath, fileHash in self.reverseDict.items():
            if (fileMatcher.match(filePath)):
                print "'%s' matches" % filePath
                matchCount += 1
                if (action == "delete"):
                    self._delFile(filePath)

        print "Found %d matches" % matchCount

    def findByPath (self, searchPath):
        """Find the hash of a file based on its path"""
        if (searchPath.startswith(self.rootPath)):
            searchPath = os.path.relpath(searchPath, self.rootPath)
        #print searchPath
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

    def shortenPaths(self, longPath=False, shortPath="", act=True):
        if (not longPath):
            longPath = self.rootPath + '/'

        print "Replacing '%s' with '%s'" % (longPath, shortPath)

        for path, key in self.reverseDict.items():
            if (not path.startswith(longPath)):
                raise NameError ("This was meant to be used to shorten the beginning of the path")
            newPath = path.replace(longPath, shortPath)
            if (act):
                self._delFile(path)
                self._addFile(key, newPath)
            else:
                print newPath

    def update(self):
        self.removeMissing()
        self.addNew()
        self.save()

    def check(self):
        """Verify all the hashes"""

        pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(self))
        success = True

        pbar.start()
        for path, key in self.reverseDict.items():
            mypath = os.path.join(self.rootPath, path)
            if (not os.path.exists(mypath)):
                print "Not found: '%s'" % mypath
                success = False
                continue
            if (os.path.islink(mypath)):
                myhash = hashlib.sha512(os.readlink(mypath))
            else:
                myhash = hashChunkFile(hashlib.sha512, mypath)
            if (key != myhash.digest()):
                print "Checksum failed: '%s': '%s' != '%s'" % (mypath, base64.b16encode(key).lower(), myhash.hexdigest())
                success = False
            pbar.increment()
        pbar.finish()
        return success




    # TODO change to "build" and have separate "add missing"
    def build(self, includePattern=False, excludePattern=False, expand=False, verbose=False):
        """Build a hash dict object for files in a path"""

        print "Determining directory size..."
        dirSize = getDirSize(self.rootPath)
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=dirSize)

        if expand:
            print "Only checking for new files in existing hash map with %d files" % len(self)
        else:
            print "Building new hash map"
        #if (includePattern):
            #includeMatcher = re.compile(includePattern, re.IGNORECASE)
        if (excludePattern):
            excludeMatcher = re.compile(excludePattern, re.IGNORECASE)


        pbar.start()
        #pnum = pden = 0
        for root, dirs, files in os.walk(self.rootPath):
            if (excludePattern and excludeMatcher.match(root)):
                continue
            #pden += len(files)
            for filename in files:
                # might check for a specific time to have elapsed
                #pbar.update(pnum, pden)
                #print "%d %d" % (pnum, pden)
                #pnum += 1
                #if (includePattern and (not includeMatcher.match(filename))):
                    #continue
                #if (excludePattern and excludeMatcher.match(filename)):
                    #continue

                mypath = os.path.join(root, filename)
                if not os.path.isfile(mypath):
                    continue

                try:
                    pbar.increment(os.path.getsize(mypath))

                    # If we are expanding and this path is anywhere in the dictionary,
                    # do not update the hash
                    if (expand and self.findByPath(mypath)):
                        continue

                    # Open the file and compute the hash
                    if (os.path.islink(mypath)):
                        myhash = hashlib.sha512(os.readlink(mypath))
                    else:
                        myhash = hashChunkFile(hashlib.sha512, mypath)
                        #f = open (mypath, 'r')
                        #myhash = hashlib.sha512(f.read())
                        #f.close()
                    #print myhash.hexdigest() + "  \"" + mypath + "\""

                    self._addFile(myhash.digest(), mypath)

                    if (verbose):
                        print myhash.hexdigest() + shaFieldSep + repr(self.hashDict[myhash.digest()])
                except (IOError, OSError) as error:
                    print str(error) + ", skipping"
                except AssertionError as error:
                    #print str(error), os.path.getsize(mypath)
                    "Ignore"

        pbar.finish()
        print "Ended with %d files, %d unique hashes" % (len(self.reverseDict), len(self.hashDict))

    def removeMissing(self):
        """Remove files referenced in the data structures that are missing on filesystem"""
        initNum = len(self.reverseDict)
        for path, key in self.reverseDict.items():
            if (not os.path.exists(os.path.join(self.rootPath, path))):
                print "'%s' is missing" % (path)
                #remove the path from the list of paths
                self._delFile(path)
        print "Removed %d missing files" % (initNum - len(self.reverseDict))

    def addNew(self, includePattern=False, verbose=False):
        """Add files on filesystem that are missing in data structures"""
        self.build(includePattern=includePattern, expand=True, verbose=verbose)

    def load(self, filePath=None):
        global bz2ext
        """Load hashes from file"""
        if (filePath != None):
            self.savePath = filePath
        print "Loading file '%s'," % self.savePath,
        sys.stdout.flush()

        if (self.savePath.endswith(bz2ext)):
            import bz2
            f = bz2.BZ2File(self.savePath, 'r')
        else:
            f = open(self.savePath, 'r')

        for line in f.readlines():
            line = line.rstrip()

            (lineHash, mypath) = line.split('  ', 1)

            try:
                myhash = base64.b16decode(lineHash.upper())
            except TypeError as myError:
                print line
                print myError

            try:
                self._addFile(myhash, mypath)
            except NameError as e:
                print e
                # ignore this entry in the input

        f.close()
        print "%d files" % len(self)


    def save(self, filePath=None, compress=True):
        global bz2ext
        """Save hashes to file"""
        if (filePath != None):
            self.savePath = filePath
        if (compress and not self.savePath.endswith(bz2ext)):
            self.savePath = '.'.join([self.savePath, bz2ext])

        if (os.path.isfile(self.savePath)):
            fileBaseName = os.path.basename(self.rootPath)
            fileExtension = sha512ext
            if (compress or self.savePath.endswith(bz2ext)):
                fileExtension += '.'+bz2ext
            backupPath = os.path.join(os.path.dirname(self.savePath),
                    '.'+fileBaseName+
                    '-'+("%d" % os.stat(self.savePath).st_mtime)+
                    '.'+fileExtension)
            print "Backing up existing file to '%s'" % backupPath
            shutil.copy2(self.savePath, backupPath)

        print "Writing file '%s'" % self.savePath

        if (self.savePath.endswith(bz2ext)):
            import bz2
            f = bz2.BZ2File(self.savePath, 'w')
        else:
            f = open(self.savePath, 'w')

        f.write(str(self))

        f.close()

    def buildAndSave (self, variableName):
        global sha512ext

        self.update (self.rootPath)
        sha512filename = ".".join(["hashpatch", variableName, sha512ext])
        self.save(sha512filename)
        #pickleFilename = "hashpatch." + variableName + ".pickle"
        #pickleFile = open(pickleFilename, "w")
        #pickle.dump(hashDict, pickleFile)
        #pickleFile.close()


    def makeDupTable (self, minSize=1024):
        """List duplicate files, in groups"""
        dupList = []
        for key, val in self.hashDict.items():
            if (os.path.getsize(val[0]) < minSize):
                continue
            if (len(val) > 1):
                dupList.append([key, val, os.path.getsize(val[0])])
        return dupList

    def makeSubset(self, subdir):
        newMap = hashMap()
        newMap.rootPath = self.rootPath
        for path, key in self.reverseDict.items():
            if (path.startswith(subdir)):
                newMap._addFile(fileHash=key, filePath=path)
        return newMap



################################################################################
# Utility functions

def printDupTable(DupTable, sortKey=2):
    groupID = 1
    for [key, paths, size] in sorted(DupTable, key=lambda record: record[sortKey]):
        print "Group %d (%d b):" % (groupID, size)
        print base64.b16encode(key).lower()
        for path in paths:
            print "%s" % path
            if (os.path.getsize(path) != size):
                print "Files not all the same size: %d" % os.path.getsize(path)
                #raise NameError ("Something wrong with hash algorithm: files not all the same size")
        groupID += 1
        print ""

def showUnequalFiles(DupTable):
    for [key, paths, size] in DupTable:
        for path in paths:
            if (os.path.getsize(path) != size):
                print "Key: " + base64.b16encode(key).lower() + "\nSizes:"
                for x in paths:
                    print "%d %s" % (os.path.getsize(x), x)
                break

def openOrBuildHashDict (variableName, searchPath):
    global sha512ext

    sourceFilename = '.'.join(["hashpatch", variableName, sha512ext])

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



def checkForMissingInDest(sourceHashDict, destHashDict, dry_run=False, act=True, exclude="", collision_ext = ".remote", destSubDir=""):

    foundMissing = []

    #rf = open('hashpatch.report', 'w')

    for key, val in sourceHashDict.hashDict.items():
        if ((exclude != "") and (exclude in val[0])):
            continue
        if (key not in destHashDict.hashDict):
            foundMissing.append(key)
            #rf.write(base64.b16encode(key) + shaFieldSep + str(val) + "\n")

            if dry_run or act:
                # val[0] gets the first one if there are more than one copy of the file
                #pathParts = os.path.dirname(val[0]).split('/')
                #popped = pathParts.pop(0) # delete the first dir
                #print popped
                #if (popped != sourceHashDict.rootPath):
                #       raise NameError ("Not yet supported")
                #pathParts.insert(0, destHashDict.rootPath) # put the dest dir in front
                sourcePath = os.path.join(sourceHashDict.rootPath, val[0])
                destPath = os.path.join(destHashDict.rootPath, destSubDir, val[0])

                print "Copying '%s' -> '%s'" % (sourcePath, destPath)

                ext = ''
                if os.path.exists(destPath):
                    ext = collision_ext
                    print "WARNING: Destination already exists! Renaming source to '%s'" % (destPath + ext)
                    if (os.path.isfile(destPath+ext)):
                        raise NameError ('Collision resolution failed')

                if act:
                    if (not os.path.exists(os.path.dirname(destPath))):
                        os.makedirs(os.path.dirname(destPath))

                    shutil.copy2(sourcePath, destPath+ext)
            else:
                print base64.b16encode(key) + " does not exist in destination"
                print "Files (%d):" % len(val)
                for file in val:
                    print "\t" + file

    print "%s %d missing files in destination" % ("Copied" if act else "Found", len(foundMissing))
    #rf.close()
    return foundMissing

def deleteDupsInDest (sourceMap, destMap, act=False, prompt=False, verbose=False):
    foundDup = 0
    foundSize = 0

    #rf = open('hashpatch.report', 'a')

    for key, val in destMap.hashDict.items():
        if (key in sourceMap.hashDict):

            for path in val:
                path = os.path.join(destMap.rootPath, path)
                if (os.path.getsize(path) == 0):
                    # If it's an empty file?
                    continue
                foundDup += 1
                foundSize += os.path.getsize(path)
                print "%s duplicate of '%s' at '%s' (%s)" % ("Removing" if act else "Found", sourceMap.hashDict[key][0], path, progressbar.humanize_bytes(os.path.getsize(path)))
                if (verbose):
                    print "Matches: " + str(sourceMap.hashDict[key])
                if act:
                    if (prompt):
                        print "OK? ",
                    if (not prompt or sys.stdin.readline().lower().startswith('y')):
                        os.remove(path)
                        # delete the parent directory if it is empty
                        if (not os.listdir(os.path.dirname(path))):
                            # This is a function that recursively removes empty directories
                            os.removedirs(os.path.dirname(path))

    print "%s %d duplicate files (%s) in destination" % ("Deleted" if act else "Found", foundDup, progressbar.humanize_bytes(foundSize))
    #rf.close()

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


import datetime
def sortByYearModified (path, excludePattern=False):
    yearMap = dict()
    if (excludePattern):
        fileMatcher = re.compile(excludePattern, re.IGNORECASE)

    for root, dirs, files in os.walk(path):
        if (excludePattern and fileMatcher.match(root)):
            continue
        for filename in files:
            mypath = os.path.join(root, filename)
            year = datetime.date.fromtimestamp(os.stat(mypath).st_mtime).year
            if (year not in yearMap):
                yearMap[year] = [mypath]
            else:
                yearMap[year].append(mypath)

    return yearMap



def moveFileToArchive(filePath, archiveRoot, act=False):
    year = datetime.date.fromtimestamp(os.stat(filePath).st_mtime).year
    destPath = os.path.join(archiveRoot, str(year), os.path.basename(filePath))
    if (not os.path.exists(destPath)):
        print "Moving " + filePath + " -> " + destPath
        if (act):
            if (not os.path.isdir(os.path.dirname(destPath))):
                os.makedirs(os.path.dirname(destPath))
            shutil.move(filePath, destPath)
    else:
        print "File " + destPath + " already exists."

def makeMissingReport(BackupBasename, BackupMap, MissingFiles):
    for key in MissingFiles:
        numExist = 0
        for path in BackupMap.hashDict[key]:
            if (os.path.isfile(path.replace(BackupBasename, ""))):
                numExist += 1
        #if numExist > 0:
            #print "OK, %d files still exist" % numExist
        #else:
        if numExist == 0:
            print base64.b16encode(key) + ":"
            print BackupMap.hashDict[key][0]
            print "FAIL, all files with that checksum are missing"
        else:
            print "OK: " + BackupMap.hashDict[key][0] + ((" and %d others" % numExist) if numExist >1 else "")

class dupeRecord:
    def __init__(self, key, fileSize, numDupes):
        self.key = key
        self.fileSize = fileSize
        self.numDupes = numDupes

    def __str__(self):
        return " ".join([self.key, self.fileSize, self.numDupes])


def findDupes(HashMap, dupesOnly=True):
    "An interactive routine similar to 'dupseek.pl' which implements a greedy algorithm, pointing out the duplicate groups using the most space. "
    # need to sort by size multiplied by number of duplicates
    print "Calculating file sizes..."
    spaceHogs = []
    for key, paths in HashMap.hashDict.items():
        try:
            size = os.path.getsize(paths[0])
            spaceHogs.append( dupeRecord(key=key, fileSize=size, numDupes=len(paths)) )
        except OSError:
            print "File '%s' is missing" % paths[0]
            HashMap._delFile(paths[0])
            continue
    spaceHogs = sorted(spaceHogs, key=lambda record: record.numDupes * record.fileSize, reverse=True)

    for item in spaceHogs:
        if (dupesOnly and item.numDupes == 1):
            continue
        print " ".join([progressbar.humanize_bytes(item.numDupes*item.fileSize), str(item.numDupes), progressbar.humanize_bytes(item.fileSize), repr(HashMap.hashDict[item.key])])


        def checkResponseValid (response, numDupes):
            matches = re.match("(\S+)(\d+)", response)
            if (response == ""):
                return True
            if (not matches):
                return False
            if (response in ['q', '']):
                return True
            if (matches.group(1) in ['k', 'l'] \
                    and matches.group(2) in range(numDupes)):
                return False

            return True

        while(True):
            print "\n", \
                    "[return] to continue, [q] to quit\n", \
                    "[k0...k"+str(item.numDupes)+"] keep one file and remove the rest"
            # if system has symbolic links
            if ( True ):
                print "[l0...l"+str(item.numDupes)+"] keep one file and substitute the rest with symbolic links\n"

            response = sys.stdin.readline()
            if (checkResponseValid(response.strip(), item.numDupes)):
                print "Response not recognized"
                break

        #responseCodes = dict( zip( map(lambda x: "k%d" % x, range(item.numDupes)), ) )
                #sys.stdin.readline().lower().startswith('y')
