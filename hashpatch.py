#!/usr/bin/python
# TODO store directory size in HashMap class. Maintain it through add and del
# operations

"""
HashPatch - this Python module is useful for computing checksums, deleting
duplicates, checking integrity and synchronizing directories.
"""

import re
import hashlib
import os
import sys
import base64
import shutil
import bz2
import datetime
import platform
import progressbar
from binascii import b2a_hex

SHA_FIELD_SEP = '  '
SHA512_EXT = 'sha512'
BZ2_EXT = 'bz2'

# http://stackoverflow.com/questions/7829499/
# using-hashlib-to-compute-md5-digest-of-a-file-in-python3
def hash_chunk_file(digest_fun, filename, chunk_size=4096):
    """
    Read a file in a series of chunks and compute an overall checksum.
    """
    with open(filename, mode='r') as f_obj:
        d_obj = digest_fun()
        while True:
            buf = f_obj.read(chunk_size)
            d_obj.update(buf)
            if not buf:
                break
    return d_obj

def get_dir_size(path):
    """Recursively compute the size of a directory."""
    dir_size = 0
    for root, _, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath):
                try:
                    dir_size += os.path.getsize(filepath)
                except OSError:
                    pass # this is just an estimation
    return dir_size

def format_hash(hash_str, trunc_len=8):
    return b2a_hex(hash_str)[:trunc_len]

def check_resp_valid(response, num_dupes):
    """
    Check if a user response is valid
    """
    matches = re.match(r'(\S+)(\d+)', response)
    if response == '':
        return True
    if not matches:
        return False
    if response in ['q', '']:
        return True
    if matches.group(1) in ['k', 'l'] \
            and matches.group(2) in range(num_dupes):
        return False

    return True



class DupeRecord(object):
    """
    A collection of data about a duplicate file
    """
    def __init__(self, key, file_size, num_dupes):
        self.key = key
        self.file_size = file_size
        self.num_dupes = num_dupes

    def __str__(self):
        return ' '.join([format_hash(self.key), self.file_size, self.num_dupes])



class HashMap(object):
    """
    HashMap builds a dictionary mapping file hashes to lists of file paths in a
    directory.  This mapping is saved in a compatible compressed text format,
    by default, to the root of the directory. If this file exists, it is loaded
    to recreate the dictionary from a previous process.

    This is useful for various operations such as merging or syncrhonizing
    directories.
    """

    # Variables declared here are class-static
    widgets = ['Progress: ',
               progressbar.Bar(marker='=', left='[', right=']'), ' ',
               progressbar.Fraction(), ' ',
               progressbar.Percentage(), ' ', progressbar.ETA()]

    def __init__(self, root_path='', sourceFile='', exclude_pattern=r'.*\.svn.*'):
        self.root_path = ''
        self.hash_dict = dict()
        self.reverse_dict = dict()
        self.save_path = ''

        if root_path != '':
            root_path = os.path.expanduser(root_path)
            if os.path.isdir(root_path):
                self.root_path = root_path.rstrip('/')
                self.save_path = os.path.join(self.root_path,
                                              '.hashpatch.'+SHA512_EXT)
                    #'.'.join([os.path.basename(self.root_path), int(time.time()), SHA512_EXT]))
            else:
                raise NameError('Root path given is not a directory')

        if sourceFile != '':
            if os.path.isfile(sourceFile):
                self.load(sourceFile)
            else:
                print 'Warning: Source file "%s" not found' % sourceFile
        elif self.save_path != '':
            # look for a .shasum.bz2 first, then a .shasum
            if os.path.isfile('.'.join([self.save_path, BZ2_EXT])):
                # load() saves the new path
                self.load('.'.join([self.save_path, BZ2_EXT]))
            elif os.path.isfile(self.save_path):
                self.load()
            else:
                print 'No file at "%s"' % self.save_path
                self.build(exclude_pattern=exclude_pattern)
                self.save()

    def __len__(self):
        """Returns the total number of files, including duplicates"""
        # should be equal to sum(map(len, self.hash_dict))
        return len(self.reverse_dict)

    def __repr__(self):
        """Represent as string, format conforms to 'shasum' output"""
        repr_str = ''
        for key, val in self.hash_dict.items():
            for path in val:
                repr_str += base64.b16encode(key).lower() + SHA_FIELD_SEP + path + '\n'

        return repr_str

    def add_file_hash(self, file_hash, file_path):
        """Internal: Add a file and hash to the appropriate data structures"""
        if file_path.startswith(self.root_path):
            file_path = os.path.relpath(file_path, self.root_path)

        if file_path in self.reverse_dict:
            raise NameError('Path \'%s\' already exists?' % file_path)

        if file_hash not in self.hash_dict:
            # map the binary hash (digest) to the file path
            self.hash_dict[file_hash] = [file_path]
        else:
            # Duplicate file found
            # This hash is already associated with a list
            self.hash_dict[file_hash].append(file_path)
        # also map the path to the hash
        self.reverse_dict[file_path] = file_hash

    def del_file_hash(self, file_path):
        """Internal: Delete a file and hash from the appropriate data structures"""
        #print len(self.reverse_dict),
        file_hash = self.reverse_dict[file_path]
        del self.reverse_dict[file_path]
        #print len(self.reverse_dict),

        index = self.hash_dict[file_hash].index(file_path)
        #print len(self.hash_dict[file_hash]),
        del self.hash_dict[file_hash][index]
        #print len(self.hash_dict[file_hash]),
        # If hash_dict file list is empty
        if not self.hash_dict[file_hash]:
            # remove it from the map
            #print len(self.hash_dict),
            del self.hash_dict[file_hash]
            #print len(self.hash_dict),
        #print ''
        return self

    def find_by_pattern(self, pattern, action=False, options=re.IGNORECASE):
        """File file paths using a pattern."""
        file_matcher = re.compile(pattern, options)
        match_count = 0
        for file_path in self.reverse_dict:
            if file_matcher.match(file_path):
                print '"%s" matches' % file_path
                match_count += 1
                if action == 'delete':
                    self.del_file_hash(file_path)

        print 'Found %d matches' % match_count

    def find_by_path(self, search_path):
        """Find the hash of a file based on its path"""
        if search_path.startswith(self.root_path):
            search_path = os.path.relpath(search_path, self.root_path)
        #print search_path
        if search_path not in self.reverse_dict:
            return False
        return self.reverse_dict[search_path]

    def shorten_paths(self, long_path=False, short_path='', act=True):
        """Useful for removing top-level parts of file paths"""
        if not long_path:
            long_path = self.root_path + '/'

        print 'Replacing "%s" with "%s"' % (long_path, short_path)

        for path, key in self.reverse_dict.items():
            if not path.startswith(long_path):
                raise NameError('This was meant to be used to shorten '
                                'the beginning of the path')
            new_path = path.replace(long_path, short_path)
            if act:
                self.del_file_hash(path)
                self.add_file_hash(key, new_path)
            else:
                print new_path

    def update(self):
        """
        Remove missing files, add new files that are not in the map and save the
        changes.
        """

        self.remove_missing()
        self.add_missing()
        self.save()

    def check(self):
        """Verify all the hashes"""

        pbar = progressbar.ProgressBar(widgets=self.widgets, maxval=len(self))
        success = True

        pbar.start()
        for path, key in self.reverse_dict.items():
            mypath = os.path.join(self.root_path, path)
            if not os.path.exists(mypath):
                print 'Not found: "%s"' % mypath
                success = False
                continue
            if os.path.islink(mypath):
                myhash = hashlib.sha512(os.readlink(mypath))
            else:
                myhash = hash_chunk_file(hashlib.sha512, mypath)
            if key != myhash.digest():
                print 'Checksum failed: "%s": "%s" != "%s"' % (
                    mypath, base64.b16encode(key).lower(), myhash.hexdigest())
                success = False
            pbar.increment()
        pbar.finish()
        return success

    def build(self, include_pattern=False, exclude_pattern=False, expand=False, verbose=False):
        """Build a hash dict object for files in a path"""

        print 'Determining directory size...'
# TODO add a dict that maps paths to sizes to this class and a method that
# populates this dict
        dir_size = get_dir_size(self.root_path)
        pbar = progressbar.ProgressBar(widgets=self.widgets, maxval=dir_size)

        if expand:
            print 'Only checking for new files in existing hash map with %d files' % len(self)
        else:
            print 'Building new hash map'
        if include_pattern:
            include_matcher = re.compile(include_pattern, re.IGNORECASE)
        if exclude_pattern:
            exclude_matcher = re.compile(exclude_pattern, re.IGNORECASE)


        pbar.start()
        #pnum = pden = 0
        for root, _, files in os.walk(self.root_path):
            if include_pattern and not include_matcher.match(root):
                continue
            if exclude_pattern and exclude_matcher.match(root):
                continue
            #pden += len(files)
            for filename in files:
                # might check for a specific time to have elapsed
                #pbar.update(pnum, pden)
                #print '%d %d' % (pnum, pden)
                #pnum += 1
                #if include_pattern and (not includeMatcher.match(filename)):
                    #continue
                #if exclude_pattern and exclude_matcher.match(filename):
                    #continue

                mypath = os.path.join(root, filename)
                # Skip if this path is a directory or special file
                if not os.path.isfile(mypath):
                    continue

                # Don't include hashpatch files
                if filename.startswith('.hashpatch'):
                    continue

                try:
                    pbar.increment(os.path.getsize(mypath))

                    # If we are expanding and this path is anywhere in the dictionary,
                    # do not update the hash
                    if expand and self.find_by_path(mypath):
                        continue

                    # Open the file and compute the hash
                    if os.path.islink(mypath):
                        myhash = hashlib.sha512(os.readlink(mypath))
                    else:
                        myhash = hash_chunk_file(hashlib.sha512, mypath)
                        #f = open (mypath, 'r')
                        #myhash = hashlib.sha512(f.read())
                        #f.close()
                    #print myhash.hexdigest() + '  "' + mypath + '"'

                    self.add_file_hash(myhash.digest(), mypath)

                    if verbose:
                        print myhash.hexdigest() + SHA_FIELD_SEP + \
                            repr(self.hash_dict[myhash.digest()])
                except (IOError, OSError) as error:
                    print str(error) + ', skipping'
                except AssertionError as error:
                    #print str(error), os.path.getsize(mypath)
                    pass

        pbar.finish()
        print 'Ended with %d files, %d unique hashes' % \
            (len(self.reverse_dict), len(self.hash_dict))

    def remove_missing(self):
        """Remove files referenced in the data structures that are missing on filesystem"""
        init_num = len(self.reverse_dict)
        for path in self.reverse_dict:
            if not os.path.exists(os.path.join(self.root_path, path)):
                print '"%s" is missing with %d other copies' % (
                    path,
                    len(self.hash_dict[self.reverse_dict[path]])-1)
                #remove the path from the list of paths
                self.del_file_hash(path)
        print 'Removed %d missing files' % (init_num - len(self.reverse_dict))

    def add_missing(self, include_pattern=False, verbose=False):
        """Add files on filesystem that are missing in data structures"""
        self.build(include_pattern=include_pattern, expand=True, verbose=verbose)

    def load(self, file_path=None):
        """Load hashes from file"""

        if file_path != None:
            self.save_path = file_path
        print 'Loading file "%s",' % self.save_path,
        sys.stdout.flush()

        if self.save_path.endswith(BZ2_EXT):
            bz_file = bz2.BZ2File(self.save_path, 'r')
        else:
            bz_file = open(self.save_path, 'r')

        for line in bz_file.readlines():
            line = line.rstrip()

            (line_hash, mypath) = line.split('  ', 1)

            try:
                myhash = base64.b16decode(line_hash.upper())
            except TypeError as err:
                print line
                print err

            try:
                self.add_file_hash(myhash, mypath)
            except NameError as err:
                print err
                # ignore this entry in the input

        bz_file.close()
        print '%d files' % len(self)

# TODO implement dirty bit. Set when any change is made. Reset on save.
    def save(self, file_path=None, compress=True):
        """Save hashes to file"""
        if file_path != None:
            self.save_path = file_path
        if compress and not self.save_path.endswith(BZ2_EXT):
            self.save_path = '.'.join([self.save_path, BZ2_EXT])

        if os.path.isfile(self.save_path):
            file_extension = SHA512_EXT
            if compress or self.save_path.endswith(BZ2_EXT):
                file_extension += '.'+BZ2_EXT
            backup_path = os.path.join(
                os.path.dirname(self.save_path),
                '.hashpatch-'+('%d' % os.stat(self.save_path).st_mtime)+
                '.'+file_extension)
            print 'Backing up existing file to "%s"' % backup_path
            shutil.copy2(self.save_path, backup_path)

        print 'Writing file "%s"' % self.save_path

        if self.save_path.endswith(BZ2_EXT):
            bzf = bz2.BZ2File(self.save_path, 'w')
        else:
            bzf = open(self.save_path, 'w')

        bzf.write(str(self))
        bzf.close()

    def make_dup_table(self, min_size=1024):
        """List duplicate files, in groups"""
        dup_list = []
        for key, val in self.hash_dict.items():
            if os.path.getsize(val[0]) < min_size:
                continue
            if len(val) > 1:
                dup_list.append([key, val, os.path.getsize(val[0])])
        return dup_list

    def make_subset(self, subdir):
        """
        Return a new HashMap that is a subset of this with only files under the
        specified path.
        """
        sub = HashMap()
        sub.root_path = self.root_path
        for path, key in self.reverse_dict.items():
            if path.startswith(subdir):
                sub.add_file_hash(file_hash=key, file_path=path)
        return sub

    def delete_dupes_starting_with(self, prefix):
        """
        Delete duplicates in this HashMap beginning with the specified prefix.
        """
        for val in self.hash_dict.values():
            if len(val) > 1:
                for path in val:
                    if path.startswith(prefix):
                        assert sum([s.startswith(prefix) for s in val]) == 1
                        print 'rm %s' % path
                        os.unlink(os.path.join(self.root_path, path))
                        self.del_file_hash(path)

    def find_dupes(self, dupes_only=True):
        """
        An interactive routine similar to 'dupseek.pl' which implements a
        greedy algorithm, pointing out the duplicate groups using the most
        space.
        """
        # need to sort by size multiplied by number of duplicates
        print 'Calculating file sizes...'
        space_hogs = []
        for key, paths in self.hash_dict.items():
            try:
                size = os.path.getsize(paths[0])
                space_hogs.append(
                    DupeRecord(key=key, file_size=size, num_dupes=len(paths)))
            except OSError:
                print 'File "%s" is missing' % paths[0]
                self.del_file_hash(paths[0])
                continue
        space_hogs = sorted(
            space_hogs,
            key=lambda record: record.num_dupes * record.file_size,
            reverse=True)

        for item in space_hogs:
            if dupes_only and item.num_dupes == 1:
                continue
            print ' '.join([
                progressbar.humanize_bytes(item.num_dupes*item.file_size),
                str(item.num_dupes),
                progressbar.humanize_bytes(item.file_size),
                repr(self.hash_dict[item.key])])


            while True:
                print '\n', \
                        '[return] to continue, [q] to quit\n', \
                        '[k0...k'+str(item.num_dupes)+'] '\
                        'keep one file and remove the rest'
                # if system has symbolic links
                if platform.system() != 'Windows':
                    print '[l0...l'+str(item.num_dupes)+'] '\
                        'keep one file and substitute the rest with '\
                        'symbolic links\n'

                response = sys.stdin.readline()
                if check_resp_valid(response.strip(), item.num_dupes):
                    print 'Response not recognized'
                    break

            #responseCodes = dict( zip( map(lambda x: 'k%d' % x, range(item.num_dupes)), ) )
                    #sys.stdin.readline().lower().startswith('y')

################################################################################
# Utility functions

def print_dup_table(dup_table, sort_key=2):
    """
    Print a table of duplicate file groups in a duplicate table
    """
    group_id = 1
    for [key, paths, size] in sorted(dup_table, key=lambda record: record[sort_key]):
        print 'Group %d (%d b):' % (group_id, size)
        print base64.b16encode(key).lower()
        for path in paths:
            print '%s' % path
            if os.path.getsize(path) != size:
                print 'Files not all the same size: %d' % os.path.getsize(path)
        group_id += 1
        print ''

# TODO replace this function
def show_unequal_files(dup_table):
    """
    Print a list of files and sizes in a duplicate table
    """
    for [key, paths, size] in dup_table:
        for path in paths:
            if os.path.getsize(path) != size:
                print 'Key: ' + base64.b16encode(key).lower() + '\nSizes:'
                for thispath in paths:
                    print '%d %s' % (os.path.getsize(thispath), thispath)
                break

def check_for_missing_in_dest(
        source, dest, act=True,
        exclude='', collision_ext='.remote', dest_subdir=''):
    """
    Copy files from source that are missing in dest
    """

    found_missing = []

    for key, path_list in source.hash_dict.items():
        if exclude and (exclude in path_list[0]):
            continue
        if key not in dest.hash_dict:
            found_missing.append(key)

            if act:
                # path_list[0] gets the first one if there are more than one copy of the file
                #pathParts = os.path.dirname(path_list[0]).split('/')
                #popped = pathParts.pop(0) # delete the first dir
                #print popped
                #if popped != source.root_path:
                #       raise NameError ('Not yet supported')
                #pathParts.insert(0, dest.root_path) # put the dest dir in front
                source_path = os.path.join(source.root_path, path_list[0])
                dest_path = os.path.join(dest.root_path, dest_subdir, path_list[0])

                print 'Copying "%s" -> "%s"' % (source_path, dest_path)

                ext = ''
                if os.path.exists(dest_path):
                    ext = collision_ext
                    print 'WARNING: Destination already exists! '\
                        'Renaming source to "%s"' % (dest_path + ext)
                    if os.path.isfile(dest_path+ext):
                        raise NameError('Collision resolution failed')

                if act:
                    if not os.path.exists(os.path.dirname(dest_path)):
                        os.makedirs(os.path.dirname(dest_path))

                    shutil.copy2(source_path, dest_path+ext)
            else:
                print base64.b16encode(key) + ' does not exist in destination'
                print 'Files (%d):' % len(path_list)
                for path in path_list:
                    print '\t' + path

    print '%s %d missing files in destination' % ('Copied' if act else 'Found', len(found_missing))
    return found_missing

def delete_dups_in_dest(source, dest, act=False, prompt=False,
                        verbose=False, min_size=None):
    """
    Delete files in dest HashMap that are duplicates of files in source
    HashMap.
    """
    found_dup = 0
    found_size = 0

    for key, path_list in dest.hash_dict.items():
        if key not in source.hash_dict:
            continue

        for rel_path in path_list:
            path = os.path.join(dest.root_path, rel_path)
            if not os.path.isfile(path):
                print '"%s" does not exist' % path
                continue
            if os.path.getsize(path) == 0:
                # If it's an empty file?
                continue
            if min_size and os.stat(path).st_size < min_size:
                continue
            found_dup += 1
            found_size += os.path.getsize(path)
            print '%s duplicate of "%s" at "%s" (%s)' % (
                'Removing' if act else 'Found',
                source.hash_dict[key][0],
                path,
                progressbar.humanize_bytes(os.path.getsize(path)))
            if verbose:
                print 'Matches: ' + str(source.hash_dict[key])
            if act:
                if prompt:
                    if not input('OK? ').lower().startswith('y'):
                        continue
                os.remove(path)
                # delete the parent directory if it is empty
                if not os.listdir(os.path.dirname(path)):
                    # recursively remove empty directories
                    os.removedirs(os.path.dirname(path))
                dest.del_file_hash(rel_path)

    print '%s %d duplicate files (%s) in destination' % (
        'Deleted' if act else 'Found',
        found_dup,
        progressbar.humanize_bytes(found_size))
    dest.save()

def delete_broken_links(path, act=False):
    """
    Delete files that are broken links
    """

    for root, _, files in os.walk(path):
        for filename in files:
            #print filename
            if os.path.islink(os.path.join(root, filename)):
                #print 'Link at %s/%s' % (root, filename)
                if not os.path.exists(os.path.join(root, filename)):
                    if act:
                        os.remove(os.path.join(root, filename))
                        if not os.listdir(root):
                            # This is a function that recursively removes empty directories
                            os.removedirs(root)
                    print '%s broken link at %s/%s' % (
                        'Deleted' if act else 'Found',
                        root,
                        filename)

def delete_empty_dirs(path, act=False):
    """
    Delete directories that are empty
    """

    for root, dirs, files in os.walk(path):
        #for dir in dirs:
        if not dirs and not files:
            # This is a function that recursively removes empty directories
            if act:
                os.removedirs(root)
            print '%s empty directory at %s' % ('Deleted' if act else 'Found', root)


def sort_by_year_modified(path, exclude_pattern=False):
    """
    Return a dictionary sorting the files in a directory by the year in which
    they were modified.
    """
    year_map = dict()
    if exclude_pattern:
        file_matcher = re.compile(exclude_pattern, re.IGNORECASE)

    for root, _, files in os.walk(path):
        if exclude_pattern and file_matcher.match(root):
            continue
        for filename in files:
            mypath = os.path.join(root, filename)
            year = datetime.date.fromtimestamp(os.stat(mypath).st_mtime).year
            if year not in year_map:
                year_map[year] = [mypath]
            else:
                year_map[year].append(mypath)

    return year_map



def move_file_to_archive(file_path, archive_root, act=False):
    """
    Move file to annual archive
    """
    year = datetime.date.fromtimestamp(os.stat(file_path).st_mtime).year
    dest_path = os.path.join(archive_root, str(year), os.path.basename(file_path))
    if not os.path.exists(dest_path):
        print 'Moving ' + file_path + ' -> ' + dest_path
        if act:
            if not os.path.isdir(os.path.dirname(dest_path)):
                os.makedirs(os.path.dirname(dest_path))
            shutil.move(file_path, dest_path)
    else:
        print 'File ' + dest_path + ' already exists.'

def make_missing_report(backup_basename, backup_map, missing_files):
    """
    Report missing files
    """
    for key in missing_files:
        num_exist = 0
        for path in backup_map.hash_dict[key]:
            if os.path.isfile(path.replace(backup_basename, '')):
                num_exist += 1
        #if num_exist > 0:
            #print 'OK, %d files still exist' % num_exist
        #else:
        if num_exist == 0:
            print base64.b16encode(key) + ':'
            print backup_map.hash_dict[key][0]
            print 'FAIL, all files with that checksum are missing'
        else:
            print 'OK: ' + backup_map.hash_dict[key][0] + \
                ((' and %d others' % num_exist) if num_exist > 1 else '')
