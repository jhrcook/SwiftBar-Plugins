#!/Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

"""SwiftBar plugin to show all conda environments and copy to clipboard."""

# <bitbar.title>Display Conda Virtual Environments</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Joshua Cook</bitbar.author>
# <bitbar.author.github>jhrcook</bitbar.author.github>
# <bitbar.desc>List the conda virtual environments and copy to clipboard.</bitbar.desc>
# <bitbar.image>https://docs.conda.io/en/latest/_images/conda_logo.svg</bitbar.image>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>


import subprocess
import sys
from pathlib import Path

self_path = Path(sys.argv[0])


def _header() -> None:
    print(":c.circle: | symbolize=true")
    print("---")
    print("Click to copy to clipboard")
    return None


def print_environments() -> None:
    """Print the environments to standard output."""
    _header()
    conda_envs_subp = subprocess.run(["conda", "env", "list"], stdout=subprocess.PIPE)
    conda_envs = conda_envs_subp.stdout.decode("utf-8").split("\n")
    for conda_env in conda_envs:
        if "#" not in conda_env and conda_env != "":
            env = conda_env.strip().split(" ")[0]
            env = Path(env).name
            if env != "base":
                msg = f"{env} | bash={self_path.as_posix()} param1={env}"
                msg += " refresh=true terminal=false"
                print(msg)

    print("---")
    print("Refresh | refresh=true")
    return None


def copy_env_to_clipboard(env: str) -> None:
    """Copy an environment name to clipboard."""
    p1 = subprocess.Popen(["echo", env], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["pbcopy"], stdin=p1.stdout)
    if p1.stdout is not None:
        p1.stdout.close()
    if p2.stdin is not None:
        p2.stdin.close()
    return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        copy_env_to_clipboard(env=sys.argv[1])
    else:
        print_environments()
