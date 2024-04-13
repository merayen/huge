if __name__ == '__main__':
	import sys
	from .cli import execute_cli_command
	execute_cli_command(sys.argv[1:])
