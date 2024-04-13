import os
import re
from contextlib import contextmanager
from typing import Callable


def huge_test(func: Callable[[], None]) -> Callable[[], None]:
	"""
	Creates a temporary directory and cd into it, patching huge.fail and huge.output()

	Usage:
		@huge_test
		def test_my_test():
			...
	"""
	import pytest
	from unittest.mock import patch

	def decorator() -> None:
		with (
			temporary_repository() as d,
			patch(
				"huge.fail",
				new=lambda *a,**b: pytest.fail(f"fail() was not expected here: {a, b}"),
			),
			patch(
				"huge.error",
				new=lambda *a,**b: pytest.fail(f"error() was not expected here: {a, b}"),
			),
			patch(
				"huge.output",
				new=lambda *a,**b: pytest.fail(f"output() was not expected here: {a, b}"),
			),
		):
			old = os.path.abspath(os.getcwd())
			os.chdir(d)
			try:
				func()
			finally:
				os.chdir(old)

	return decorator


@contextmanager
def temporary_repository():
	import tempfile

	with tempfile.TemporaryDirectory() as d:
		yield d


@contextmanager
def cd(path):
	old = os.path.abspath(os.getcwd())

	os.chdir(path)
	try:
		yield
	finally:
		os.chdir(old)


def catch_fail():
	return _assert_emission("huge.fail")


def catch_error():
	return _assert_emission("huge.error")


def catch_output():
	return _assert_emission("huge.output")


@contextmanager
def _assert_emission(method: str):
	from io import StringIO
	from unittest.mock import patch

	string = StringIO()

	with patch(method, new=lambda x: string.write(x + "\n")):
		yield string


def test_assert_emission_str() -> None:
	with catch_output() as out:
		from huge import output
		output("test")
		assert out.getvalue() == "test\n"


def test_assert_emission_regex() -> None:
	with catch_output() as out:
		from huge import output
		output("68b329da9893e34099c7d8ad5cb9c940 2024-01-02 13:37 42%")
		re.match(
			"[0-9a-f]{32} \\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2} \\d\\d?\\d?%",
			out.getvalue(),
		)


if __name__ == '__main__':
	for x in dir():
		if x.startswith("test_"):
			exec(f"{x}()")
