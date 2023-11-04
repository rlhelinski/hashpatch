import os
import subprocess
from unittest import TestCase, main
from tempfile import mkdtemp
from random import seed, randbytes
from binascii import b2a_hex
from shutil import rmtree
from os.path import join
import hashpatch

equiv_cmds = {"openssl_sha256": "sha256sum"}


class RandomFileTest(TestCase):
    def setUp(self):
        """create files in a temporary directory, some duplicates"""
        self.num_files = 100
        self.num_dupes = 30
        self.rand_seed = 42
        self.file_size = 2**12
        seed(self.rand_seed)

        self.temp_dir = mkdtemp(prefix="hashmap")
        for i in range(self.num_files - 2):
            self.make_random_file(self.get_random_filename())

        link_target = self.get_random_filename()
        self.make_random_file(link_target)
        link_filename = join(self.temp_dir, self.get_random_filename("link"))
        os.symlink(link_target, link_filename, target_is_directory=False)

        link_target = self.get_random_filename()
        os.mkdir(join(self.temp_dir, link_target))
        link_filename = join(self.temp_dir, self.get_random_filename("link"))
        os.symlink(link_target, link_filename, target_is_directory=True)

    def make_random_file(self, filename):
        with open(join(self.temp_dir, filename), "wb") as f:
            f.write(randbytes(self.file_size))
        return filename

    def get_random_filename(self, prefix="file"):
        return prefix + b2a_hex(randbytes(10)).decode()

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


class FileSystemTest(RandomFileTest):
    def setUp(self):
        super().setUp()

        self.map = hashpatch.CheckFileHashMap(self.temp_dir)
        self.map.load()

    def tearDown(self):
        super().tearDown()

    def test_build(self):
        """test building a hashmap"""
        self.assertEqual(len(self.map), self.num_files)

    def test_consistency(self):
        self.assertEqual(
            len(self.map.path_to_hash_dict),
            sum(map(len, self.map.hash_to_paths_dict.values())),
        )

    def test_file_output(self):
        hashpatch_checkfile_output = str(self.map)
        hashpatch_checkfile_output = "\n".join(
            sorted(hashpatch_checkfile_output.split("\n"))
        )
        hashpatch_checkfile_output = hashpatch_checkfile_output.strip()
        equiv_cmd = f"find -L {self.temp_dir} -type f -print0 | xargs -0 {equiv_cmds[self.map.hash_type.hash_func.__name__]} | sort"
        equiv_cmd_output = subprocess.getoutput(equiv_cmd)
        self.assertEqual(hashpatch_checkfile_output, equiv_cmd_output)


if __name__ == "__main__":
    main()
