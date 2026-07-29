import subprocess
import sys


def main():
    args = sys.argv[1:]
    result = subprocess.run(["git"] + args, check=False)

    if result.returncode == 0:
        if "commit" in args:
            print("post-commit: done")
        elif "push" in args:
            print("post-push: done")

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
