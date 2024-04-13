"""
File and directory path constants
"""
import os

# The special directory where huge's data is stored
HUGE_DIRECTORY = ".huge"

# Textfile containing regular expressions that exclude files
IGNORE_FILE = ".hugeignore"

# The current commit the user is working from
CURRENT_COMMIT_FILE = os.path.join(HUGE_DIRECTORY, "current")

# A file containing a list of all the files that are stored in this commit
# The actual files defined in FILES_DIRECTORY.
COMMITS_DIRECTORY = os.path.join(HUGE_DIRECTORY, "commits")

# Where all the actual files are stored.
# Files inside are stored with their checksum as the filename.
FILES_DIRECTORY = os.path.join(HUGE_DIRECTORY, "storage")

# The unique identifier
# It is used to block pushing or pulling from two different repositories.
REPO_ID_FILE = os.path.join(HUGE_DIRECTORY, "id")

# Information about other repositories we pull and push data to
REMOTES_FOLDER = os.path.join(HUGE_DIRECTORY, "remotes")

# Local information on current staged files
STAGED_FILE = os.path.join(HUGE_DIRECTORY, "stage")
