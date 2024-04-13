"""
Staging of files

For now, it is not staging, it is just the files that the user is working on.
"""
import os
import re
from dataclasses import dataclass


@dataclass
class FileStatus:
	new: bool
	changed: bool
	deleted: bool
	size: int
	new_size: int


@dataclass
class FileStageStatus:
	"""
	Status for a single file
	"""
	workspace: FileStatus
	stage: FileStatus


def get_workspace_files(
	commit_hash: str | None = None,
) -> tuple[dict[str, str], dict[str, str], set[str], dict[str, str]]:
	"""
	Compares the checked out files with the ones in the current active commit
	"""
	from huge.repo.commit import get_commit_files, get_current_commit

	new = {}
	changed = {}
	unchanged = {}

	if not commit_hash:
		commit_hash = get_current_commit()

	commit_files = commit_hash and get_commit_files(commit_hash) or {}
	staged_files = hash_workspace_files()

	for path, user_file_hash  in staged_files.items():
		assert not os.path.islink(path)

		commit_file_hash = commit_files.get(path)

		if commit_file_hash:  # Already exists in the active commit
			if user_file_hash != commit_file_hash:
				changed[path] = user_file_hash
			else:  # File is unchanged
				unchanged[path] = user_file_hash

		else:
			# File does not exist in commit
			new[path] = user_file_hash

	return (
		new,
		changed,
		set(commit_files) - set(staged_files),  # Deleted
		unchanged,
	)


def hash_workspace_files() -> dict[str, str]:
	"""
	Returns an hash of all the files in the user's directory

	Format: {"path": "hash sum"}
	"""
	import hashlib
	import subprocess
	import sys
	import time

	# Find all files, excluding .huge folder
	process = subprocess.Popen(
		[
			"find", ".",
			"-not", "-path", "*/.huge/*",
			"-type", "f",
		],
		stdout=subprocess.PIPE,
	)

	stdout, _ = process.communicate()

	assert process.returncode == 0

	# Read ignore-list, if any
	ignore = get_ignore_patterns()

	result: dict[str, str] = {}

	bytes_hashed = 0
	last_print = time.time() + .5
	printed = ""
	for file_count, x in enumerate(stdout.decode().splitlines()):
		path = os.path.normpath(x.strip())

		# Remove files that matches ignore-list
		if any(x.match(path) for x in ignore):
			continue

		md5sum = hashlib.md5()

		with open(x, "rb") as f:
			while 1:
				data = f.read(2**20)
				if not data:
					break

				md5sum.update(data)

				bytes_hashed += len(data)

				if last_print < time.time():
					last_print = time.time() + .1
					printed = f"\rHashing files: {int(bytes_hashed/2**20)} MB, {file_count} files"
					sys.stdout.write(printed)
					sys.stdout.flush()

		hash_sum = md5sum.hexdigest().lower()

		result[os.path.normpath(path)] = hash_sum

	if printed:
		sys.stdout.write(" " * len(printed) + "\r")

	return result


def mark_as_staged(paths: list[str]) -> None:
	"""
	Marks a file as staged for commit

	This is not the same as git's staging. We don't store the file in a staging
	area; we only mark it that it should be considered for committing.
	"""
	import subprocess
	from huge.repo.paths import STAGED_FILE

	# TODO merayen respect .hugeignore

	to_add = set()

	# First add direct paths
	for path in paths:
		if os.path.isfile(path):
			to_add.add(path)

	folder_paths = [("\\" + x) if x.startswith("-") else x for x in paths if os.path.isdir(x)]

	# Then add folders. They automatically expands to all the files
	if folder_paths:
		process = subprocess.Popen(["find"] + folder_paths + ["-type", "f"], stdout=subprocess.PIPE)
		stdout, _ = process.communicate()
		assert not process.returncode

		to_add.update(x.strip() for x in stdout.decode().splitlines())

	# Remove files that are hit by the .hugeignore file
	ignore_patterns: list[re.Pattern[str]] = get_ignore_patterns()

	for path in list(to_add):
		for ignore_pattern in ignore_patterns:
			if ignore_pattern.match(path):
				to_add.remove(path)
				break

	# Remove any stray empty path
	to_add.discard("")

	if to_add:
		with open(STAGED_FILE, "a") as f:
			f.write("\n".join(to_add) + "\n")


def unmark_as_staged(paths: list[str]) -> None:
	from huge.repo.paths import STAGED_FILE

	staged_files: set[str] = get_staged_files_2()

	for path in sorted(paths):
		path = os.path.normpath(path)

		if path == ".":
			staged_files = set()
			break

		staged_files = {x for x in staged_files if not x.startswith(path + os.path.sep) and x != path}

	staged_files.discard("")

	if staged_files:
		with open(STAGED_FILE, "w") as f:
			f.write("\n".join(sorted(staged_files)) + "\n")

	elif os.path.exists(STAGED_FILE):
		os.remove(STAGED_FILE)


def reset_staging() -> None:
	from huge.repo.paths import STAGED_FILE

	if os.path.exists(STAGED_FILE):
		os.remove(STAGED_FILE)


# TODO merayen rename to get_staged_files
def get_staged_files_2() -> set[str]:
	from huge.repo.paths import STAGED_FILE

	if os.path.exists(STAGED_FILE):
		with open(STAGED_FILE) as f:
			return {x.strip() for x in f if x.strip()}

	return set()


def get_ignore_patterns() -> list[re.Pattern[str]]:
	from huge.repo.paths import IGNORE_FILE

	if os.path.isfile(IGNORE_FILE):
		with open(IGNORE_FILE) as f:
			return [
				re.compile(x.strip())
				for x in (
					x
					for x in f
					if x.split("#", maxsplit=1)[0].strip()
				)
				if x
			]

	return []
