#!//Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

# <bitbar.title>Coffee Tracker Plugin</bitbar.title>
# <bitbar.version>v1.0.0</bitbar.version>
# <bitbar.author>Joshua Cook</bitbar.author>
# <bitbar.author.github>jhrcook</bitbar.author.github>
# <bitbar.desc>Logging of cups of coffee with my Coffee Tracker API.</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

import os
import sys
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

import keyring
import requests
import typer
from pydantic import BaseModel
from typer.params import Option

self_path = Path(sys.argv[0])

api_url = "https://a7a9ck.deta.dev/"

app = typer.Typer()


class CLICommands(str, Enum):
    deactivate_bag = "deactivate_bag"
    use_bag = "use_bag"
    new_bag = "new_bag"
    profile = "profile"


def get_api_password() -> Optional[str]:
    """Get my password for the API.

    Returns:
        Optional[str]: The password, if one is found.
    """
    return keyring.get_password("swiftbar_coffee-tracker", "Joshua Cook")


class CoffeeBag(BaseModel):
    brand: str
    name: str
    weight: float
    start: date
    key: str

    def __str__(self) -> str:
        return self.brand + " - " + self.name


class CoffeeUse(BaseModel):
    bag_id: str
    datetime: datetime
    key: str


#### ---- Date and Datetime Formatting ---- ####


def date_format() -> str:
    return "%Y-%m-%d"


def datetime_format() -> str:
    return date_format() + "T%H:%M:%S"


def get_today_formatted_datetime() -> str:
    t = datetime.combine(date.today(), datetime.min.time())
    return t.strftime(datetime_format())


def get_now_formatted_datetime() -> str:
    return datetime.now().strftime(datetime_format())


def get_today_formatted_date() -> str:
    return date.today().strftime(date_format())


#### ---- Notifications ---- ####


def notify(title: str, subtitle: str, text: str) -> None:
    cmd = f'osascript -e \'display notification "{text}" with title "{title}" subtitle "{subtitle}" \''
    os.system(cmd)


def notify_failed_request(res: requests.Response, subtitle: str) -> None:
    notify(
        title=f"Request failed ({res.status_code})",
        subtitle=subtitle,
        text=res.json()["detail"],
    )


#### ---- SwiftBar Plugin UI ---- ####


def get_active_coffee_bags() -> List[CoffeeBag]:
    try:
        response = requests.get(api_url + "active_bags/")
    except Exception as err:
        print(f"error: {err}")
        return []

    if response.status_code == 200:
        return [CoffeeBag(key=k, **i) for k, i in response.json().items()]
    else:
        raise Exception(response.status_code)


def get_todays_uses() -> List[CoffeeUse]:
    try:
        response = requests.get(
            api_url + f"uses/?n_last=20&since={get_today_formatted_datetime()}"
        )
        return [CoffeeUse(key=k, **i) for k, i in response.json().items()]
    except Exception as err:
        print(f"error: {err}")
        return []


def get_number_of_cups_today() -> int:
    cups: List[CoffeeUse] = get_todays_uses()
    return len(cups)


def standard_command(terminal="false") -> str:
    cmd = "refresh=true "
    cmd += f"bash={self_path.as_posix()} "
    cmd += f"terminal={terminal} "
    return cmd


def make_default_command(bag: CoffeeBag) -> str:
    cmd = standard_command()
    cmd += f"param1='{CLICommands.use_bag}' "
    cmd += f"param2='{bag.key}' "
    return cmd


def make_option_command(bag: CoffeeBag) -> str:
    cmd = standard_command()
    cmd += "color=red alternate=true "
    cmd += f"param1='{CLICommands.deactivate_bag}' "
    cmd += f"param2='{bag.key}' "
    return cmd


def make_newbag_command() -> str:
    cmd = standard_command(terminal="true")
    cmd += f"param1='{CLICommands.new_bag}' "
    return cmd


def swiftbar_plugin():
    """The default plugin to interact with the Coffee Counter API."""
    print(":drop.fill: | sfcolor=#764636 ansi=false emojize=false symbolize=true")
    print("---")

    coffee_bags = get_active_coffee_bags()
    for bag in coffee_bags:
        default_cmd = make_default_command(bag)
        option_cmd = make_option_command(bag)
        print(str(bag) + " | " + default_cmd)
        print("finish " + str(bag) + " | " + option_cmd)

    print("---")

    print("Add a new bag... | " + make_newbag_command())

    print("---")

    n_cups = get_number_of_cups_today()
    cups_label = "cup" if n_cups == 1 else "cups"
    print(f"{n_cups} {cups_label} of ☕️ today")

    print("---")

    print("Refresh | refresh=true")

    return None


#### ---- Use of a coffee ---- ####


def display_response_results(
    res: requests.Response,
    on_fail_only=False,
    notify: bool = False,
    subtitle: Optional[str] = None,
):
    if res.status_code == 200:
        if on_fail_only:
            return
        print("Successful!")
        print(res.json())
    else:
        print(f"Error: status code: {res.status_code}")
        print(res.json())
        if notify and subtitle is not None:
            notify_failed_request(res, subtitle=subtitle)


@app.command(CLICommands.use_bag)
def put_coffee_use(bag_id: str):
    """Submit a new coffee use to the API

    Args:
        bag_id (str): The unique ID for the bag.

    Raises:
        Exception: Invalid password.
    """
    password = get_api_password()
    if password is None:
        raise Exception("Password not found.")

    when = get_now_formatted_datetime()
    url = api_url + f"new_use/{bag_id}?password={password}&when={when}"
    response = requests.put(url)
    display_response_results(
        response, notify=True, subtitle="Unable to put coffee use."
    )


#### ---- Deactivate a bag ---- ####


@app.command(CLICommands.deactivate_bag)
def deactivate_coffee_bag(bag_id: str):
    """Deactivate a bag in the data base.

    Args:
        bag_id (str): The unique ID for the bag.

    Raises:
        Exception: Invalid password.
    """
    password = get_api_password()
    if password is None:
        raise Exception("Password not found.")

    d = get_today_formatted_date()
    url = api_url + f"deactivate/{bag_id}?password={password}&when={d}"
    response = requests.patch(url)
    display_response_results(
        response, notify=True, subtitle="Unable to deactivate bag."
    )


#### ---- New bag ---- ####


def submit_new_bag(bag: CoffeeBag):
    password = get_api_password()
    if password is None:
        raise Exception("Password not found.")
    url = api_url + f"new_bag/?password={password}"
    bag_data = bag.dict()
    bag_data["start"] = bag.start.strftime(date_format())
    _ = bag_data.pop("key", None)
    print(bag_data)
    response = requests.put(url, json=bag_data)
    display_response_results(
        response, on_fail_only=True, notify=True, subtitle="Unable to add a new bag."
    )


def confirm_new_bag_info(bag: CoffeeBag) -> bool:
    head_msg = "New Coffee Bag Information:"
    print("-" * len(head_msg))
    print(head_msg)
    print(f">  brand: {bag.brand}")
    print(f">   name: {bag.name}")
    print(f"> weight: {bag.weight}")
    print(f">  start: {bag.start}")
    print("-" * len(head_msg))
    return typer.confirm("Submit bag?", default=True)


@app.command(CLICommands.new_bag)
def new_bag(
    brand: str = typer.Option(..., prompt="bag brand"),
    name: str = typer.Option(..., prompt="bag name"),
    weight: float = typer.Option(340.0, prompt="weight"),
    start: datetime = typer.Option(
        default=get_today_formatted_date(), prompt="starting date"
    ),
):
    """Add a new bag to the data base

    This command gets data from the user interactively if called from the CLI.

    Args:
        brand (str, optional): Brand of the bag.
        name (str, optional): Name of the bag.
        weight (float, optional): Weight of the bag in grams. Defaults to 340.0.
        start (datetime, optional): When the bag was started. Defaults to today.

    Returns:
        [type]: [description]
    """
    bag = CoffeeBag(brand=brand, name=name, weight=weight, start=start, key="stand-in")
    if not confirm_new_bag_info(bag):
        print("Bag not submitted.")
    else:
        submit_new_bag(bag)
        print("New bag submitted!")
    return None


#### ---- Profiling ---- ####


@app.command(CLICommands.profile)
def profile_plugin(n_loops: int = 10):
    """Profile the plugin.

    Args:
        n_loops (int, optional): Number of loops. Defaults to 10.
    """
    from statistics import mean, median, stdev
    from time import time

    timers: List[float] = []
    for _ in range(n_loops):
        a = time()
        swiftbar_plugin()
        b = time()
        timers.append(b - a)
    print(f"     mean: {mean(timers)}")
    print(f"   median: {median(timers)}")
    print(f"std. dev.: {stdev(timers)}")


#### ---- Main ---- ####

# This is a bit of a workaround to get a default option without providing a command.
# https://github.com/tiangolo/typer/issues/18#issuecomment-617089716
@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    """A hack to have a default command with the Typer CLI.

    Args:
        ctx (typer.Context): The context supplied by Typer.
    """
    if ctx.invoked_subcommand is None:
        swiftbar_plugin()


if __name__ == "__main__":
    app()
