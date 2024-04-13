"""
Repository
"""
import os


def is_repository() -> bool:
	from .paths import (
		COMMITS_DIRECTORY,
		FILES_DIRECTORY,
		HUGE_DIRECTORY,
		REPO_ID_FILE,
	)

	return (
		os.path.isdir(COMMITS_DIRECTORY) and
		os.path.isdir(FILES_DIRECTORY) and
		os.path.isdir(HUGE_DIRECTORY) and
		os.path.isfile(REPO_ID_FILE)
	)


def create_repository() -> None:
	from .paths import (
		CURRENT_COMMIT_FILE,
		IGNORE_FILE,
		REPO_ID_FILE,
	)

	create_repository_structure(".")

	with open(CURRENT_COMMIT_FILE, "w"):
		pass

	with open(REPO_ID_FILE, "w") as f:
		f.write(create_hash())

	with open(IGNORE_FILE, "w") as f:
		f.write(
			"# Files that should be ignored.\n"
			"# Use regular expressions.\n"
			"# Examples:\n"
			"#   \\.dat$   <-- Ignore any paths that end with \".dat\"\n"
			"#   my_folder/ignore_this_file.txt$\n"
			"#   .*/ignore.txt$  <-- Ignore all paths ending with \"/ignore.txt\"\n"
			"#   top/.*  <-- Ignore top-level \"top\" folder\n"
			"\\.git/.*\n"
			".*\\.gitattributes$\n"
			".*\\.gitignore$\n"
			".*~$\n"
		)

def create_hash() -> str:
	import hashlib
	import uuid

	random_string = "".join(str(uuid.uuid4()) for _ in range(10)).encode("ascii")

	return hashlib.md5(random_string).hexdigest().lower()


def create_repository_structure(path: str) -> None:
	from .paths import (
		COMMITS_DIRECTORY,
		FILES_DIRECTORY,
		HUGE_DIRECTORY,
		REMOTES_FOLDER,
	)
	assert not os.path.exists(os.path.join(path, HUGE_DIRECTORY))

	os.mkdir(os.path.join(path, HUGE_DIRECTORY))
	os.mkdir(os.path.join(path, COMMITS_DIRECTORY))
	os.mkdir(os.path.join(path, FILES_DIRECTORY))
	os.mkdir(os.path.join(path, REMOTES_FOLDER))
