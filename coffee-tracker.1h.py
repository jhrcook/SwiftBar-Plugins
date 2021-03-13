#!//Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

# <bitbar.title>Coffee Tracker Plugin</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Joshua Cook</bitbar.author>
# <bitbar.author.github>jhrcook</bitbar.author.github>
# <bitbar.desc>Easy logging of cups of coffee.</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import keyring
import requests
from pydantic import BaseModel

self_path = Path(sys.argv[0])

api_url = "https://a7a9ck.deta.dev/"


def get_api_password() -> Optional[str]:
    return keyring.get_password("swiftbar_coffee-tracker", "Joshua Cook")


class CoffeeBag(BaseModel):
    brand: str
    name: str
    key: str

    def __str__(self) -> str:
        return self.brand + " - " + self.name


class CoffeeUse(BaseModel):
    bag_id: str
    datetime: datetime
    key: str


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


def make_default_command(bag: CoffeeBag) -> str:
    cmd = "refresh=true "
    cmd += f"bash={self_path.as_posix()} "
    cmd += f"param1='{bag.key}' "
    cmd += "terminal=false"
    return cmd


def get_todays_uses() -> List[CoffeeUse]:
    try:
        response = requests.get(
            api_url + f"uses/?n_last=20&since={get_today_formatted()}"
        )
        return [CoffeeUse(key=k, **i) for k, i in response.json().items()]
    except Exception as err:
        print(f"error: {err}")
        return []


def get_number_of_cups_today(bags: List[CoffeeBag]) -> int:
    cups: List[CoffeeUse] = get_todays_uses()
    bag_keys = [b.key for b in bags]
    cups = [cup for cup in cups if cup.bag_id in bag_keys]
    return len(cups)


def make_option_command(bag: CoffeeBag) -> str:
    return "color=red alternate=true"


def swiftbar_plugin():
    print(":drop.fill: | sfcolor=#764636 ansi=false emojize=false symbolize=true")
    print("---")

    coffee_bags = get_active_coffee_bags()
    for bag in coffee_bags:
        default_cmd = make_default_command(bag)
        option_cmd = make_option_command(bag)
        print(str(bag) + " | " + default_cmd)
        print("finish " + str(bag) + " | " + option_cmd)

    print("---")

    n_cups = get_number_of_cups_today(bags=coffee_bags)
    cups_label = "cup" if n_cups == 1 else "cups"
    print(f"{n_cups} {cups_label} of ☕️ today")

    print("---")

    print("Refresh | refresh=true")

    return None


#### ---- Response to clicking a coffee ---- ####


def get_datetime_format() -> str:
    return "%Y-%m-%dT%H:%M:%S"


def get_today_formatted() -> str:
    t = datetime.combine(date.today(), datetime.min.time())
    return t.strftime(get_datetime_format())


def get_now_formatted() -> str:
    return datetime.now().strftime(get_datetime_format())


def put_coffee_use(bag_id: str):
    password = get_api_password()
    if password is None:
        raise Exception("Password not found.")

    when = get_now_formatted()
    url = api_url + f"new_use/{bag_id}?password={password}&when={when}"
    response = requests.put(url)
    if response.status_code == 200:
        print("Successful!")
        print(response.json())
    else:
        print(f"Error: status code {response.status_code}")
        print(response.json())


#### ---- Profiling ---- ####


def profile_plugin(n: int):
    from statistics import mean, median, stdev
    from time import time

    timers: List[float] = []
    for _ in range(n):
        a = time()
        swiftbar_plugin()
        b = time()
        timers.append(b - a)
    print(f"     mean: {mean(timers)}")
    print(f"   median: {median(timers)}")
    print(f"std. dev.: {stdev(timers)}")


#### ---- Argument Parsing ---- ####


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag_id", type=str, default=None, nargs="?")
    parser.add_argument("--profile", type=int, default=None, nargs="?")
    return parser.parse_args()


#### ---- Main ---- ####


def main():
    args = parse_arguments()
    if not args.bag_id is None:
        put_coffee_use(args.bag_id)
    elif not args.profile is None:
        profile_plugin(args.profile)
    else:
        swiftbar_plugin()


if __name__ == "__main__":
    main()
