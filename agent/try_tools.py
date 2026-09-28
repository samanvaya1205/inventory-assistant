import json
from getpass import getpass

from tools import login, make_read_tools

username = input("username: ")
password = getpass("password: ")

token = login(username, password)
list_items, get_item, list_categories, list_tags = make_read_tools(token)

print(json.dumps(list_items.invoke({}), indent=2))
print(json.dumps(get_item.invoke({"item_id": 1}), indent=2))
print(json.dumps(get_item.invoke({"item_id": 999}), indent=2))