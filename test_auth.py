from auth import *

print(login("manager", "manager123"))

print(create_user(
    "John Smith",
    "john@test.com",
    "john",
    "12345",
    "employee"
))

print(get_user("john"))

print(get_all_users())

change_password("john", "newpass")

deactivate_user("john")

print(get_user("john"))