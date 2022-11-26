"""
Classes for associating one or more file paths to unique signatures
"""
import bz2
import hashlib
import logging
import base64
import os.path
from os.path import isfile, join
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from collections import defaultdict

BZ2_EXT_LIST = ['.bz2', '.bzip2']
SHA_FIELD_SEP = '  '


def is_bzip2(path):
    return os.path.splitext(path)[1] in BZ2_EXT_LIST


def hash_chunk_file(digest_fun, filename, chunk_size=4096):
    """
    Read a file in a series of chunks and compute an overall checksum.
    """
    with open(filename, mode='rb') as f_obj:
        d_obj = digest_fun()
        while True:
            buf = f_obj.read(chunk_size)
            d_obj.update(buf)
            if not buf:
                break
    return d_obj


class HashMapCore:
    """Associates one or more file paths with a unique signature
    regardless of how this information is stored"""
    def __init__(self, root_path, store_path=''):
        self.root_path = root_path
        self.store_path = store_path
        self.hash_func = hashlib.sha256
        self.max_threads = cpu_count()

    def get_save_name(self):
        return '.hashpatch'

    def get_save_ext(self):
        return ''

    def compute_file_hash(self, filepath):
        if os.path.islink(filepath):
            filehash = self.hash_func(os.readlink(filepath).encode('utf-8'))
        else:
            filehash = hash_chunk_file(self.hash_func, filepath)

        return filehash.digest(), filepath


class CheckFileHashMap(HashMapCore):
    """Associates one or more file paths with a unique signature
    using checksum text or bzip2 files for storage"""

    def __init__(self, root_path):
        super().__init__(root_path)
        self.hash_to_paths_dict = defaultdict(list)
        self.path_to_hash_dict = dict()
        self.save_path = self.get_save_path()
        self.dirty = False

    def __len__(self):
        """Returns the total number of files, including duplicates"""
        return len(self.path_to_hash_dict)

    def __str__(self):
        """Represent as string, format conforms to 'shasum' output"""
        repr_str = ''
        for key, val in self.hash_to_paths_dict.items():
            for path in val:
                repr_str += base64.b16encode(key).lower().decode('utf-8') \
                            + SHA_FIELD_SEP + path + '\n'

        return repr_str

    def __getitem__(self, raw_hash):
        return self.hash_to_paths_dict[raw_hash]

    def get_save_path(self):
        return join(self.root_path, self.get_save_name() + self.get_save_ext())

    def load(self):
        """Load a hash file if it exists and create one otherwise"""
        if isfile(self.save_path):
            self.__load_from_file()
        else:
            self.compute_hashes()

        logging.info('Loaded %d files; %d unique', len(self), len(self.hash_to_paths_dict))

    def add_file_hash(self, raw_digest, file_path):
        self.hash_to_paths_dict[raw_digest].append(file_path)
        self.path_to_hash_dict[file_path] = raw_digest

    def __load_from_file(self):
        """Load hashes from checksum file"""

        logging.info('Loading file "%s"', self.save_path)

        file_opener = bz2.BZ2File if is_bzip2(self.store_path) else open
        with file_opener(self.save_path, 'r') as hash_file:
            self.__load_file_lines(hash_file)

    def compute_hashes(self):
        logging.info('Computing hashes under directory "%s"', self.root_path)
        walker = DirectoryWalker(self.root_path)
        with Pool(self.max_threads) as pool:
            imap = pool.imap_unordered(self.compute_file_hash, walker.walk())
            pbar = tqdm(imap,
                        total=walker.count_files(),
                        unit=' files')
            for raw_hash, filepath in pbar:
                self.add_file_hash(raw_hash, filepath)

    def __load_file_lines(self, hash_file):
        line_num = 1
        for line in hash_file:
            line = line.rstrip()
            (line_hash, line_path) = line.split(SHA_FIELD_SEP, 1)
            raw_hash = base64.b16decode(line_hash.upper())
            self.add_file_hash(raw_hash, line_path)
            line_num += 1


class DirectoryWalker:
    def __init__(self, root_path):
        self.root_path = root_path

    def get_message(self):
        return f'Walking directory "{self.root_path}"'

    def is_excluded(self, filename, filepath):
        if not os.path.isfile(filepath):
            return True

        if filename.startswith('.hashpatch'):
            return True

        return False

    def walk(self):
        for root, dirnames, files in os.walk(self.root_path, topdown=True):
            dirnames[:] = [
                dir for dir in dirnames
                if not os.path.ismount(os.path.join(root, dir))]

            for filename in files:
                filepath = os.path.join(root, filename)
                if self.is_excluded(filename, filepath):
                    continue

                yield filepath

    def count_files(self):
        return len(list(self.walk()))

