"""
Sending a repository to another location

The opposite of cloning.
"""
from huge.repo.address import SSHAddress


def send_repository(address: str) -> None:
	from huge.repo import is_repository
	from huge.repo.address import parse_address, PathAddress
	from huge.repo.fetch import fetch_repositories
	from huge.repo.remote import add_remote

	assert is_repository()

	parsed_address = parse_address(address)

	if isinstance(parsed_address, PathAddress):
		_local_send(parsed_address.path)

	elif isinstance(parsed_address, SSHAddress):
		_remote_send(parsed_address)

	else:
		raise NotImplementedError

	# Store newly created repository as a remote on our end
	add_remote(address)

	# Then do a complete fetch which will update commit information on new remote (and all others)
	fetch_repositories()


def _local_send(address: str) -> None:
	import os
	import shutil
	from huge.repo import create_repository_structure
	from huge.repo.paths import REPO_ID_FILE

	assert not os.path.exists(address)

	os.mkdir(address)

	# Create structure
	create_repository_structure(address)

	# Copy repository id
	shutil.copy(REPO_ID_FILE, os.path.join(address, REPO_ID_FILE))


def _remote_send(parsed_address: SSHAddress) -> None:
	import subprocess
	from huge import fail
	from huge.repo.paths import COMMITS_DIRECTORY, FILES_DIRECTORY, REMOTES_FOLDER, REPO_ID_FILE

	# Create folder
	process = subprocess.Popen(
		[
			"ssh", f"{parsed_address.login}@{parsed_address.server}",
			"mkdir", "-p", f"{parsed_address.path}/{FILES_DIRECTORY}",
		]
	)

	process.wait()

	if process.returncode:
		fail(f"Could not create repository at {parsed_address}")
		return

	# Send the actual repository metadata
	process = subprocess.Popen(
		["rsync", "-ah", "--info=progress2"] +

		# Sources
		[
			REPO_ID_FILE,
			REMOTES_FOLDER,
			COMMITS_DIRECTORY,
		] +

		# Destination
		[f"{parsed_address.login}@{parsed_address.server}:{parsed_address.path}/.huge/"]
	)

	process.wait()

	if process.returncode:
		fail(f"Could not transfer files from {parsed_address}")
		return
