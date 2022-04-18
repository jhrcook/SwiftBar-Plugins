#!/Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

"""Quick access to TaskWarrior tasks."""

# <bitbar.title>TaskWarrior</bitbar.title>
# <bitbar.version>v1.0.0</bitbar.version>
# <bitbar.author>Joshua Cook</bitbar.author>
# <bitbar.author.github>jhrcook</bitbar.author.github>
# <bitbar.desc>TaskWarrior task lists.</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>
# <swiftbar.refreshOnOpen>true</swiftbar.refreshOnOpen>

import argparse
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Final, Optional
from uuid import UUID

from pydantic import BaseModel
from taskw import TaskWarrior

# --- Setup ---


def _mod_taskrc_file() -> str:
    return str(Path(__file__).parent / ".mod-taskrc")


tw = TaskWarrior(config_filename=_mod_taskrc_file(), marshal=True)

FILE = str(Path(__file__))

PROJECT_NAMES: Final[dict[str, str]] = {
    "speclet": ":laptopcomputer: speclet",
    "bluishred": ":laptopcomputer: bluishred",
    "katsaros": ":laptopcomputer: katsaros",
    "home": ":house.fill: home",
    "lab": ":briefcase: lab",
    "none": ":command: general",
}


# --- Classes ---


class TaskStatus(Enum):
    """TaskWarrior status."""

    pending = "pending"
    completed = "completed"


class TaskPriority(Enum):
    """TaskWarrior priority."""

    L = "L"
    M = "M"
    H = "H"


class Task(BaseModel):
    """TaskWarrior task."""

    description: str
    project: str = "none"
    entry: datetime
    id: int
    modified: datetime
    priority: Optional[TaskPriority] = None
    status: TaskStatus
    start: Optional[datetime] = None
    urgency: float
    uuid: UUID


class Tasks:
    """TaskWarrior tasks."""

    tasks: list[Task]

    def __init__(self) -> None:
        """Initialize a TaskWarrior tasks object."""
        self.tasks = self._retrieve_tasks()
        return None

    def _retrieve_tasks(self) -> list[Task]:
        return [Task(**t) for t in tw.load_tasks()["pending"]]

    def sort_by_urgency(self) -> None:
        """Sort tasks by urgency."""
        self.tasks.sort(key=lambda t: -t.urgency)
        return None

    def per_project(self) -> dict[str, list[Task]]:
        """Organize tasks by project."""
        projects: list[str] = [t.project for t in self.tasks if t.project != "none"]
        projects = list(set(projects))
        projects.sort()
        projects.append("none")
        proj_tasks: dict[str, list[Task]] = {}
        for project in projects:
            proj_task = [t for t in self.tasks if t.project == project]
            proj_tasks[project] = proj_task
        return proj_tasks


class CLICommand(Enum):
    """Available commands through the CLI."""

    SWIFTBAR = "SWIFTBAR"
    COMPLETED = "COMPLETED"
    ACTIVE = "ACTIVE"


class CLIArguments(BaseModel):
    """CLI result."""

    command: CLICommand
    id: int


# --- SwiftBar ---


def menu_bar_icon() -> None:
    """Print SwiftBar menu icon."""
    icon = ":list.bullet.circle:"
    color = "purple"
    extras = "dropdown=False tooltip='TextWarrior'"
    print(f"{icon} | symbolize=True sfcolor={color} {extras}")
    print("---")


def _task_command_string(task: Task) -> str:
    task_desc = "  " + task.description + " | "
    msg = task_desc
    if task.start is not None:
        msg += "color=#fc9cc7 "
    cmd1 = f"--command={CLICommand.COMPLETED.value}"
    cmd2 = f"--id={task.id}"
    msg += f"bash={FILE} param0='{cmd1}' param1='{cmd2}' terminal=false "
    msg += "trim=false"

    alt_msg = task_desc
    cmd1 = f"--command={CLICommand.ACTIVE.value}"
    alt_msg += f"bash={FILE} param0='{cmd1}' param1='{cmd2}' terminal=false "
    alt_msg += "alternate=true color=#A3AAFF "
    alt_msg += "trim=false"
    msg += "\n" + alt_msg

    return msg


def _modify_project_name(project: str) -> str:
    return PROJECT_NAMES.get(project, project)


def list_tasks_by_project() -> None:
    """Print tasks organized by project for SwiftBar dropdown."""
    tasks = Tasks()
    tasks.sort_by_urgency()
    for project, proj_tasks in tasks.per_project().items():
        proj_name = _modify_project_name(project)
        print(proj_name + " |  sfcolor=gray")
        for task in proj_tasks:
            print(_task_command_string(task))
        print("---")

    return None


def swiftbar_app() -> None:
    """Run SwiftBar app."""
    menu_bar_icon()
    list_tasks_by_project()
    return None


# --- Complete task ---


def complate_task(id: int) -> None:
    """Mark a task completed."""
    tw.task_done(id=id)
    return None


# --- Active task ---


def start_task(id: int) -> None:
    """Mark a task started."""
    tw.task_start(id=id)
    return None


# --- Main ---


def parse_arguments() -> CLIArguments:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--command",
        help="primary command",
        type=CLICommand,
        default=CLICommand.SWIFTBAR,
    )
    parser.add_argument("-i", "--id", help="task ID", type=int, default=-1)
    args = parser.parse_args()
    return CLIArguments(command=args.command, id=args.id)


def main() -> None:
    """Main."""
    args = parse_arguments()
    if args.command is CLICommand.SWIFTBAR:
        swiftbar_app()
        return None
    elif args.command is CLICommand.COMPLETED:
        complate_task(args.id)
    elif args.command is CLICommand.ACTIVE:
        start_task(args.id)
    else:
        raise NotImplementedError(f"Unexpected command: '{args.command.value}'")


if __name__ == "__main__":
    main()
