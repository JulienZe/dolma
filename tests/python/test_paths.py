import itertools
import os
from pathlib import Path
from unittest import TestCase

from dolma.core.paths import (
    _pathify,
    add_suffix,
    glob_path,
    make_relative,
    sub_prefix,
    sub_suffix,
)

LOCAL_DATA = Path(__file__).parent.parent / "data"


class TestPaths(TestCase):
    def test_pathify(self):
        path = "s3://path/to/file"
        protocol, path = _pathify(path)
        self.assertEqual(protocol, "s3")
        self.assertEqual(path, Path("path/to/file"))

        path = "path/to/file"
        protocol, path = _pathify(path)
        self.assertEqual(protocol, "")
        self.assertEqual(path, Path("path/to/file"))

        path = "/path/to/file"
        protocol, path = _pathify(path)
        self.assertEqual(protocol, "")
        self.assertEqual(path, Path("/path/to/file"))

    def test_local_glob_path(self):
        local_glob = str(LOCAL_DATA / "*.json.gz")
        paths = list(glob_path(local_glob))
        expected = [str(LOCAL_DATA / fn) for fn in os.listdir(LOCAL_DATA) if fn.endswith(".json.gz")]
        self.assertEqual(sorted(paths), sorted(expected))

    def test_remote_glob_path(self):
        prefix = "s3://ai2-llm/pretraining-data/tests/mixer/expected"
        paths = list(glob_path(f"{prefix}/*"))
        expected = [f"{prefix}/{fn}" for fn in os.listdir(LOCAL_DATA / "expected") if fn.endswith(".json.gz")]
        self.assertEqual(sorted(paths), sorted(expected))

    def test_local_glob_with_recursive(self):
        local_glob = str(LOCAL_DATA / "**/*-paragraphs.json.gz")
        paths = list(glob_path(local_glob))
        expected = list(
            itertools.chain.from_iterable(
                (str(fp),)
                if (fp := LOCAL_DATA / fn).is_file() and "paragraphs" in fn
                else ((str(fp / sn) for sn in os.listdir(fp) if "paragraphs" in sn) if fp.is_dir() else ())
                for fn in os.listdir(LOCAL_DATA)
            )
        )
        self.assertEqual(sorted(paths), sorted(expected))

    def test_sub_prefix(self):
        path_a = "s3://path/to/b/and/more"
        path_b = "s3://path/to/b"

        self.assertEqual(sub_prefix(path_a, path_b), "and/more")
        self.assertEqual(sub_prefix(path_b, path_a), path_b)

        path_c = "/path/to/c"
        path_d = "/path/to/c/and/more"

        self.assertEqual(sub_prefix(path_d, path_c), "and/more")
        self.assertEqual(sub_prefix(path_c, path_d), path_c)

        with self.assertRaises(ValueError):
            sub_prefix(path_a, path_c)

    def test_sub_suffix(self):
        path_a = "s3://path/to/dir/and/more"
        path_b = "and/more"
        self.assertEqual(sub_suffix(path_a, path_b), "s3://path/to/dir")

        path_c = "/path/to/dir/and/more"
        path_d = "path/to/dir/and/more"
        self.assertEqual(sub_suffix(path_c, path_d), "/")

    def test_add_prefix(self):
        path_a = "s3://path/to/b"
        path_b = "and/more"

        self.assertEqual(add_suffix(path_a, path_b), "s3://path/to/b/and/more")

        path_c = "/path/to/c"
        path_d = "and/more"

        self.assertEqual(add_suffix(path_c, path_d), "/path/to/c/and/more")

        with self.assertRaises(ValueError):
            add_suffix(path_a, path_c)
            add_suffix(path_c, path_a)
            add_suffix(path_a, path_a)

    def test_wildcard_operations(self):
        path_a = "s3://path/to/dir"
        self.assertEqual(add_suffix(path_a, "*"), "s3://path/to/dir/*")

        path_b = "/path/to/dir/**"
        self.assertEqual(add_suffix(path_b, "*"), "/path/to/dir/**/*")

        path_c = "s3://path/to/dir/**"
        self.assertEqual(sub_prefix(path_c, path_a), "**")

    def test_make_relative(self):
        paths = [
            "/path/to/dir/and/more",
            "/path/to/dir/and/**.zip",
            "/path/to/dir/more/**/stuff",
        ]
        base, relative_paths = make_relative(paths)
        self.assertEqual(base, "/path/to/dir")
        self.assertEqual(relative_paths, ["and/more", "and/**.zip", "more/**/stuff"])

        paths = [
            "/foo",
            "/bar/**",
            "/baz/**/**",
        ]
        base, relative_paths = make_relative(paths)
        self.assertEqual(base, "/")
        self.assertEqual(relative_paths, ["foo", "bar/**", "baz/**/**"])

        paths = [
            "s3://path/to/a/and/b",
            "s3://path/to/a/and/**.zip",
            "s3://path/to/b/more/**/stuff",
        ]

        base, relative_paths = make_relative(paths)
        self.assertEqual(base, "s3://path/to")
        self.assertEqual(relative_paths, ["a/and/b", "a/and/**.zip", "b/more/**/stuff"])

        paths = [
            "s3://path_a/to/dir/and/more",
            "s3://path_b/to/dir/and/**.zip",
            "s3://path_c/to/dir/more/**/stuff",
        ]

        base, relative_paths = make_relative(paths)
        self.assertEqual(base, "s3://")
        self.assertEqual(
            relative_paths,
            [
                "path_a/to/dir/and/more",
                "path_b/to/dir/and/**.zip",
                "path_c/to/dir/more/**/stuff",
            ],
        )
