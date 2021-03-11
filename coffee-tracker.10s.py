#!//Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import keyring
import requests

self_path = Path(sys.argv[0])

api_url = "https://a7a9ck.deta.dev/"


def get_api_password() -> Optional[str]:
    return keyring.get_password("swiftbar_coffee-tracker", "Joshua Cook")


class CoffeeBag:
    brand: str
    name: str
    key: str

    def __init__(self, brand, name, key, **info):
        self.brand = brand
        self.name = name
        self.key = key

    def __str__(self) -> str:
        return self.brand + " - " + self.name


#### ---- SwiftBar Plugin UI ---- ####


def get_active_coffee_bags() -> List[Dict[str, Any]]:
    try:
        response = requests.get(api_url + "active_bags/")
    except Exception as err:
        print(f"error: {err}")
        return []

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(response.status_code)


def make_click_command(bag: CoffeeBag) -> str:
    cmd = "refresh=true "
    cmd += f"bash={self_path.as_posix()} "
    cmd += f"param1='{bag.key}' "
    cmd += "terminal=false"
    return cmd

    # bash={self_path.as_posix()} param1={env} refresh=true terminal=false


def swiftbar_plugin():
    print(":drop.fill: | sfcolor=#764636 ansi=false emojize=false symbolize=true")
    print("---")

    coffee_bags = get_active_coffee_bags()
    for info in coffee_bags:
        coffee_bag = CoffeeBag(**info)
        click_cmd = make_click_command(coffee_bag)
        print(coffee_bag.__str__() + " | " + click_cmd)


#### ---- Response to clicking a coffee ---- ####


def get_now_formatted() -> str:
    dtformat = "%Y-%m-%dT%H:%M:%S"
    return datetime.now().strftime(dtformat)


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


#### ---- Argument Parsing ---- ####


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag_id", type=str, default=None, nargs="?")
    return parser.parse_args()


#### ---- Main ---- ####

if __name__ == "__main__":
    args = parse_arguments()
    if args.bag_id is None:
        swiftbar_plugin()
    else:
        put_coffee_use(args.bag_id)
    # Argument parsing:
    # no arguments: the plugin is just running
    # one argument: the coffee button that was selected
    # Use the arguments to either run `swiftbar_plugin()` or `coffee_selected()`.
