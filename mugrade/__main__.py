import mugrade
import sys
import os
import pytest
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run mugrade')
    parser.add_argument("operation", nargs=1, choices = ["submit", "publish"],
        help = "operation: 'submit' or 'publish'")
    parser.add_argument("key", nargs=1, help = "Your mugrade grader key")
    parser.add_argument("hw", nargs=1, help = "Homework name")
    parser.add_argument("--server", dest="server", default=None,
                        help="Server base URL (default https://api.mugrade.org/)")
    args, pytest_args = parser.parse_known_args()
    os.environ["MUGRADE_KEY"] = args.key[0]
    os.environ["MUGRADE_OP"] = args.operation[0]
    os.environ["MUGRADE_HW"] = args.hw[0]
    # Optionally override the default server URL
    if args.server is not None:
        server = args.server if args.server.endswith('/') else args.server + '/'
        os.environ["MUGRADE_SERVER"] = server
    print(os.environ["MUGRADE_OP"])
    # Suppress pytest warnings in output for cleaner grader logs
    pytest.main(pytest_args + ["-s", "--disable-warnings", "-o", "python_functions='submit_*'"], plugins=[mugrade])
    return 0

if __name__ == "__main__":
    sys.exit(main())
