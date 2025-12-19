from backend import access_person as ap
from backend import db_refresh as dr

user_input = input("1=> DB Refresh\n" \
"2=> Get Output \n Enter the Option:")
if user_input == "1":
    dr.refresh()
elif user_input == "2":
    roll_no = input("Enter the roll no: ")
    ap.get_user_by_reg(roll_no.lower())
else:
    print("Invalid option")