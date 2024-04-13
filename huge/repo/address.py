"""
Managing address strings
"""
import os
from dataclasses import dataclass


@dataclass
class SSHAddress:
	"""
	An address to a server via SSH
	"""
	login: str
	server: str
	path: str

	def __str__(self):
		return f"{self.login}@{self.server}:{self.path}"


@dataclass
class PathAddress:
	"""
	A path represented by the local file system

	For example:
		/home/login/repository
		/some-shared-folder-somewhere
	"""
	path: str

	def __str__(self):
		return self.path


# TODO merayen make sure callers check for path existence or that they create it
def parse_address(address: str) -> SSHAddress | PathAddress:
	try:
		return split_remote_address(address)
	except ValueError:
		pass

	return PathAddress(path=address.strip())



def split_remote_address(address: str) -> tuple[str, str, str]:
	server, path = address.split(":", maxsplit=1)
	try:
		login, server = server.split("@", maxsplit=1)
	except ValueError:
		login = os.getlogin()

	return SSHAddress(
		login=login.strip(),
		server=server.strip(),
		path=path.strip(),
	)


def test_remote_path():
	from unittest.mock import patch

	with patch("os.getlogin", return_value="login"):
		address = split_remote_address("server:/home/login/repository")

	assert isinstance(address, SSHAddress)
	assert address.login == "login"
	assert address.server == "server"
	assert address.path == "/home/login/repository"


def test_remote_path_with_login():
	from unittest.mock import patch

	with patch("os.getlogin", return_value="login"):
		address = split_remote_address("mylogin@server:/home/login/repository")

	assert isinstance(address, SSHAddress)
	assert address.login == "mylogin"
	assert address.server == "server"
	assert address.path == "/home/login/repository"


def test_local_path():
	address = parse_address("/tmp")

	assert isinstance(address, PathAddress)
	assert address.path == "/tmp"


if __name__ == '__main__':
	for x in dir():
		if x.startswith("test_"):
			exec(f"{x}()")
