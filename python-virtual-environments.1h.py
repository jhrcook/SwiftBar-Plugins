#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# <bitbar.title>Display Conda Virtual Environments</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Joshua Cook</bitbar.author>
# <bitbar.author.github>jhrcook</bitbar.author.github>
# <bitbar.desc>List the conda virtual environments and copy to clipboard when clicked..</bitbar.desc>
# <bitbar.image>https://docs.conda.io/en/latest/_images/conda_logo.svg</bitbar.image>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>


import subprocess
import sys
from pathlib import Path

self_path = Path(sys.argv[0])


def print_environments():
    """Print the environments to standard output."""

    print("🅒")  # print("🐍 | emojize=true")

    print("---")

    print("Click to copy to clipboard")

    conda_envs = subprocess.run(["conda", "env", "list"], stdout=subprocess.PIPE)
    conda_envs = conda_envs.stdout.decode("utf-8")
    conda_envs = conda_envs.split("\n")
    for conda_env in conda_envs:
        if not "#" in conda_env and conda_env != "":
            env = conda_env.strip().split(" ")[0]
            env = Path(env).name
            if env != "base":
                print(
                    f"{env} | bash={self_path.as_posix()} param1={env} refresh=true terminal=false"
                )

    print("---")

    print("Refresh | refresh=true")


def copy_env_to_clipboard(env):
    """Copy an environment name to clipboard."""
    p1 = subprocess.Popen(["echo", env], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["pbcopy"], stdin=p1.stdout)
    p1.stdout.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        copy_env_to_clipboard(env=sys.argv[1])
    else:
        print_environments()
