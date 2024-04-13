"""
The methods here are mostly here to be patchable for unit testing

Route all output via these fail() and output() methods.
"""

__version__ = (0,1,0)

def fail(message: str) -> None:
	import sys
	print(message, file=sys.stderr)
	exit(1)


def error(message: str) -> None:
	import sys
	print(f"\033[31mERROR:\033[0m {message}", file=sys.stderr)


def output(message: str) -> None:
	print(message)
