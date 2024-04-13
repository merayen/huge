"""
Dropping commit data from local repository
"""
from huge.repo.commit import CommitInfo


def drop_commit_files(commit_hashes: list[str]) -> None:
	"""
	Delete local files that the commits represents

	This is mainly meant for saving space or get rid of unwanted data.
	"""
	raise NotImplementedError("drop commit files")  # TODO merayen drop commit files


def get_removable_commits(
	commit_hashes: list[str],
	commit_infos: list[CommitInfo],
) -> list[CommitInfo]:
	"""
	Calculates which commits that has enough coverage so that they can be deleted
	"""
	result: list[CommitInfo] = []

	# Remove commits that have too little coverage
	commit_info: CommitInfo
	for commit_info in commit_infos:
		if commit_info.commit_hash not in commit_hashes:
			continue

		# Only list commits that are replicated elsewhere
		if commit_info.total_coverage - commit_info.coverage >= 1.0:
			result.append(commit_info)

	return result


def get_removable_files(
		commit_hashes: list[str],
		commit_infos: list[CommitInfo],
	) -> list[CommitInfo]:
	"""
	Calculates which files can be deleted without causing dataloss for other commits

	This requires a newly "huge fetch" from all repositories to not risk
	calculation on outdated data.
	"""
	from huge.repo.commit import get_commit_infos

	assert isinstance(commit_hashes, list)
	assert all(isinstance(commit_hash, str) for commit_hash in commit_hashes)

	assert isinstance(commit_infos, list)
	assert all(isinstance(commit_info, CommitInfo) for commit_info in commit_infos)

	# Get the files we want to try to delete
	to_drop: set[str] = {
		file_hash
		for commit_info in commit_infos
		if commit_info.commit_hash in commit_hashes
		for file_hash, path in commit_info.files
	}

	# Remove files that are pointed at by commits not in commit_hashes
	to_drop -= {
		file_hash
		for commit_info in commit_infos
		if commit_info.commit_hash not in commit_hashes
		for file_hash, path in commit_info.files
	}

	return to_drop
