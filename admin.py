import backend.db_refresh as dr
import backend.view as v
import backend.access_person as ap


print("Welcome to Admin Dashboard")

while True:
    print("1. To DB Refresh")
    print("2. To View")
    print("3. Test")
    print("q=> Quit")
    user_input = input("Enter the Option: ")
    if user_input == "1":
        dr.refresh()
    elif user_input == "2":
        v.view()
    elif user_input == "3":
        roll_no = input("Enter the roll no: ")
        print(ap.get_user_by_reg(roll_no))
    elif user_input.lower() == "q":
        break
    else:
        print("Invalid Option")

print("Exited..")
    