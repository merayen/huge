"""
Calculation of coverage of files
"""
from dataclasses import dataclass


@dataclass
class RepositoryCoverage:
	"""
	Coverage of a single commit
	"""
	address: str

	files_available: set[str]
	files_unavailable: set[str]

	available: bool = True

	@property
	def coverage(self) -> float:
		"""
		Coverage for a single commit on a single remote
		"""
		if len(self.files_available) + len(self.files_unavailable) > 0:
			return len(self.files_available) / (len(self.files_available) + len(self.files_unavailable))

		return 1


@dataclass
class CoverageAnalysis:
	repositories: list[RepositoryCoverage]

	@property
	def coverage(self) -> float:
		"""
		Calculates coverage for all repositories

		Coverage is calculated by file count, not the data size (file sizes) themselves.

		coverage = 0.0
		Data is lost

		coverage = 1.0
		Data is available, but if one or more repository disappears, data could be lost.

		coverage = 1.5
		Data is available, but if one or more repository disappears, data could be lost.
		However, it is statistically less chance of data loss than 1.0.

		coverage = 2.0
		One repository can be removed without any loss of data.

		coverage = 3.0
		Two repositories can be removed without any loss of data.
		"""
		assert self.repositories

		files_required: set[str] = {
			file_hash
			for repository in self.repositories
			for file_hash in repository.files_available | repository.files_unavailable
		}

		if not files_required:
			return 1.0

		file_hash_count = {x: 0 for x in files_required}

		for repository in self.repositories:
			for file_hash in repository.files_available:
				file_hash_count[file_hash] += 1

		coverage = min(file_hash_count.values())

		return coverage + sum(min(1, x - coverage) for x in file_hash_count.values()) / len(file_hash_count)


def analyze_repository_coverages(commit_hash: str) -> CoverageAnalysis:
	"""
	Calculate repositories' coverage of commits

	Returns: {"<commit hash>": RepositoryCoverage(...)}

	User should have fetched latest information from remote repositories before
	running this method.
	"""
	import os
	from huge import error
	from huge.repo.paths import FILES_DIRECTORY, REMOTES_FOLDER
	from huge.repo.commit import get_commit_files, ensure_commit_exists

	ensure_commit_exists(commit_hash)

	commit_files: set[str] = set(get_commit_files(commit_hash).values())

	repositories: list[RepositoryCoverage] = []

	for remote in os.listdir(os.path.join(REMOTES_FOLDER)):

		with open(os.path.join(REMOTES_FOLDER, remote, "address")) as f:
			address = f.read().strip()

		# Check if we have coverage information
		if not os.path.isfile(os.path.join(REMOTES_FOLDER, remote, "coverage")):
			repositories.append(
				RepositoryCoverage(
					available=False,
					address=address,
					files_available=set(),
					files_unavailable=commit_files,
				)
			)
			continue

		# TODO merayen also read when the coverage file was last updated to inform the user

		with open(os.path.join(REMOTES_FOLDER, remote, "coverage")) as f:
			files_available: set[str] = {x.strip() for x in f if x.strip()} & commit_files

		files_unavailable = commit_files - files_available

		repositories.append(
			RepositoryCoverage(
				available=True,
				address=address,
				files_available=files_available,
				files_unavailable=files_unavailable,
			)
		)

	# Add ourselves to the resultset
	files_available = set(os.listdir(FILES_DIRECTORY)) & commit_files

	repositories.append(
		RepositoryCoverage(
			available=True,
			address=".",
			files_available=files_available,
			files_unavailable=commit_files - files_available,
		)
	)

	return CoverageAnalysis(
		repositories=repositories,
	)


def test_coverage_calculation_less_than_1():
	coverage_analysis = CoverageAnalysis(
		repositories=[
			RepositoryCoverage(address="", files_available={"a", "b"}, files_unavailable={"c"}),
			RepositoryCoverage(address="", files_available={"a", "b"}, files_unavailable={"c", "d"}),
		],
	)

	# File "c" and "d" is missing, "a" and "b" exists, therefore 0.5
	assert coverage_analysis.coverage == 0.5


def test_coverage_calculation_one_repo_backed():
	"""
	One repostiroy has all the files. Another one has half of them.
	"""
	coverage_analysis = CoverageAnalysis(
		repositories=[
			RepositoryCoverage(address="", files_available={"a", "b", "c", "d"}, files_unavailable=set()),
			RepositoryCoverage(address="", files_available={"a", "b"}, files_unavailable={"c", "d"}),
		],
	)

	assert coverage_analysis.coverage == 1.5


def test_coverage_calculation_distributed():
	"""
	Two repositories has their own shares of the files

	If one of the repositories are removed, we have dataloss.
	Therefore coverage is 1.0.
	"""
	coverage_analysis = CoverageAnalysis(
		repositories=[
			RepositoryCoverage(address="", files_available={"a", "b"}, files_unavailable={"c", "d"}),
			RepositoryCoverage(address="", files_available={"c", "d"}, files_unavailable={"a", "b"}),
		],
	)

	assert coverage_analysis.coverage == 1.0


def test_coverage_calculation_dataloss():
	coverage_analysis = CoverageAnalysis(
		repositories=[
			RepositoryCoverage(address="", files_available=set(), files_unavailable={"a", "b", "c", "d"}),
			RepositoryCoverage(address="", files_available={"c", "d"}, files_unavailable={"a", "b"}),
		],
	)

	assert coverage_analysis.coverage == 0.5


def test_coverage_calculation_double_coverage():
	coverage_analysis = CoverageAnalysis(
		repositories=[
			RepositoryCoverage(address="", files_available={"a", "b", "c", "d"}, files_unavailable=set()),
			RepositoryCoverage(address="", files_available={"a", "b", "c", "d"}, files_unavailable=set()),
			RepositoryCoverage(address="", files_available={"a"}, files_unavailable={"b", "c", "d"}),
		],
	)

	assert coverage_analysis.coverage == 2.25


if __name__ == '__main__':
	for x in dir():
		if x.startswith("test_"):
			exec(f"{x}()")
