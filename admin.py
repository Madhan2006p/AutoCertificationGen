import backend.db_refresh as dr
import backend.view as v


print("Welcome to Admin Dashboard")

while True:
    print("1. To DB Refresh")
    print("2. To View")
    print("3. Exit")
    user_input = input("Enter the Option: ")
    if user_input == "1":
        dr.refresh()
    elif user_input == "2":
        v.view()
    elif user_input == "3":
        break
    else:
        print("Invalid Option")

print("Exited..")
    