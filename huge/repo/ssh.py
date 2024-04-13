"""
Common methods for communication over SSH
"""
from huge.repo.address import SSHAddress


def get_remote_files(address: SSHAddress) -> set[str]:
	"""
	Retrieve a list of available files from remote

	Returns the hashes of the files.
	"""
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

	remote_files, _ = process.communicate()

	if process.returncode:
		fail("Could not transfer files")
		return {}

	return {x.strip() for x in remote_files.decode().splitlines()}

