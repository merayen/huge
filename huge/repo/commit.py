"""
Commits in a repo
"""
import datetime
import os
from dataclasses import dataclass


def get_commit_hashes() -> list[str]:
	from huge.repo.paths import COMMITS_DIRECTORY

	return os.listdir(COMMITS_DIRECTORY)


@dataclass
class CommitInfo:
	commit_hash: str
	timestamp: datetime.datetime
	message: str | None
	parents: set[str]

	# Files in commit: [("hash sum", "path/to/file.txt"), ...]
	files: list[tuple[str, str]]

	# Files available locally
	coverage: float  # 0.0 to 1.0

	# Total coverage, including local
	total_coverage: float  # 0.0 to infinity


def get_commit_infos() -> list[CommitInfo]:
	from huge.repo.paths import COMMITS_DIRECTORY, FILES_DIRECTORY
	from huge.repo.coverage import analyze_repository_coverages

	result: list[CommitInfo] = []

	files: list[tuple[str, str]]
	available_files = set(os.listdir(FILES_DIRECTORY))

	for commit_hash in get_commit_hashes():
		attributes = {}
		for attribute in ["timestamp", "message", "parents"]:
			if os.path.isfile(f"{COMMITS_DIRECTORY}/{commit_hash}/{attribute}"):
				with open(os.path.join(COMMITS_DIRECTORY, commit_hash, attribute)) as f:
					attributes[attribute] = f.read()

			with open(os.path.join(COMMITS_DIRECTORY, commit_hash, "files")) as f:
				files = [tuple(x.split(maxsplit=1)) for x in f.readlines()]

		if files:
			coverage = sum(file_hash in available_files for file_hash, file_path in files) / len(files)
		else:
			coverage = 1

		result.append(
			CommitInfo(
				commit_hash=commit_hash,

				timestamp=datetime.datetime.fromisoformat(
					attributes["timestamp"],
				).replace(
					tzinfo=datetime.timezone.utc,
				).astimezone(None),

				message=attributes.get("message"),

				parents={x.strip() for x in attributes["parents"].splitlines()},

				files=files,

				coverage=coverage,

				total_coverage=analyze_repository_coverages(commit_hash).coverage,
			)
		)

	return sorted(result, key=lambda x:x.timestamp)


def get_current_commit() -> str | None:
	"""
	Get the current activated commit
	"""
	from .paths import CURRENT_COMMIT_FILE

	if os.path.isfile(CURRENT_COMMIT_FILE):
		with open(CURRENT_COMMIT_FILE) as f:
			return f.readline().strip()

	return None


def create_commit(message: str | None) -> None:
	# TODO merayen make sure to only commit files in .huge/stage

	import datetime
	import shutil
	from huge.repo import create_hash
	from huge.repo.commit import get_current_commit
	from huge.repo.paths import (
		COMMITS_DIRECTORY,
		CURRENT_COMMIT_FILE,
		FILES_DIRECTORY,
	)
	from huge.repo.stage import (
		get_staged_files_2,
		hash_workspace_files,
		reset_staging,
	)

	current_commit_hash = get_current_commit()
	previous_commit_files: dict[str, str] = {}

	if current_commit_hash:
		previous_commit_files = get_commit_files(current_commit_hash)

	workspace_files: dict[str, str] = hash_workspace_files()  # TODO merayen performance: don't hash files that are not staged

	staged_files: set[str] = get_staged_files_2()

	commit_hash = create_hash()

	assert not os.path.exists(os.path.join(COMMITS_DIRECTORY, commit_hash))

	os.mkdir(os.path.join(COMMITS_DIRECTORY, commit_hash))

	# Copy files that doesn't exist into FILES_DIRECTORY
	# TODO merayen rename all "hash_sum" to "path_sum"
	for path, hash_sum in workspace_files.items():
		if path in staged_files:  # Only commit staged files
			storage_path = os.path.join(FILES_DIRECTORY, hash_sum)

			if not os.path.isfile(storage_path):
				shutil.copyfile(path, storage_path)

	# Files that should go/be forwarded into the commit we are making, minus the ones to remove
	with open(os.path.join(COMMITS_DIRECTORY, commit_hash, "files"), "w") as f:
		# Add files that are staged and in workspace
		for path in set(workspace_files) & staged_files:
			hash_sum = workspace_files[path]
			f.write(f"{workspace_files[path]}\t{path}\n")

		# Write all the other files that are untouched (not staged)
		for path in set(previous_commit_files) - staged_files:
			hash_sum = previous_commit_files[path]
			assert hash_sum
			f.write(f"{hash_sum}\t{path}\n")

	# Write commit message
	if message is not None and message.strip():
		with open(os.path.join(COMMITS_DIRECTORY, commit_hash, "message"), "w") as f:
			f.write(message)

	# Write list of parent to commit
	with open(os.path.join(COMMITS_DIRECTORY, commit_hash, "parents"), "w") as f:
		if current_commit_hash := get_current_commit():
			f.write(f"{current_commit_hash}\n")

	# Write timestamp to commit
	with open(os.path.join(COMMITS_DIRECTORY, commit_hash, "timestamp"), "w") as f:
		f.write(datetime.datetime.utcnow().isoformat())

	# Move current position to this commit
	with open(os.path.join(CURRENT_COMMIT_FILE), "w") as f:
		f.write(commit_hash)

	# Remove the file that says which files are to be committed
	reset_staging()


def get_commit_files(commit_hash: str) -> dict[str, str]:
	"""
	Get all the paths and their checksum in a commit
	"""
	from huge.repo.paths import COMMITS_DIRECTORY

	result: dict[str, str] = {}

	commit_path = os.path.join(COMMITS_DIRECTORY, commit_hash, "files")

	if not os.path.isfile(commit_path):
		return {}

	with open(commit_path) as f:
		for x in f:
			x = x.strip()
			if x:
				hash_sum, path = x.split("\t")
				result[os.path.normpath(path)] = hash_sum

	return result


def checkout_commit(commit_hash: str) -> None:
	"""
	Replace workspace files with files from another revision
	"""
	import pathlib
	import shutil
	from huge import fail
	from huge.repo.paths import CURRENT_COMMIT_FILE, FILES_DIRECTORY

	ensure_commit_exists(commit_hash)

	previous_commit_files = get_commit_files(get_current_commit())

	commit_files: dict[str, str] = get_commit_files(commit_hash)

	# Verify that we actually got all the files
	for path, path_sum in commit_files.items():
		if not os.path.isfile(os.path.join(FILES_DIRECTORY, path_sum)):
			fail(
				"ERROR: Missing one or more files locally.\n\n"
				f"Try:\n  huge pull {commit_hash}\n\n"
				"...which will try to retrieve the data from any of the known remotes."
			)
			return

	# Remove files that was tracked in previous commit
	files_to_remove = set(previous_commit_files) - set(commit_files)
	for path in files_to_remove:
		os.remove(path)

	# Remove empty directories that was tracked in previous commit, but not in the one we checking
	# out.
	for path in files_to_remove:
		while path := os.path.split(path)[0]:
			if os.path.isdir(path) and not os.listdir(path):
				shutil.rmtree(path)

	# Copy files from the commit we are checking out
	for path, path_sum in commit_files.items():
		if folder_path := os.path.split(path)[0]:
			pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

		shutil.copyfile(os.path.join(FILES_DIRECTORY, path_sum), path)

	# Change the current commit
	with open(CURRENT_COMMIT_FILE, "w") as f:
		f.write(commit_hash)


def checkout_files(commit_hash: str, files: list[str]) -> None:
	"""
	Checkout some files from another commit

	Requires that the files are available.
	"""
	import pathlib
	import shutil
	from huge import fail
	from huge.repo.paths import FILES_DIRECTORY

	ensure_commit_exists(commit_hash)

	commit_files: dict[str, str] = get_commit_files(commit_hash)

	not_found: list[str] = []
	for x in files:
		if os.path.normpath(x) not in commit_files:
			not_found.append(x)

	if not_found:
		fail("Files not found in commit:\n  " + "\n  ".join(not_found))
		return

	for path, path_sum in commit_files.items():
		if path not in files:
			continue

		assert os.path.isfile(os.path.join(FILES_DIRECTORY, path_sum))

		# Create folders if not exists
		if folder_path := os.path.split(path)[0]:
			pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

		# We overwrite changed files, in the same manner as git does
		shutil.copyfile(os.path.join(FILES_DIRECTORY, path_sum), path)


# TODO merayen make sure this one is catched
class CommitNotFound(Exception):
	pass


def ensure_commit_exists(commit_hash: str) -> None:
	from huge.repo.paths import COMMITS_DIRECTORY

	if not os.path.isdir(os.path.join(COMMITS_DIRECTORY, commit_hash)):
		raise CommitNotFound(repr(commit_hash))
