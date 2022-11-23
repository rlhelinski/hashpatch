import os
from unittest import TestCase, main
from tempfile import mkdtemp
from random import seed, randbytes
from binascii import b2a_hex
from shutil import rmtree
from os.path import join
import hashpatch


class RandomFileTest(TestCase):

    def setUp(self):
        """create files in a temporary directory, some duplicates"""
        self.num_files = 100
        self.num_dupes = 30
        self.rand_seed = 42
        self.file_size = 2**12
        seed(self.rand_seed)

        self.temp_dir = mkdtemp(prefix='hashmap')
        for i in range(self.num_files):
            with open(join(self.temp_dir, 'file'+b2a_hex(randbytes(10)).decode()), 'wb') as f:
                f.write(randbytes(self.file_size))

    def tearDown(self):
        """delete the files"""
        rmtree(self.temp_dir)


class DirectoryWalkerTest(RandomFileTest):
    def setUp(self):
        super().setUp()
        self.walker = hashpatch.DirectoryWalker(self.temp_dir)

    def test_size(self):
        result = list(self.walker.walk())
        self.assertEqual(len(result), self.num_files)


class DirectorySizeWalkerTest(RandomFileTest):
    def setUp(self):
        super().setUp()
        self.walker = hashpatch.DirectorySizeWalker(self.temp_dir)


class FileSystemTest(RandomFileTest):

    def setUp(self):
        super().setUp()

        self.map = hashpatch.CheckFileHashMap(self.temp_dir)
        self.map.load()

    def tearDown(self):
        super().tearDown()

    def test_build(self):
        """test building a hashmap"""
        #os.system(f'ls {self.temp_dir}')
        self.assertEqual(len(self.map), self.num_files)

    def test_consistency(self):
        self.assertEqual(len(self.map.path_to_hash_dict), sum(map(len, self.map.hash_to_paths_dict.values())))


if __name__ == '__main__':
    main()
