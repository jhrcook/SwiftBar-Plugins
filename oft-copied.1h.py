#!/Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

"""Easy access to oft copied text."""

# <bitbar.title>Oft Copied Text</bitbar.title>
# <bitbar.version>v1.0.0</bitbar.version>
# <bitbar.author>Joshua Cook</bitbar.author>
# <bitbar.author.github>jhrcook</bitbar.author.github>
# <bitbar.desc>Easy access to text I often copy from some source.</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

import os
import subprocess
import sys
from pathlib import Path
from typing import Final, Optional

import typer

# --- Setup ---


app = typer.Typer()

if (plugin_path := os.getenv("SWIFTBAR_PLUGIN_PATH")) is not None:
    self_path = Path(plugin_path)
else:
    self_path = Path(sys.argv[0])


# --- Copyable text ---


COPY_TEXT_INFO: Final[dict[str, str]] = {
    "IPython autoreload": "%load_ext autoreload\n%autoreload 2",
    "Pystan in Jupyter": "import nest_asyncio\nnest_asyncio.apply()",
    "matplotlib retina": "%matplotlib inline\n%config InlineBackend.figure_format='retina'",  # noqa: E501
}


# --- SwiftBar ---


def _header() -> None:
    print(":text.bubble: | symbolize=True")
    print("---")
    print("Click to copy to clipboard")
    print("---")
    return None


def _format_copyable(title: str, text: str) -> str:
    out = f"{title} | bash={self_path} param0='--to-copy={title}'"
    text = text.replace("\n", "\\\\n")
    out += f" tooltip='{text}'"
    out += " refresh=true terminal=false"
    return out


def _copyables() -> None:
    for title, text in COPY_TEXT_INFO.items():
        print(_format_copyable(title, text))
    return None


def _refresh() -> None:
    print("---")
    print(":arrow.clockwise: Refresh | symbolize=true refresh=true terminal=false")
    return None


def _edit() -> None:
    out = ":pencil.tip.crop.circle: Edit... | symbolize=true"
    out += f" bash='mate' param0='{str(plugin_path)}'"
    out += " refresh=true terminal=false"
    print(out)
    return None


def swiftbar_app() -> None:
    """Print to standard out the data for the SwiftBar application."""
    _header()
    _copyables()
    _refresh()
    _edit()
    return None


# --- Adding text to Pasteboard ---


def copy_text(title: str) -> None:
    """Copy desired text to pasteboard.

    Args:
        title (str): Title of the copyable text in the look-up table.
    """
    text = COPY_TEXT_INFO[title]
    p1 = subprocess.Popen(["echo", text], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["pbcopy"], stdin=p1.stdout)
    if p1.stdout is not None:
        p1.stdout.close()
    if p2.stdin is not None:
        p2.stdin.close()
    return None


# --- Main ---


@app.command()
def main(to_copy: Optional[str] = None) -> None:
    """Primary entry point for the SwiftBar application.

    This function handles the possible input and runs the appropriate method:

    - If there is no input, then the SwiftBar application information needs to be
      presented for SwiftBar.
    - If a string is provided, then the corresponding text needs to be added to the
      pasteboard.

    Args:
        to_copy (Optional[str], optional): Title of the text to copy. Defaults to None.
    """
    if to_copy is not None:
        copy_text(to_copy)
    else:
        swiftbar_app()
    return None


if __name__ == "__main__":
    app()
