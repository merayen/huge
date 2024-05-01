"""
Pushing commit files to other repositories
"""
from huge.repo.address import SSHAddress
from huge.repo.remote import RemoteInfo


def push_commit(commits: list[str], remotes: list[RemoteInfo]) -> None:
	"""
	Push actual user files to remote repositories

	Before doing this, make sure to be synchronized with repositories. This does not fetch any
	metadata in any way. Use "huge fetch".

	If metadata is not updated on remotes, they might not have any commits actually pointing at the
	files.
	"""
	import os
	from huge import output
	from huge.repo.commit import get_commit_files
	from huge.repo.address import PathAddress, SSHAddress, parse_address
	from huge.repo.paths import REMOTES_FOLDER

	assert commits
	assert remotes

	# TODO merayen add the files pushed to the .huge/remotes/.../coverage file... here? otherwise another fetch is needed

	commit_files = list(
		{
			file_hash
			for commit in commits
			for file_hash in get_commit_files(commit).values()
		}
	)

	remote: RemoteInfo
	for remote in remotes:
		address = parse_address(remote.address)

		output(f"Pushing files to {address}")

		if isinstance(address, PathAddress):
			file_hashes_pushed = _local_push(address.path, commit_files=commit_files)

		elif isinstance(address, SSHAddress):
			file_hashes_pushed = _remote_push(address, commit_files=commit_files)

		else:
			raise NotImplementedError

		# Write to remote's coverage file for the files we have sent
		with open(os.path.join(REMOTES_FOLDER, remote.remote_hash, "coverage"), "a") as f:
			for file_hash in file_hashes_pushed:
				f.write(f"{file_hash}\n")


def _local_push(remote_path: str, commit_files: list[str]) -> set[str]:
	import os
	import shutil
	from huge import fail
	from huge.repo.paths import FILES_DIRECTORY, HUGE_DIRECTORY, REPO_ID_FILE

	# TODO merayen verify earlier that all the commits actually exists

	if not os.path.isdir(os.path.join(remote_path, HUGE_DIRECTORY)):
		fail(f"Skipping invalid remote '{remote_path}'")
		return set()

	# Verify repository id is the same
	with open(os.path.join(remote_path, REPO_ID_FILE)) as f:
		remote_id = f.read().strip()

	with open(os.path.join(REPO_ID_FILE)) as f:
		local_id = f.read().strip()

	if remote_id != local_id:
		fail(f"Remote repository is another repository: '{remote_path}'")
		return set()

	# Get all the remote files
	remote_files = set(os.listdir(os.path.join(remote_path, FILES_DIRECTORY)))

	# Calculate and send the files that is needed for the remote to represent the whole commit
	files_to_process = set(commit_files) - set(remote_files)

	for file_checksum in files_to_process:
		# TODO merayen should we copy to a temporary location first, then move everything in one go?
		shutil.copy(
			os.path.join(FILES_DIRECTORY, file_checksum),
			os.path.join(remote_path, FILES_DIRECTORY, file_checksum),
		)

	return files_to_process


def _remote_push(address: SSHAddress, commit_files: list[str]) -> set[str]:
	import subprocess
	from huge import fail
	from huge.repo.paths import FILES_DIRECTORY

	process = subprocess.Popen(
		[
			"ssh", f"{address.login}@{address.server}",
			"ls", f"{address.path}/{FILES_DIRECTORY}",
		],
		stdout=subprocess.PIPE,
	)

	stdout, _ = process.communicate()

	if process.returncode:
		fail("Could not transfer files")
		return set()

	remote_files = [x.strip() for x in stdout.decode().splitlines()]

	files_to_process = list(set(commit_files) - set(remote_files))

	if files_to_process:
		while files_to_process:
			current_files, files_to_process = files_to_process[:500], files_to_process[500:]

			process = subprocess.Popen(
				["rsync", "-ah", "--info=progress2", "--ignore-existing"] +

				# Source files
				[f"{FILES_DIRECTORY}/{x}" for x in current_files] +

				# Destination
				[f"{address.login}@{address.server}:{address.path}/{FILES_DIRECTORY}/"],
			)

			process.wait()

			if process.returncode:
				fail("Could not transfer (all) files")
				return set()

	return files_to_process
