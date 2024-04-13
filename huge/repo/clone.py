"""
Cloning from a remote repository
"""
import os
from huge.repo.address import PathAddress, SSHAddress


class InvalidRepositoryAddress(Exception):
	pass


class CouldNotCloneRemote(Exception):
	pass


def clone_repository(address: str) -> None:
	from huge.repo import create_hash, is_repository
	from huge.repo.address import parse_address
	from huge.repo.fetch import fetch_repositories
	from huge.repo.paths import IGNORE_FILE, REMOTES_FOLDER

	parsed_address = parse_address(address)

	assert not os.path.exists(os.path.split(parsed_address.path)[1])

	previous_path = os.path.abspath(os.getcwd())

	# Create folder that has the same name of the folder from the repository we are cloning
	os.mkdir(os.path.split(parsed_address.path)[1])

	try:
		os.chdir(os.path.split(parsed_address.path)[1])

		if isinstance(parsed_address, PathAddress):
			assert os.path.isdir(parsed_address.path)
			_clone_local(parsed_address)

		elif isinstance(parsed_address, SSHAddress):
			_clone_remote(parsed_address)

		else:
			raise NotImplementedError

		# Add the remote we clone from to our own list of remotes
		# TODO merayen replace with add_remote()?
		add_remote_path = os.path.join(REMOTES_FOLDER, create_hash())
		os.mkdir(add_remote_path)
		with open(os.path.join(add_remote_path, "address"), "w") as f:
			f.write(address)

		# Delete the automatically created, special .hugeignore file
		os.remove(IGNORE_FILE)

		# Do a fetch to get commits and coverages
		fetch_repositories()

	finally:
		os.chdir(previous_path)


def _clone_remote(address: SSHAddress) -> None:
	"""
	Clone a remote repository

	Only copies the files that are necessary to do a fetch afterwards to get the
	actual files needed.
	"""
	import subprocess
	from huge.repo import create_repository
	from huge.repo.paths import HUGE_DIRECTORY, REMOTES_FOLDER, REPO_ID_FILE

	# Create a new repository at current path that we will overwrite
	create_repository()

	process = subprocess.Popen(
		[
			"rsync", "-ahz", "--info=progress2",

			# Sources - only the files that are initially needed
			f"{address.login}@{address.server}:{address.path}/{REPO_ID_FILE}",
			f"{address.login}@{address.server}:{address.path}/{REMOTES_FOLDER}",

			# Target
			HUGE_DIRECTORY,
		],
	)

	process.wait()

	if process.returncode:
		# TODO merayen at this point, maybe we should invalidate the cloned repository to make it unusable
		raise CouldNotCloneRemote


def _clone_local(address: PathAddress) -> None:
	"""
	Clone a local repository

	Only copies the files that are necessary to do a fetch afterwards to get the
	actual files needed.
	"""
	import shutil
	from huge.repo import create_repository
	from huge.repo.paths import HUGE_DIRECTORY, REMOTES_FOLDER, REPO_ID_FILE

	if not os.path.isdir(os.path.join(address.path, HUGE_DIRECTORY)):
		raise InvalidRepositoryAddress

	# Create a new repository at current path that we will overwrite
	create_repository()

	# Overwrite our repo ID
	shutil.copyfile(
		os.path.join(address.path, REPO_ID_FILE),
		REPO_ID_FILE,
	)

	# Copy remotes
	shutil.copytree(
		os.path.join(address.path, REMOTES_FOLDER),
		REMOTES_FOLDER,
		dirs_exist_ok=True,
	)
