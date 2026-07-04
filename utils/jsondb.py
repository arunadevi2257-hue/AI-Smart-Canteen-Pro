import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_FILE = os.path.join(BASE_DIR, "data", "users.json")


def load_users():
    if not os.path.exists(USER_FILE):
        return []

    with open(USER_FILE, "r") as file:
        try:
            return json.load(file)
        except:
            return []


def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)


import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ORDER_FILE = os.path.join(BASE_DIR, "data", "orders.json")


def load_orders():

    if not os.path.exists(ORDER_FILE):
        return []

    with open(ORDER_FILE, "r") as file:
        try:
            return json.load(file)
        except:
            return []


def save_orders(orders):

    with open(ORDER_FILE, "w") as file:
        json.dump(orders, file, indent=4)        