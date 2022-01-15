#!/Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

# <bitbar.title>Coffee Tracker Plugin</bitbar.title>
# <bitbar.version>v1.0.0</bitbar.version>
# <bitbar.author>Joshua Cook</bitbar.author>
# <bitbar.author.github>jhrcook</bitbar.author.github>
# <bitbar.desc>Recording of cups of coffee with my Coffee Tracker API.</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

import os
import socket
import sys
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlencode

import keyring
import requests
import typer
from pydantic import BaseModel

# --- API and app configuration ---

self_path = Path(sys.argv[0])

api_url = "https://coffee-counter.deta.dev/"
streamlit_url = "https://share.streamlit.io/jhrcook/coffee-counter-streamlit/app.py"
app = typer.Typer()

# --- Constants ---

ICON_BROWN: str = "#764636"


class CLICommands(str, Enum):
    """Available CLI commands."""

    deactivate_bag = "deactivate_bag"
    use_bag = "use_bag"
    new_bag = "new_bag"
    profile = "profile"


# --- Interactions with KeyChain ---


def get_api_password() -> Optional[str]:
    """Get my password for the API.

    Returns:
        Optional[str]: The password, if one is found.
    """
    return keyring.get_password("swiftbar_coffee-tracker", "Joshua Cook")


# --- Models ---


class CoffeeBag(BaseModel):
    """Coffee bag information."""

    brand: str
    name: str
    weight: float
    start: date
    key: str

    def __str__(self) -> str:
        """Human-readable representation."""
        return self.brand + " - " + self.name


class CoffeeUse(BaseModel):
    """Cup of coffee."""

    bag_id: str
    datetime: datetime
    key: str


# --- Date and Datetime Formatting ---


def date_format() -> str:
    """Date formatting string."""
    return "%Y-%m-%d"


def datetime_format() -> str:
    """Datetime formatting string."""
    return date_format() + "T%H:%M:%S"


def get_today_formatted_datetime() -> str:
    """Formatted datetime for today."""
    t = datetime.combine(date.today(), datetime.min.time())
    return t.strftime(datetime_format())


def get_now_formatted_datetime() -> str:
    """Formatted datetime for right now."""
    return datetime.now().strftime(datetime_format())


def get_today_formatted_date() -> str:
    """Formatted date for today."""
    return date.today().strftime(date_format())


# --- Network ---


def is_connected(hostname: str = "1.1.1.1") -> bool:
    """Whether or not there is a network connection.

    Args:
        hostname (str, optional): Hostname to try to reach. Defaults to "1.1.1.1".

    Returns:
        bool: Is there a network connection?
    """
    try:
        host = socket.gethostbyname(hostname)
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except BaseException:
        pass
    return False


# --- Notifications ---


def notify(title: str, subtitle: str, body: str) -> None:
    """Notification to show in the MacOS notifications through SwiftBar.

    Args:
        title (str): Title of the notification.
        subtitle (str): Subtitle of the notification.
        body (str): Body text of the notification.
    """
    notification: dict[str, str] = {
        "plugin": "coffee-tracker.1h.py",
        "title": title,
        "subtitle": subtitle,
        "body": body,
    }
    query = urlencode(notification, quote_via=quote)  # type: ignore
    cmd = f'open -g "swiftbar://notify?{query}"'
    os.system(cmd)


def notify_failed_request(res: requests.Response, subtitle: str) -> None:
    """Create a notification that a request failed.

    Args:
        res (requests.Response): Response of the failed request.
        subtitle (str): Subtitle for the notification.
    """
    notify(
        title=f"Request failed ({res.status_code})",
        subtitle=subtitle,
        body=res.json()["detail"],
    )


# --- SwiftBar Plugin UI ---


def get_active_coffee_bags() -> list[CoffeeBag]:
    """List the active coffee bags.

    TODO: Use more appropriate exception classes.

    Raises:
        BaseException: Raised if the request to the API fails.

    Returns:
        list[CoffeeBag]: List of coffee bags.
    """
    try:
        response = requests.get(api_url + "active_bags/")
    except BaseException:
        return []

    if response.status_code == 200:
        return [CoffeeBag(key=k, **i) for k, i in response.json().items()]
    else:
        raise BaseException(response.status_code)


def get_number_of_cups_today() -> int:
    """Number of cups of coffee consumed today.

    TODO: Use more appropriate exception classes.

    Raises:
        BaseException: Raised if the request to the API fails.

    Returns:
        int: Number of cups of coffee.
    """
    try:
        response = requests.get(
            api_url + f"number_of_uses/?since={get_today_formatted_datetime()}"
        )
    except BaseException:
        return 0

    if response.status_code == 200:
        return response.json()
    else:
        return 0


def _standard_command(terminal="false") -> str:
    cmd = "refresh=true "
    cmd += f"bash={self_path.as_posix()} "
    cmd += f"terminal={terminal} "
    return cmd


def make_default_command(bag: CoffeeBag) -> str:
    """Generate text for SwiftBar to call the script for the use of a coffee bag.

    Example output:
        "BRCC - Murdered Out | refresh=true bash=coffee-tracker.1h.py terminal=false
                               param1='use_bag' param2='bag-uuid'"

    Args:
        bag (CoffeeBag): Bag of coffee.

    Returns:
        str: Text for SwiftBar to indicate a cup of coffee was made with the coffee bag
        by calling this script with the appropriate arguments and parameters.
    """
    cmd = _standard_command()
    cmd += f"param1='{CLICommands.use_bag}' "
    cmd += f"param2='{bag.key}' "
    return cmd


def make_option_command(bag: CoffeeBag) -> str:
    """Generate text for SwiftBar to call the script for the deactivation of a bag.

    Example output:
        "finish BRCC - Murdered Out | refresh=true bash=coffee-tracker.1h.py
                                      terminal=false color=red alternate=true
                                      param1='deactivate_bag' param2='bag-uuid'"

    Args:
        bag (CoffeeBag): Bag of coffee to deactivate.

    Returns:
        str: Text for SwiftBar to indicate a cup of coffee was made with the coffee bag
        by calling this script with the appropriate arguments and parameters.
    """
    cmd = _standard_command()
    cmd += "color=red alternate=true "
    cmd += f"param1='{CLICommands.deactivate_bag}' "
    cmd += f"param2='{bag.key}' "
    return cmd


def make_newbag_command() -> str:
    """Generate text for SwiftBar for an option to add a new bag of coffee."""
    cmd = _standard_command(terminal="true")
    cmd += f"param1='{CLICommands.new_bag}' "
    return cmd


def display_add_new_bag() -> None:
    """Display the option to add a new bag in the SwiftBar dropdown menu."""
    print("---")
    print(":plus.circle: Add a new bag... | symbolize=true" + make_newbag_command())
    print("---")
    return None


def get_icon(network_is_connected: bool, num_bags: int) -> tuple[str, str]:
    """Icon for the menu bar.

    Args:
        network_is_connected (bool): Is there a network connection?
        num_bags (int): Number of coffee bags available.

    Returns:
        tuple[str, str]: Icon and its color.
    """
    if not network_is_connected:
        return ":drop:", ICON_BROWN
    if num_bags < 1:
        return ":drop.triangle:", "red"
    return ":drop.fill:", ICON_BROWN


def display_menu_bar_icon(network_is_connected: bool, num_bags: int) -> None:
    icon, icon_color = get_icon(network_is_connected, num_bags)
    print(f"{icon} | sfcolor={icon_color} ansi=false emojize=false symbolize=true")
    print("---")
    return None


def display_number_of_cups() -> None:
    """Display the number of cups consumed today in the SwiftBar dropdown menu."""
    n_cups = get_number_of_cups_today()
    cups_label = "cup" if n_cups == 1 else "cups"
    print(f"{n_cups} {cups_label} of ☕️ today")
    return None


def display_refresh() -> None:
    """Display a refresh button in the SwiftBar dropdown menu."""
    print(":arrow.clockwise: Refresh | refresh=true symbolize=true")
    return None


def display_open_docs() -> None:
    """Display an option to open the online docs in the SwiftBar dropdown menu."""
    print(f":doc.text: Open online docs | href={api_url}docs symbolize=true")
    return None


def display_open_streamlit_app() -> None:
    """Display an option to open the Streamlit app in the SwiftBar dropdown menu."""
    print(f":chart.xyaxis.line: Streamlit app | href={streamlit_url} symbolize=true")
    return None


def display_coffee_bag_choices(coffee_bags: list[CoffeeBag]) -> None:
    for bag in coffee_bags:
        default_cmd = make_default_command(bag)
        option_cmd = make_option_command(bag)
        print(str(bag) + " | " + default_cmd)
        print("finish " + str(bag) + " | " + option_cmd)
    return None


def display_no_coffee_bags_message() -> None:
    print("No bags available 😦")
    return None


def swiftbar_plugin():
    """The default plugin to interact with the Coffee Counter API."""
    network_connection = is_connected()
    coffee_bags: list[CoffeeBag] = (
        get_active_coffee_bags() if network_connection else []
    )

    display_menu_bar_icon(network_connection, num_bags=len(coffee_bags))

    if network_connection:
        if len(coffee_bags) == 0:
            display_no_coffee_bags_message()
        else:
            display_coffee_bag_choices(coffee_bags)
        display_add_new_bag()
        display_number_of_cups()
    else:
        print("No network connection.")
    print("---")
    display_refresh()
    display_open_docs()
    display_open_streamlit_app()
    return None


# --- Use of a coffee ---


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
    """Submit a new coffee use to the API.

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


# --- Deactivate a bag ---


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


# --- New bag ---


def submit_new_bag(bag: CoffeeBag):
    password = get_api_password()
    if password is None:
        raise Exception("Password not found.")
    url = api_url + f"new_bag/?password={password}"
    bag_data = bag.dict()
    bag_data["start"] = bag.start.strftime(date_format())
    _ = bag_data.pop("key", None)
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
    """Add a new bag to the data base.

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


# --- Profiling ---


@app.command(CLICommands.profile)
def profile_plugin(n_loops: int = 10):
    """Profile the plugin.

    Args:
        n_loops (int, optional): Number of loops. Defaults to 10.
    """
    from statistics import mean, median, stdev
    from time import time

    timers: list[float] = []
    for _ in range(n_loops):
        a = time()
        swiftbar_plugin()
        b = time()
        timers.append(b - a)
    print(f"     mean: {mean(timers)}")
    print(f"   median: {median(timers)}")
    print(f"std. dev.: {stdev(timers)}")


# --- Main ---

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
