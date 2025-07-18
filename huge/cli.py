import argparse
import os
from huge.testing import huge_test


def run_command(*args: list[str]) -> None:
	from huge import fail, output, __version__
	from huge.repo.paths import HUGE_DIRECTORY
	from textwrap import wrap

	COMMANDS = {
		"init": (
			"Initialize current folder with a .huge folder",
			f"A folder named {HUGE_DIRECTORY} will be created, without touching any other files.",
		),
		"status": (
			"Show status between workspace files and the active commit",
			"A = File has been added by user\n"
			"C = File has been changed by user\n"
			"D = File has been deleted by user\n\n"
			"Doing a 'huge commit' will take these changes and store them in a new revision."
		),
		"add": (
			"Mark file(s) for committing",
			"Files are marked to be committed next time a 'huge commit' is executed.\n\n"
			"Note: This is not the same as 'git add', as this tool does not save the contents of the "
			"files anywhere, it only marks the file so that it will be taken into next commit.\n"
			"E.g, adding a file that has been changed, then delete it in the workspace, and then commit "
			"will delete that file instead of adding the changes to the commit.\n\n"
			"It is a good idea to always check 'huge status' before doing a commit to see what "
			"really happens."
		),
		"reset": (
			"Unmark a file for committing",
			"Opposite of 'huge add'. The file(s) in the workspace will not be added, changed or deleted "
			"when 'huge commit' is executed."
		),
		"log": (
			"Show a list of revisions",
			"Prints a list of all the commits that exists in the repository. "
			"Note that you will need to run 'huge pull' first to get up-to-date information on the "
			"changes."
		),
		"branches": (
			"List branches",
			"A branch is made whenever a commit has a sibling.\n"
			"E.g the initial commit A has sibling B and C, both B and C are their own branches.\n\n"
			"This command lists commits that has started to diverge. This typically happens if e.g two "
			"people are working on the same commit and then pushes each their own commit based on that "
			"commit.\n\n"
			"This command is similar to 'huge heads', though this one shows the oldest, the first "
			"diverging commit."
		),
		"heads": (
			"List headers",
			"A head is a commit that has no children.\n\n"
			"This command is similar to 'huge branches', though this one shows the newest, the tip of "
			"the branch."
		),
		"commit": (
			"Store a new revision",
			"Copy the changed files into the huge repository locally. "
			"The changes can then afterwards be sent to one or more remotes using "
			"'huge push', or retrieved back locally if any changes want to be undone.\n\n"
			"It is a good idea to always check 'huge status' before doing a commit to see what "
			"really happens."
		),
		"checkout": (  # TODO merayen maybe we should call this command "switch" instead
			# TODO merayen support first argument to be a file only, not needing to specify commit_hash?
			"Swap the workspace files with another revision stored locally.",
			"If there are no changed or deleted files, huge will replace the files with ones that are  "
			"in the commit and set a new active commit.\n\n"
			"If this is not possible, huge will emit an error message and do nothing."
		),
		"drop": (
			"Deletes files in a commit",
			"WARNING: This can permanently delete data!\n\n"
			"This removes the actual files in a commit from the local repository. "
			"The commit will still exist, but the files that it points at will be deleted, as long as "
			"there are no other commits pointing at those files.\n\n"
			"The files can be retrieved again if this commit exists on a remote. Use 'huge pull "
			"<commit>' for that.\n\n"
			"Command automatically does a fetch from repository to reduce the risk of loosing data "
			"and will warn the user if it can't find copies of the files elsewhere.\n\n"
			"To delete files without doing any attempt at checking if any remote repositories are known "
			"to have the data, use -f or --force.",
			# TODO merayen this command should probably check if any other remotes has the data files
		),
		"drop-all": (
			"Deletes all commit files, removing all local coverage",
			"WARNING: This can permanently delete data!\n\n"
			# TODO merayen update documentation
			"Same as drop command, but does not take any commit hashes.\n\n"
			"This command is usually used when wanting to free up space locally and the data is "
			"available elsewhere, or the data is not important and can be permanently deleted.\n\n"
			"Command automatically does a fetch from repository to reduce the risk of loosing data.\n\n"
			"To delete files without doing any attempt at checking if any remote repositories are known "
			"to have the data, use -f or --force.",
		),
		"push": (
			"Send commits to a remote repository",
			"This will send commit metadata (same as 'huge fetch') and the commits' files to the remote "
			"repositories that is needed to represent the current commit.\n\n"
			"If no commit hash is defined, the current commit will be sent.\n\n"
			"To only send to a single remote, use --remote address-to-remote.\n\n"
			"Usual usage of sending files to a remote while working:\n"
			"  huge commit\n  huge push\n  huge commit\n  huge push\n  ..."
		),
		"pull": (
			"Pull one or more commits from a remote",
			"Get the actual files from a commit. This makes this repository a mirror of the files for "
			"another repository."
		),
		"fetch": (
			"Fetch metadata from and to remotes",
			"This does not transfer any actual data, only the metadata and revision information. This is "
			"needed before doing any 'huge pull'."
		),
		"merge": (
			"Merge another commit into this commit",
			"Creates a new commit that brings two divergent commits together.\n\n"
			"This effectively commits any new or changed files in the workspace.\n\n"
			"NOTE: There will be no attempt at any automatic merging. User needs to manually check out "
			"files from the other revision and make sure that the current files in the directory is what "
			"should be in the upcoming commit.\n\n"
			"Example:\n\n"
			"# Check out the file from another commit\n"
			"huge checkout 0123456789abcdef my_file.mp4\n\n"
			"# Creates a new commit with two parent commits\n"
			"huge merge 0123456789abcdef\n\n"
			"# Send the changes to the remotes\n"
			"huge push"
		),
		"remotes": (
			"List remotes",
			"These are the servers or other local folders that huge synchronize data with."
			# TODO merayen print last sync date (get from coverage-file timestamp?)
		),
		"remote-add": (
			"Add a remote",
			"This remote will then be synchronized with whenever 'huge fetch', 'huge pull' or 'huge "
			"push' is run."
		),
		"clone": (
			# TODO merayen create a new folder and clone into that instead
			"Clone from a remote repository",
			"Retrieves all the metadata from the remote repository without downloading any of the actual "
			"files. Use 'huge log' to find a revision of interest and then 'huge checkout <commit_hash>' "
			"to get the commit and download the files.\n\n"
			"Valid remotes are:\n"
			"  /home/login/repository\n"
			"  login@server:/home/login/repository\n"
			"  login@server:repository\n\n"
			"Your now cloned repository will then automatically point at the remote and be able to push "
			"and pull from it."
		),
		"send": (
			# TODO merayen create a new folder and clone into that instead
			"Send repository to another server or folder",
			"Opposite of clone-command. Does not send the user files themselves, only the metadata. "
			"Send data with 'huge push' afterwards to send files."
		),
		"verify": (
			"Check this local repository's integrity",
			"Verifies the structure of the .huge folder and that all the files stored are not corrupted."
		),
	}

	COMMANDS_TODO = ["drop", "drop-all", "verify", "merge", "send", "add", "reset"]

	assert not (set(COMMANDS_TODO) - set(COMMANDS))

	parser = argparse.ArgumentParser("huge", description="Handling huge files", add_help=False)

	sub_parser = parser.add_subparsers(help="Subcommands", dest="command")

	parsers = {}
	for name, (title, text) in COMMANDS.items():
		parsers[name] = sub_parser.add_parser(name=name, description=title, add_help=False)

	parsers["add"].add_argument("file", nargs="+")
	parsers["reset"].add_argument("file", nargs="+")
	parsers["commit"].add_argument("-m", "--message")
	parsers["merge"].add_argument("commit_hash")
	parsers["checkout"].add_argument("commit_hash")
	parsers["checkout"].add_argument("files", nargs="*")
	parsers["pull"].add_argument("commit_hash", nargs="+")
	parsers["pull"].add_argument("-r", "--remote", nargs="*")
	parsers["push"].add_argument("commit_hash", nargs="*")
	parsers["push"].add_argument("-r", "--remote", nargs="*")
	parsers["drop"].add_argument("commit_hash", nargs="+")
	parsers["drop"].add_argument(
		"-f",
		"--force",
		action="store_true",
	)
	parsers["drop-all"].add_argument(
		"-f",
		"--force",
		action="store_true",
	)
	parsers["remote-add"].add_argument("remote")
	parsers["clone"].add_argument("remote")
	parsers["send"].add_argument("remote")

	# Help
	help_parser = sub_parser.add_parser(name="help", help="Show help for a command", add_help=False)
	help_parser.add_argument("help_command", nargs="?", choices=list(COMMANDS) + COMMANDS_TODO)

	opts = parser.parse_args(args)

	# Find method that represents the command and execute it
	if opts.command and f"{opts.command.replace('-', '_')}_command" in globals():
		eval(f"{opts.command.replace('-', '_')}_command(opts)")
	elif opts.command == "help":
		if not opts.help_command:
			output("usage: huge help <command>")
		else:
			output("\n".join(wrap(COMMANDS[opts.help_command][0], 80)) + "\n")
			output(parsers[opts.help_command].format_usage())
			output("Description")
			output(
				"\n".join(
					f"    {y}"
					for x in COMMANDS[opts.help_command][1].splitlines()
					for y in (wrap(x, 70) if x.strip() else [""])
				)
			)
	elif not opts.command:
		output(f"Huge version {'.'.join(str(x) for x in __version__)}")
		output("\nCommands:\n" + "\n".join(f'  {x}' for x in sorted(COMMANDS)))
		output("\nNot implemented yet:\n" + "\n".join(f'  {x}' for x in sorted(COMMANDS_TODO)))
		output("\nType 'huge help <command>' to get more specific help")
	else:
		fail("Not implemented yet")


def require_repository(func):
	def decorator(opts: argparse.Namespace) -> None:
		from huge import fail
		from huge.repo import is_repository
		if not is_repository():
			fail("Not a .huge repository, or you are not in the root level of it")
			return

		return func(opts)

	return decorator


def init_command(opts: argparse.Namespace) -> None:
	"""
	Create the folder and file structure that represents an empty huge repository
	"""
	from huge import fail
	from huge.repo import create_repository
	from huge.repo.paths import HUGE_DIRECTORY

	if os.path.exists(HUGE_DIRECTORY):
		fail("Huge already initialized")
		return

	create_repository()


@huge_test
def test_init() -> None:
	from huge.testing import catch_fail

	run_command("init")

	assert os.path.isdir(".huge")

	with catch_fail() as out:
		run_command("init")
		assert out.getvalue() == "Huge already initialized\n"

	assert os.path.isdir(".huge/commits")
	assert os.path.isdir(".huge/storage")
	assert os.path.isfile(".huge/current")


@require_repository
def commit_command(opts: argparse.Namespace) -> None:
	from huge.repo.commit import create_commit

	create_commit(opts.message)


@huge_test
def test_commit() -> None:
	import hashlib
	from huge.testing import catch_fail

	def verify_stored_file(path: str) -> None:
		with open(".huge/current") as f:
			assert len(f.read()) == 32

		with open(path, "rb") as f:
			content = f.read()

			hash_sum = hashlib.md5(content).hexdigest().lower()

			with open(f".huge/storage/{hash_sum}", "rb") as f2:
				assert content == f2.read()

	with catch_fail() as out:
		run_command("commit")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	# Create a file
	os.mkdir("folder")
	with open("folder/first_file.txt", "w") as f:
		f.write("Content")

	run_command("add", "folder")
	run_command("commit")

	verify_stored_file("folder/first_file.txt")

	# Change file
	with open("folder/first_file.txt", "a") as f:
		f.write("Changed")

	# Commit again, but also include a message
	run_command("add", "folder")
	run_command("commit", "-m", "Changing first_file.txt")
	verify_stored_file("folder/first_file.txt")

	# Verify that our message is stored correctly
	with open(".huge/current") as f2:
		with open(f".huge/commits/{f2.read()}/message") as f:
			assert f.read() == "Changing first_file.txt"

	with open("other.txt", "w") as f:
		f.write("Other")

	os.remove("folder/first_file.txt")

	run_command("add", "folder", "other.txt")
	run_command("commit")
	verify_stored_file("other.txt")


@require_repository
def status_command(opts: argparse.Namespace) -> None:
	# TODO merayen split view into staged files and unstaged files
	from huge import output
	from huge.repo.commit import get_current_commit
	from huge.repo.stage import get_workspace_files, get_staged_files_2

	new, changed, deleted, unchanged = get_workspace_files()
	ordered_keys = sorted(set(new) | set(changed) | deleted | set(unchanged))
	staged_files: list[str] = sorted(get_staged_files_2())

	if commit_hash := get_current_commit():
		output(f"Commit: {commit_hash}")

	changed_text: list[str] = []

	if staged_files:
		changed_text.append("Staged for commit:")

	changed_text.extend(f"  A {x}" for x in ordered_keys if x in staged_files and x in new)
	changed_text.extend(f"  C {x}" for x in ordered_keys if x in staged_files and x in changed)
	changed_text.extend(f"  D {x}" for x in ordered_keys if x in staged_files and x in deleted)

	if (set(new) | set(changed) | set(deleted)).difference(set(staged_files)):
		if changed_text:
			changed_text.append("")

		changed_text.append("Not staged for commit:")

	changed_text.extend(f"  A {x}" for x in ordered_keys if x not in staged_files and x in new)
	changed_text.extend(f"  C {x}" for x in ordered_keys if x not in staged_files and x in changed)
	changed_text.extend(f"  D {x}" for x in ordered_keys if x not in staged_files and x in deleted)

	if changed_text:
		output("\n".join(changed_text))


@huge_test
def test_status() -> None:
	from huge.testing import catch_fail, catch_output

	with catch_fail() as out:
		run_command("status")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	# Do a status. We don't expect any output here.
	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == "Not staged for commit:\n  A .hugeignore\n"

	# Add a file
	os.mkdir("folder")
	with open("folder/first_file.txt", "w") as f:
		pass

	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == "Not staged for commit:\n  A .hugeignore\n  A folder/first_file.txt\n"

	run_command("add", "folder", ".hugeignore")
	run_command("commit")

	with open(".huge/current") as f:
		revision = f.read()

	# Don't expect any output
	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == f"Commit: {revision}\n"

	with open("folder/first_file.txt", "w") as f:
		f.write("Changed")

	with open("new_file.txt", "w") as f:
		pass

	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == f"Commit: {revision}\nNot staged for commit:\n  A new_file.txt\n  C folder/first_file.txt\n"

	run_command("add", "folder", "new_file.txt")
	run_command("commit")

	with open(".huge/current") as f:
		revision = f.read()

	# Should be no output now
	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == f"Commit: {revision}\n"

	# Remove one of the files
	os.remove("folder/first_file.txt")

	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == f"Commit: {revision}\nNot staged for commit:\n  D folder/first_file.txt\n"


@require_repository
def log_command(opts: argparse.Namespace) -> None:
	from huge import output
	from huge.repo.commit import get_commit_infos, CommitInfo


	commit_info: CommitInfo
	for commit_info in reversed(get_commit_infos()):
		datas = [
			commit_info.commit_hash,
			commit_info.timestamp.strftime("%Y-%m-%d %H:%M"),
			f"B={commit_info.branch}",
			f"L={int(commit_info.coverage)} R={int(commit_info.total_coverage)}",
		]

		if commit_info.message:
			datas.append(commit_info.message)

		output(" ".join(datas))


@huge_test
def test_log() -> None:
	import datetime
	from huge.testing import catch_fail, catch_output

	with catch_fail() as out:
		run_command("log")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	# We haven't committed anything. There should be no output
	run_command("log")

	os.mkdir("folder")
	with open("folder/first_file.txt", "w") as f:
		f.write("Content")

	# Still no logs should be written
	run_command("log")

	# Now we create a revision (a log entry)
	run_command("add", "folder")
	run_command("commit", "--message", "Added first_file.txt")

	# Get the log revision
	with open(".huge/current") as f:
		commit_hash = f.read()

	# Get the timestamp when the commit was created
	with open(f".huge/commits/{commit_hash}/timestamp") as f:
		timestamp = datetime.datetime.fromisoformat(f.read())

	timestamp = timestamp.replace(tzinfo=datetime.timezone.utc).astimezone(None)

	with open(f".huge/commits/{commit_hash}/message") as f:
		message = f.read()

	with catch_output() as out:
		run_command("log")
		assert out.getvalue() == f"{commit_hash} {str(timestamp)[:16]} 100%/100% {message}\n"


@require_repository
def merge_command(opts: argparse.Namespace) -> None:
	assert opts.commit_hash

	raise NotImplementedError("Implement merging")  # TODO merayen implement merging


@huge_test
def test_merge() -> None:
	from huge.testing import catch_fail

	with catch_fail() as out:
		run_command("merge", "abcdef")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	os.mkdir("folder")
	with open("folder/first_file.txt", "w") as f:
		f.write("Content")

	run_command("add", "folder")
	run_command("commit")

	# TODO merayen implement "checkout" to continue this path


@require_repository
def checkout_command(opts: argparse.Namespace) -> None:
	from huge import fail
	from huge.repo.commit import checkout_commit, checkout_files, WorkspaceHasChanges

	# TODO merayen make sure that we have all the files available in .huge/storage, or we may ask user to fetch them first

	if opts.files:
		checkout_files(opts.commit_hash, opts.files)
		return

	try:
		checkout_commit(opts.commit_hash)
	except WorkspaceHasChanges:
		fail("Workspace has changes. Aborted.")
		return


@huge_test
def test_checkout() -> None:
	from huge.testing import catch_fail, catch_output

	# TODO merayen check that all of the usages are tested
	with catch_fail() as out:
		run_command("checkout", "abcdef")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	os.mkdir("folder")
	with open("folder/first_file.txt", "w") as f:
		f.write("Content")

	with open("second_file.txt", "w") as f:
		f.write("Second file")

	run_command("add", "folder/first_file.txt", "second_file.txt", ".hugeignore")
	run_command("commit")

	with open(".huge/current") as f:
		first_revision = f.read()

	with open("folder/first_file.txt", "w") as f:
		f.write("Changed")

	with open("second_file.txt", "w") as f:
		f.write("Second file changed")

	# Make second commit
	run_command("add", "folder", "second_file.txt")
	run_command("commit")

	with open(".huge/current") as f:
		second_revision = f.read()

	# Workspace should be clean
	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == f"Commit: {second_revision}\n"

	# Check out the previous commit
	run_command("checkout", first_revision)

	# Verify that we actually moved to the first revision
	with open(".huge/current") as f:
		assert f.read() == first_revision

	# Verify that we got the old files
	with open("folder/first_file.txt") as f:
		assert f.read() == "Content"

	with open("second_file.txt") as f:
		assert f.read() == "Second file"

	# Now modify a file and make sure we won't allow any checkouts anymore
	with open("folder/first_file.txt", "w") as f:
		f.write("Changed again")

	with catch_fail() as out:
		run_command("checkout", second_revision)
		assert out.getvalue() == "Workspace has changes. Aborted.\n"

	# Manually make the file equal to to what it was in first and current revision
	with open("folder/first_file.txt", "w") as f:
		f.write("Content")

	# Should not emit anything, meaning workspace is clean
	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == f"Commit: {first_revision}\n"

	# Now check out the second file from the second revision
	run_command("checkout", second_revision, "folder/first_file.txt")

	# Make sure the file content is the one from second_revision
	with open("folder/first_file.txt") as f:
		assert f.read() == "Changed"

	# But the second file should not have been changed, should stay at checkout out revision
	with open("second_file.txt") as f:
		assert f.read() == "Second file"

	# Delete the folder instead
	os.remove("folder/first_file.txt")
	os.rmdir("folder")

	run_command("checkout", second_revision, "folder/first_file.txt")

	# Make sure the file content is the one from second_revision again
	with open("folder/first_file.txt") as f:
		assert f.read() == "Changed"


@huge_test
def test_add_removed_files() -> None:
	"""
	It should be possible to stage files removed from workspace
	"""
	import re
	import shutil
	from huge.testing import catch_output
	run_command("init")

	_create_test_file("a")
	_create_test_file("b")
	_create_test_file("c/d")
	_create_test_file("c/e")
	_create_test_file("f/g")

	run_command("add", "a", "b", "c", "f", ".hugeignore")

	with catch_output() as out:
		run_command("status")
		assert out.getvalue() == f"Staged for commit:\n  A .hugeignore\n  A a\n  A b\n  A c/d\n  A c/e\n  A f/g\n"

	run_command("commit")

	# Remove a file and a folder
	os.remove("a")
	shutil.rmtree("c")

	run_command("add", "a", "c", "f")

	with catch_output() as out:
		run_command("status")
		assert re.match("Commit: [0-9a-f]{32}\nStaged for commit:\n  D a\n  D c/d\n  D c/e\n", out.getvalue())


@huge_test
def test_checkout_removed_files() -> None:
	"""
	Files should automatically be removed if not existing in target commit
	"""
	import shutil
	from huge.testing import catch_output

	run_command("init")
	_create_test_file("a")
	_create_test_file("b/c/d", "bcd file")

	run_command("add", "a", "b", ".hugeignore")
	run_command("commit")

	os.remove("a")
	shutil.rmtree("b")

	run_command("add", "a", "b")
	run_command("commit")

	# Get commit hashes
	with catch_output() as out:
		run_command("log")
		second_commit, first_commit = [x.split()[0] for x in out.getvalue().strip().splitlines()]

	# Go back to first revision
	run_command("checkout", first_commit)

	# Ensure that we have the files back
	assert set(os.listdir()) == {"a", "b", ".huge", ".hugeignore"}
	assert _contains_contents("b/c/d", "bcd file")

	# Now go to second commit again, which removed some files
	run_command("checkout", second_commit)
	assert set(os.listdir()) == {".huge", ".hugeignore"}  # Files should be gone


@require_repository
def remote_add_command(opts: argparse.Namespace) -> None:
	from huge.repo.remote import add_remote

	add_remote(opts.remote)


@huge_test
def test_remote_add():
	from huge.testing import catch_error, catch_fail, catch_output, cd, temporary_repository

	with catch_fail() as out:
		run_command("remote-add", "another_huge_repo")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	# Verify that there are no remotes
	assert not os.listdir(".huge/remotes")

	run_command("remote-add", "another_huge_repo")

	# Verify that the remote was added
	remote, = os.listdir(".huge/remotes/")

	# Store the path of the "main" repository
	main_repo = os.path.abspath(os.getcwd())

	# We create the "remote" repository
	with (
		temporary_repository() as other_repo,
		catch_output() as out,
		catch_error() as err,
	):
		with cd(other_repo):
			# Clone the first repository we made
			run_command("clone", main_repo)

		assert out.getvalue().startswith("Fetching from ")
		assert err.getvalue() == "Invalid address: another_huge_repo. Skipped.\n"

		other_repo = os.path.join(other_repo, os.path.split(main_repo)[1])

		with cd(other_repo):
			assert len(os.listdir(".huge/remotes")) == 2

			# TODO merayen test that we actually added the remote repository to our list



def clone_command(opts: argparse.Namespace) -> None:
	from huge import fail
	from huge.repo import is_repository
	from huge.repo.clone import clone_repository, InvalidRepositoryAddress

	if is_repository():
		fail("Huge already initialized")
		return

	try:
		clone_repository(opts.remote)
	except InvalidRepositoryAddress:
		fail(f"Invalid remote: {opts.remote}. Skipped.")
		return


@huge_test
def test_clone():
	import re
	from huge.testing import catch_error, catch_fail, catch_output, cd, temporary_repository

	def get_remotes():
		for remote_hash in os.listdir(".huge/remotes"):
			with open(f".huge/remotes/{remote_hash}/address") as f:
				yield f.read()

	# Create and add a file and some history to the remote repo
	run_command("init")

	# Make sure that it isn't possible to clone into an existing repository
	with catch_fail() as out:
		run_command("clone", "something")
		assert out.getvalue() == "Huge already initialized\n"

	os.mkdir("folder")
	with open("folder/first_file.txt", "w") as f:
		f.write("Content")

	run_command("add", "folder")
	run_command("commit", "--message", "First commit")

	with open("folder/first_file.txt", "w") as f:
		f.write("ContentChanged")

	run_command("add", "folder")
	run_command("commit", "--message", "Second commit")

	# Add fake remote
	run_command("remote-add", "doesntexist")

	# Get the remotes
	main_repo_remotes = list(get_remotes())

	# Store the main repository's address
	main_repo = os.path.abspath(os.getcwd())

	# Create the "local" repository
	with temporary_repository() as other_repo:
		with temporary_repository() as invalid_repo, cd(other_repo):
			with catch_fail() as out:
				run_command("clone", invalid_repo)
				assert out.getvalue() == f"Invalid remote: {invalid_repo}. Skipped.\n"

		with catch_output() as out, catch_error() as err, cd(other_repo):
			run_command("clone", main_repo)
			assert re.match("Fetching from .*\nFetching from .*\n$", out.getvalue())
			assert err.getvalue() == "Invalid address: doesntexist. Skipped.\n"

		other_repo = os.path.join(other_repo, os.path.split(main_repo)[1])

		with cd(other_repo):
			# Verify that we got the contents of main repository
			assert os.path.isdir(".huge")

			assert os.path.isfile(".huge/current")

			# Verify that no commit is checked out yet
			with open(".huge/current") as f:
				assert not f.read()

			# Verify that the logs looks okay
			with catch_output() as out:
				run_command("log")
				assert re.match(
					"[0-9a-f]{32} \\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d 0%/100% Second commit\n"
					"[0-9a-f]{32} \\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d 0%/100% First commit\n",
					out.getvalue()
				)

			# Verify that we inherited the remotes from the remote
			# TODO merayen verify that we added the remote we cloned from to our own remote list
			assert len(list(get_remotes())) - 1 == len(main_repo_remotes)


@require_repository
def send_command(opts: argparse.Namespace) -> None:
	from huge.repo.send import send_repository

	send_repository(opts.remote)


@huge_test
def test_send():
	import re
	from huge.testing import catch_fail, catch_output, temporary_repository

	with temporary_repository() as remote_repo:
		remote_repo = os.path.join(remote_repo, "huge")

		with catch_fail() as out:
			run_command("send", remote_repo)
			assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

		run_command("init")

		with open("first_file.txt", "w") as f:
			f.write("Content")

		run_command("add", "first_file.txt", ".hugeignore")
		run_command("commit")

		assert len(os.listdir(".huge/storage")) == 2

		# Send the repository metadata, but no commit files
		with catch_output() as out:
			run_command("send", remote_repo)
			assert out.getvalue().startswith(f"Fetching from {remote_repo}")

		# TODO merayen verify that we added the new remote as a remote on our side
		for x in os.listdir(".huge/remotes"):
			with open(f".huge/remotes/{x}/address") as f:
				if f.read().strip() == remote_repo:
					break  # All good
		else:
			assert 0, "Expected to find sent repository as a remote on our side"

		# Push the current commit files
		with catch_output() as out:
			run_command("push")
			assert out.getvalue().startswith(f"Fetching from {remote_repo}")

		# TODO merayen verify that the files are stored in the remote repository, in .huge/storage
		assert (
			set(os.listdir(".huge/storage"))
			==
			set(os.listdir(os.path.join(remote_repo, ".huge/storage")))
		)

		with catch_output() as out:
			run_command("log")

			# Check that replication statistics are updated and correct
			assert re.match("[0-9a-f]{32} [0-9-]{10} [0-9:]{5} 100%/200%\n$", out.getvalue())


@require_repository
def fetch_command(opts: argparse.Namespace):
	from huge.repo.fetch import fetch_repositories

	fetch_repositories()


@huge_test
def test_fetch():
	import re
	from huge.testing import catch_fail, catch_output, cd, temporary_repository

	with catch_fail() as out:
		run_command("fetch")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	os.mkdir("folder")
	with open("folder/first_file.txt", "w") as f:
		f.write("Content")

	run_command("add", "folder")
	run_command("commit")

	main_repo = os.path.abspath(os.getcwd())

	with temporary_repository() as other_repo:
		with cd(other_repo), catch_output() as out:
			run_command("clone", main_repo)
			assert re.match("Fetching from .*\n$", out.getvalue())

		other_repo = os.path.join(other_repo, os.path.split(main_repo)[1])

		# Create a new commit in the main repo
		with open("folder/first_file.txt", "w") as f:
			f.write("ContentChanged")

		run_command("add", "folder")
		run_command("commit")

		# Get the logs for the main repo
		with catch_output() as out:
			run_command("log")
			main_repo_logs = out.getvalue()

		with cd(other_repo):
			# Make sure that we have the first commit, but none of the files pulled yet (therefore 0%)
			with catch_output() as out:
				run_command("log")
				assert out.getvalue() == " ".join(main_repo_logs.splitlines()[1].split()[:-1]) + " 0%/100%\n"

			# Now we fetch the metadata for the second commit
			with catch_output() as out:
				run_command("fetch")
				assert re.match("^Fetching from .*\n$", out.getvalue())

			# Now the logs should be the same, but with 0%
			with catch_output() as out:
				run_command("log")
				assert out.getvalue() == "\n".join(
					" ".join(x.split()[:-1]) + " 0%/100%"  # 0% because fetching does not retrieve files
					for x in main_repo_logs.splitlines()
				) + "\n"

		# TODO merayen check that coverage information is put into .huge/remotes/coverage


@require_repository
def push_command(opts: argparse.Namespace) -> None:
	from huge import fail
	from huge.repo.commit import get_current_commit
	from huge.repo.fetch import fetch_repositories
	from huge.repo.push import push_commit
	from huge.repo.remote import get_remotes

	# Synchronize with all the remotes first.
	# This is not perfect as remotes might be unavailable under fetching.
	# If that is the case, user needs to run "huge fetch" later on to make commits
	# visible on the remote repositories that was previously unavailable.
	fetch_repositories()

	commit_hash = get_current_commit()

	if not opts.commit_hash and not commit_hash:
		fail("Nothing to push")
		return

	remotes = opts.remote or get_remotes()

	if not remotes:
		fail("No remotes found")
		return

	push_commit(
		commits=opts.commit_hash or [commit_hash],
		remotes=remotes,
	)


@huge_test
def test_push():
	import re
	from huge.testing import catch_fail, catch_output, cd, temporary_repository

	with catch_fail() as out:
		run_command("push")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	with catch_fail() as out:
		run_command("push")
		assert out.getvalue() == "Nothing to push\n"

	main_repo = os.path.abspath(os.getcwd())

	# Create another repository and clone the main one
	with temporary_repository() as other_repo:
		with cd(other_repo):
			# Clone into other_repo
			with catch_output() as out:
				run_command("clone", main_repo)
				assert out.getvalue().startswith("Fetching from ")

		other_repo = os.path.join(other_repo, os.path.split(main_repo)[1])

		with cd(other_repo):
			# Create two test commits
			# TODO merayen maybe also test with two files in first commit, change one of the files in second commit, to see that the coverage is 50% on the second commit
			os.mkdir("folder")

			with open("folder/first_file.txt", "w") as f:
				f.write("ContentFirst")

			with open("folder/second_file.txt", "w") as f:
				f.write("ContentSecond")

			run_command("add", "folder")
			run_command("commit")

			# Now only change one of the files in the next commit
			with open("folder/second_file.txt", "w") as f:
				f.write("ContentChanged")

			run_command("add", "folder")
			run_command("commit")

			# Retrieve the logs of the two commits
			with catch_output() as out:
				run_command("log")
				other_repo_logs = out.getvalue()
				assert len(other_repo_logs.strip().splitlines()) == 2, "Expected two commits"

			# Verify that we have two commits in this repo
			with catch_output() as out:
				run_command("log")
				# TODO merayen maybe we should make total_coverage to remote_coverage in the log command output
				assert re.match(
					"[0-9a-f]{32} \\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d 100%/100%\n"
					"[0-9a-f]{32} \\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d 100%/100%\n$",
					out.getvalue(),
				)

			# Push the current commit, which is the second commit
			with catch_output() as out:
				run_command("push")
				assert re.match("Fetching from .*\nPushing files to .*", out.getvalue())

		# Verify that the repository that has been pushed to has received the commit metadata and all
		# the actual files for that commit. Since the first commit shares a file with the second commit,
		# the first commit should automatically have 50% coverage.
		with catch_output() as out:
			run_command("log")
			# TODO merayen verify if the coverage numbers are correct
			assert re.match(
				"[0-9a-f]{32} \\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d 100%/100%\n"  # Whole second commit was pushed
				"[0-9a-f]{32} \\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d 50%/50%\n",  # 50% leaks into first commit
				out.getvalue(),
			)


@require_repository
def pull_command(opts: argparse.Namespace) -> None:
	from huge.repo.remote import get_remotes
	from huge.repo.pull import pull_commit

	pull_commit(commits=opts.commit_hash, remotes=opts.remote or get_remotes())


@huge_test
def test_pull():
	import re
	from huge.testing import catch_fail, catch_output, cd, temporary_repository

	with catch_fail() as out:
		run_command("pull", "123")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	main_repo = os.path.abspath(os.getcwd())

	with temporary_repository() as other_repo:
		with cd(other_repo), catch_output() as out:
			run_command("clone", main_repo)
			assert re.match("Fetching from .*\n$", out.getvalue())

		other_repo = os.path.join(other_repo, os.path.split(main_repo)[1])

		with open("first_file.txt", "w") as f:
			f.write("Content")

		with open("second_file.txt", "w") as f:
			f.write("Content2")

		run_command("add", "first_file.txt", "second_file.txt")

		run_command("commit")

		with cd(other_repo):
			with catch_output() as out:
				run_command("fetch")
				assert re.match("Fetching from .*\n$", out.getvalue())

			with catch_output() as out:
				run_command("log")
				commit_hash = out.getvalue()[:32]

			# Now try to checkout the commit, but we don't have the data yet
			with catch_fail() as out:
				run_command("checkout", commit_hash)

				assert re.match(
					"^ERROR: Missing one or more files locally.\n\n"
					"Try:\n"
					f"  huge pull {commit_hash}\n\n"
					"...which will try to retrieve the data from any of the known remotes.\n$",
					out.getvalue(),
				)

			assert not os.path.exists("first_file.txt")

			# So now we get the actual commit data
			with catch_output() as out:
				run_command("pull", commit_hash)
				assert out.getvalue() == f"Pulling files from {main_repo}\n"

			# Now we can do the checkout again
			run_command("checkout", commit_hash)

			with open("first_file.txt") as f:
				assert f.read() == "Content"


@huge_test
def test_ignore_files():
	from huge.testing import catch_fail, catch_output

	with catch_output() as out:
		run_command("init")

		with open("first_file.txt", "w") as f:
			f.write("Content")

		with open("second_file.txt", "w") as f:
			f.write("Content2")

		with open(".hugeignore", "w") as f:
			f.write(".*second.*\n")

	run_command("add", "first_file.txt", ".hugeignore", "second_file.txt")

	with catch_output() as out:
		run_command("status")

		# Assert that second_file.txt is now ignored
		assert out.getvalue() == "Staged for commit:\n  A .hugeignore\n  A first_file.txt\n"

	run_command("commit")

	# Make sure only two of the files got stored
	assert len(os.listdir(".huge/storage")) == 2

	with catch_output() as out:
		run_command("log")
		commit_hash = out.getvalue().splitlines()[0].split()[0]

	os.remove("first_file.txt")
	os.remove("second_file.txt")

	# Check out the file stored
	run_command("checkout", commit_hash, "first_file.txt")

	with open("first_file.txt") as f:
		assert f.read() == "Content"

	with catch_fail() as out:
		run_command("checkout", commit_hash, "second_file.txt")
		assert out.getvalue() == "Files not found in commit:\n  second_file.txt\n"


@require_repository
def drop_command(opts: argparse.Namespace) -> None:
	from huge import fail
	from huge.repo.commit import get_commit_infos
	from huge.repo.drop import drop_commit_files, get_removable_files, get_removable_commits
	from huge.repo.fetch import fetch_repositories

	if not opts.force:
		fetch_repositories()
		commit_infos = get_commit_infos()
		removable_commits = get_removable_commits(opts.commit_hash, commit_infos)
		dropable = get_removable_files(opts.commit_hash, commit_infos)

		# TODO merayen rather allow dropping commits, but skip those with coverage < 200%
		if set(dropable) != set(opts.commit_hash):
			fail(
				"The total coverage of the commits are less than 200%, meaning we could loose data.\n"
				"If you really want to continue, run the command with --force."
			)
			return

	# TODO merayen we should probably in some way lock the remote repositories for changes when dropping

	drop_commit_files(opts.commit_hash)

	# TODO merayen should we do a fetch afterwards, and tell other repos about our coverage status that has us as our remote?


@huge_test
def test_drop() -> None:
	from huge.testing import catch_fail, catch_output

	with catch_fail() as out:
		run_command("drop", "invalid")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	# TODO merayen test that only the files in the commit not used by others are dropped

	run_command("init")

	# Create two commits adding each their own file
	with open("first_file.txt", "w") as f:
		f.write("Content")

	run_command("add", "first_file.txt")
	run_command("commit")

	with open("second_file.txt", "w") as f:
		f.write("Content2")

	run_command("add", "second_file.txt")
	run_command("commit")

	with catch_output() as out:
		run_command("log")
		repo_commits = [x[:32] for x in out.getvalue().strip().splitlines()]

	# Now drop the second commit, which fails because no one has a copy
	with catch_fail() as out:
		run_command("drop", repo_commits[0])
		assert out.getvalue() == (
			"The total coverage of the commits are less than 200%, meaning we could loose data.\n"
			"If you really want to continue, run the command with --force.\n"
		)

	# TODO merayen 'huge send' the repository and push the second commit and try drop again
	# TODO merayen await implementation of 'huge send'


@require_repository
def remotes_command(opts: argparse.Namespace) -> None:
	from huge import output
	from huge.repo.remote import get_remotes

	for remote in get_remotes():
		output(
			" ".join(
				[
					remote.remote_hash,
					(
						remote.last_coverage_update and remote.last_coverage_update.strftime("%Y-%m-%d %H:%M")
						or " " * 16
					),
					remote.address,
				]
			)
		)


@huge_test
def test_remotes():
	import re
	from huge.testing import catch_fail, catch_output, cd, temporary_repository

	with catch_fail() as out:
		run_command("remotes")
		assert out.getvalue() == "Not a .huge repository, or you are not in the root level of it\n"

	run_command("init")

	main_repo = os.path.abspath(os.getcwd())

	# Still no output expected
	run_command("remotes")

	# TODO merayen rename or use tempfile.TemporaryDirectory directly. Doesn't make so much sense anymore
	with temporary_repository() as other_repo:
		with catch_output() as out, cd(other_repo):
			run_command("clone", main_repo)
			assert out.getvalue().startswith("Fetching from ")

		with cd(os.path.join(other_repo, os.path.split(main_repo)[1])):
			remote_hash, = os.listdir(".huge/remotes")

			# Verify that we output correctly
			with catch_output() as out:
				run_command("remotes")
				assert re.match(
					f"{remote_hash} \\d{{4}}-\\d\\d-\\d\\d \\d\\d:\\d\\d {main_repo}\n",
					out.getvalue(),
				)


@require_repository
def add_command(opts: argparse.Namespace) -> None:
	from huge.repo.stage import mark_as_staged

	mark_as_staged(opts.file)


@huge_test
def test_add() -> None:
	run_command("init")

	text_file = _create_test_file()
	other_text_file = _create_test_file("folder/other_file.txt")

	assert not os.path.isfile(".huge/stage")

	run_command("add", "my_file.txt", "folder/other_file.txt")

	with open(".huge/stage") as f:
		assert {x.strip() for x in f.read().splitlines()} == {"my_file.txt", "folder/other_file.txt"}

	run_command("reset", ".")

	assert not os.path.isfile(".huge/stage")

	# Only add single file, but via folder
	run_command("add", "folder")

	with open(".huge/stage") as f:
		# Only the path to the file in the folder should be added to stage file.
		# We don't support folders themselves.
		assert f.read() == "folder/other_file.txt\n"

	_create_test_file("ignored_folder/file.txt")

	_create_ignore_file(["ignored_folder"])

	run_command("add", "ignored_folder")
	run_command("add", "ignored_folder/file.txt")

	with open(".huge/stage") as f:
		# Make sure that we respected .hugeignore and didn't add anymore files
		assert f.read() == "folder/other_file.txt\n"

	# TODO merayen think about making committing not using .hugeignore, but rather only when staging files


@require_repository
def reset_command(opts: argparse.Namespace) -> None:
	from huge.repo.stage import unmark_as_staged

	unmark_as_staged(opts.file)


@huge_test
def test_reset() -> None:
	run_command("init")

	text_file = _create_test_file()

	run_command("add", text_file)

	assert os.path.isfile(".huge/stage")

	run_command("reset", text_file)

	assert not os.path.isfile(".huge/stage")


def _create_test_file(path: str = "my_file.txt", text: str = "Content") -> str:
	import pathlib

	path_root = os.path.split(path)[0]
	if path_root and not os.path.exists(path_root):
		pathlib.Path(path_root).mkdir(parents=True, exist_ok=True)

	with open(path, "w") as f:
		f.write(text)

	return path


def _create_ignore_file(paths: list[str]) -> None:
	with open(".hugeignore", "w") as f:
		f.write("\n".join(paths) + "\n")


def _contains_contents(path: str, content: str) -> bool:
	if not os.path.isfile(path):
		return False

	with open(path) as f:
		return f.read() == content


if __name__ == '__main__':
	for x in dir():
		if x.startswith("test_"):
			exec(f"{x}()")
