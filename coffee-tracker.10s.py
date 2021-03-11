#!//Users/admin/Documents/SwiftBar-Plugins/.env/bin/python3

from typing import Dict, Any

import requests

api_url = "https://a7a9ck.deta.dev/"


class CoffeeBag:
    brand: str
    name: str

    def __init__(self, brand: str, name: str):
        self.brand = brand
        self.name = name

    def __str__(self) -> str:
        return self.brand + " - " + self.name


def get_active_coffee_bags() -> List[Dict[str, Any]]:
    response = requests.get(api_url + "active_bags/")
    if response.status_code == 200:
        return response.json()


def swiftbar_plugin():
    print(":drop.fill: | sfcolor=#764636 ansi=false emojize=false symbolize=true")
    print("---")

    coffee_bags = get_active_coffee_bags()
    for info in coffee_bags:
        coffee_bag = CoffeeBag(brand=info["brand"], name=info["name"])
        print(coffee_bag)


if __name__ == "__main__":

    # Argument parsing:
    # no arguments: the plugin is just running
    # one argument: the coffee button that was selected
    # Use the arguments to either run `swiftbar_plugin()` or `coffee_selected()`.

    swiftbar_plugin()