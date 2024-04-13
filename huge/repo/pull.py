"""
Pulling commit files from remote repositories
"""
import os
from huge.repo.address import PathAddress, SSHAddress


def pull_commit(commits: list[str], remotes: list[str]) -> None:
	from huge import output
	from huge.repo.address import PathAddress, parse_address
	from huge.repo.commit import get_commit_files
	from huge.repo.paths import FILES_DIRECTORY

	assert commits
	assert remotes

	# Make a list of all the file checksums we need
	remaining_files = {
		file_hash
		for commit in commits
		for file_hash in get_commit_files(commit).values()
	}

	# Then remove the files we already have locally
	remaining_files -= set(os.listdir(FILES_DIRECTORY))

	for remote in remotes:
		if not remaining_files:
			break  # Got all the files, no reason to get from other remotes

		# TODO merayen exit this loop when all files have been retrieved

		address = parse_address(remote.address)

		output(f"Pulling files from {address}")

		if isinstance(address, PathAddress):
			_local_pull(
				address=address,
				remaining_files=remaining_files,
			)

		elif isinstance(address, SSHAddress):
			_remote_pull(
				address=address,
				remaining_files=remaining_files,
			)

		else:
			raise NotImplementedError

	if remaining_files:
		error("Not able to retrieve all required files.")


def _remote_pull(address: SSHAddress, remaining_files: set[str]) -> None:
	import shutil
	import subprocess
	import tempfile
	from huge import error
	from huge.repo.paths import FILES_DIRECTORY, HUGE_DIRECTORY
	from huge.repo.ssh import get_remote_files

	files_to_process = list(remaining_files & get_remote_files(address))

	with tempfile.TemporaryDirectory(dir=HUGE_DIRECTORY) as d:
		while files_to_process:
			current_files, files_to_process = set(files_to_process[:500]), files_to_process[500:]

			process = subprocess.Popen(
				["rsync", "-ah", "--info=progress2"] +
				[f"{address.login}@{address.server}:{address.path}/{FILES_DIRECTORY}/{x}" for x in current_files] +
				[f"{d}/"],
			)

			process.wait()

			if process.returncode:
				error(f"Could not transfer files from {address}")
				return

			# Move the transferred files as scp reported transfer was successful
			for file_hash in current_files:
				shutil.move(os.path.join(d, file_hash), os.path.join(FILES_DIRECTORY, file_hash))

			remaining_files -= current_files


def _local_pull(address: PathAddress, remaining_files: set[str]) -> None:
	import shutil
	import tempfile
	from huge import fail
	from huge.repo.paths import FILES_DIRECTORY, HUGE_DIRECTORY

	if not os.path.isdir(address.path):
		fail(f"Could not transfer files from {address}")
		return

	files_available = remaining_files & set(os.listdir(os.path.join(address.path, FILES_DIRECTORY)))

	# Copy the files that are available to temporary directory, hopefully on same device.
	# If this fails, with-statement should delete the temporary files.
	with tempfile.TemporaryDirectory(dir=HUGE_DIRECTORY) as d:
		for file_hash in files_available:
			shutil.copy(os.path.join(address.path, FILES_DIRECTORY, file_hash), d)

		# If getting here, move files in place
		for file_hash in files_available:
			shutil.move(os.path.join(d, file_hash), os.path.join(FILES_DIRECTORY, file_hash))

	remaining_files -= files_available
