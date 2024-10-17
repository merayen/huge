"""
Handling of remotes
"""
import datetime
from typing import Iterator
from dataclasses import dataclass


def add_remote(address: str) -> None:
	import os
	from huge.repo.paths import REMOTES_FOLDER
	from huge.repo import create_hash

	if any(x.address.strip() == address.strip() for x in get_remotes()):
		return  # Silently ignore request

	remote_hash = create_hash()

	os.mkdir(os.path.join(REMOTES_FOLDER, remote_hash))

	with open(os.path.join(REMOTES_FOLDER, remote_hash, "address"), "w") as f:
		f.write(f"{address.strip()}\n")


@dataclass
class RemoteInfo:
	address: str
	remote_hash: str
	last_coverage_update: datetime.datetime | None


def get_remotes() -> Iterator[RemoteInfo]:
	import os
	from huge.repo.paths import REMOTES_FOLDER

	for x in os.listdir(REMOTES_FOLDER):
		if os.path.isfile(os.path.join(REMOTES_FOLDER, x, "disabled")):
			continue

		with open(os.path.join(REMOTES_FOLDER, x, "address")) as f:
			address = f.read()

		# Figure out the last time the coverage file was updated
		coverage_file = os.path.join(REMOTES_FOLDER, x, "coverage")

		mtime: datetime.datetime | None = None

		if os.path.isfile(coverage_file):
			mtime = datetime.datetime.fromtimestamp(
				os.path.getmtime(coverage_file),
			).astimezone(None)

		yield RemoteInfo(
			address=address.strip(),
			remote_hash=x.strip(),
			last_coverage_update=mtime,
		)
