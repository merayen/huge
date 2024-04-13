"""
Fecthing metadata to and from remote repositories
"""
from huge.repo.address import PathAddress, SSHAddress


def fetch_repositories() -> None:
	import os
	import shutil
	from huge import error, output
	from huge.repo.address import parse_address
	from huge.repo.paths import COMMITS_DIRECTORY, REMOTES_FOLDER, REPO_ID_FILE
	from huge.repo.remote import get_remotes

	local_commits = set(os.listdir(COMMITS_DIRECTORY))

	for remote in get_remotes():
		# TODO merayen verify that we verify the remote repository id, and that it is equal

		address = parse_address(remote.address)

		output(f"Fetching from {address}")
		if isinstance(address, PathAddress):
			if not os.path.isdir(address.path):
				error(f"Invalid address: {remote.address}. Skipped.")
				continue

			remote_commits = set(os.listdir(os.path.join(address.path, COMMITS_DIRECTORY)))

			# Verify that the remote has the same repository id as we do
			with open(os.path.join(address.path, REPO_ID_FILE)) as f:
				remote_id = f.read().strip()

			with open(os.path.join(REPO_ID_FILE)) as f:
				local_id = f.read().strip()

			if remote_id != local_id:
				error(f"Remote repository is another repository: '{address.path}'. Skipped")
				continue

			# Send commit metadata to remote
			for commit_hash in remote_commits - local_commits:
				shutil.copytree(
					os.path.join(address.path, COMMITS_DIRECTORY, commit_hash),
					os.path.join(COMMITS_DIRECTORY, commit_hash),
				)

			# Retrieve commit data from local remote
			for commit_hash in local_commits - remote_commits:
				shutil.copytree(
					os.path.join(COMMITS_DIRECTORY, commit_hash),
					os.path.join(address.path, COMMITS_DIRECTORY, commit_hash),
				)

			# Get and write coverage from remote
			with open(os.path.join(REMOTES_FOLDER, remote.remote_hash, "coverage"), "w") as f:
				for file_hash in _fetch_local_coverage_information(address):
					f.write(f"{file_hash}\n")

		elif isinstance(address, SSHAddress):
			try:
				_remote_fetch(address, remote.remote_hash)
			except InvalidRemoteData as exception:
				error(str(exception))

		else:
			raise NotImplementedError


def _remote_fetch(address: SSHAddress, remote_hash: str) -> None:
	import os
	import subprocess
	from huge.repo.paths import COMMITS_DIRECTORY, REPO_ID_FILE, REMOTES_FOLDER

	ssh = ["ssh", f"{address.login}@{address.server}"]

	process = subprocess.Popen(
		ssh +
		[
			"cat",
			f"{address.path}/{REPO_ID_FILE}",
		],
		stdout=subprocess.PIPE,
	)

	stdout, _ = process.communicate()

	repo_id: str = stdout.decode().strip()

	if process.returncode:
		raise InvalidRemoteData("Not able to list files from remote")

	if len(repo_id) != 32:
		raise InvalidRemoteData("Invalid remote repository id detected")

	with open(REPO_ID_FILE) as f:
		if repo_id != f.read().strip():
			raise InvalidRemoteData("remote repository id doesn't match local repository id")

	# Now calculate which commits to synchronize
	local_commits: set[str] = set(os.listdir(COMMITS_DIRECTORY))

	# Get list of commits on remote
	process = subprocess.Popen(
		ssh +
		[
			"ls",
			f"{address.path}/{COMMITS_DIRECTORY}",
		],
		stdout=subprocess.PIPE,
	)

	stdout, _ = process.communicate()

	if process.returncode:
		raise InvalidRemoteData

	remote_commits: set[str] = {x.strip() for x in stdout.decode().splitlines() if x.strip()}

	# Send commits we have that remote is missing
	if missing_commits := local_commits - remote_commits:
		process = subprocess.Popen(
			["rsync", "-ah", "--info=progress2"] +

			# Source files
			[f"{COMMITS_DIRECTORY}/{x}" for x in missing_commits] +

			# Destination
			[f"{address.login}@{address.server}:{address.path}/{COMMITS_DIRECTORY}/"],
		)

		process.wait()

		if process.returncode:
			raise InvalidRemoteData

	# Retrieve commits from remote that we are missing
	if missing_commits := remote_commits - local_commits:
		process = subprocess.Popen(
			["rsync", "-ah", "--info=progress2"] +

			# Source files
			[
				f"{address.login}@{address.server}:{address.path}/{COMMITS_DIRECTORY}/{x}"
				for x in
				missing_commits
			] +

			# Destination
			[f"{COMMITS_DIRECTORY}/"],
		)

		process.wait()

		if process.returncode:
			raise InvalidRemoteData

	# Get and store the remote coverage information locally so that we have it easily available.
	# E.g when being offline.
	with open(os.path.join(REMOTES_FOLDER, remote_hash, "coverage"), "w") as f:
		for file_hash in _fetch_remote_coverage_information(address):
			f.write(f"{file_hash}\n")


class InvalidRemoteData(Exception):
	pass


def _fetch_remote_coverage_information(address: SSHAddress) -> set[str]:
	import subprocess
	from huge.repo.paths import FILES_DIRECTORY

	process = subprocess.Popen(
		[
			"ssh",
			f"{address.login}@{address.server}",
			"ls",
			f"{address.path}/{FILES_DIRECTORY}",
		],
		stdout=subprocess.PIPE,
	)

	stdout, _ = process.communicate()

	if process.returncode:
		raise InvalidRemoteData(f"Could not list remote repository files: {address}")

	file_hashes: set[str] = {x.strip() for x in stdout.decode().splitlines()}

	_verify_file_hashes(file_hashes)

	return file_hashes


def _fetch_local_coverage_information(address: SSHAddress) -> set[str]:
	import os
	from huge.repo.paths import FILES_DIRECTORY

	file_hashes = set(os.listdir(os.path.join(address.path, FILES_DIRECTORY)))

	_verify_file_hashes(file_hashes)

	return file_hashes


def _verify_file_hashes(file_hashes: set[str]) -> None:
	"""
	Verify the list of files that they really are valid hashes
	"""
	x: str
	for x in file_hashes:
		if len(x) != 32:
			raise InvalidRemoteData(f"Invalid file name in remote: {x}")

		try:
			int(x, 16)
		except ValueError:
			raise InvalidRemoteData(f"Invalid hex in file name in remote: {x}")
