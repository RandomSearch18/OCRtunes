import re
from datetime import date
import csv


def iso_date(parts):
    return "-".join([str(part) for part in parts])


def add_option(name, callback, show=None):
    options.append({"name": name, "callback": callback, "show": show})


def show_menu(options):
    for i, option in enumerate(options):
        if option["show"]:
            shouldShow = option["show"](state)
            if not shouldShow:
                continue
        print(f"{i+1}) {option['name']}")
    selection = get_selection(len(options))
    print()
    options[selection]["callback"]()


def new_record(*columns):
    record = ",".join([str(column) for column in columns])
    return record + "\n"


def get_file(filename):
    try:
        return open(filename, "r")
    except FileNotFoundError:
        # Create the file if it doesn't exist
        file = open(filename, "w")
        file.close()
        return open(filename, "r")


def get_selection(max):
    raw_input = input("Make a selection: ")
    if not raw_input.isnumeric():
        print("Your selection must be a number!")
        return get_selection(max)

    selection = int(raw_input)
    if selection < 1:
        print("Select a positive number! (Greater than zero)")
        return get_selection(max)
    if selection > max:
        print("Selection out of bounds: Must be below", max)
        return get_selection(max)

    return selection - 1


def name_input():
    raw_input = input("Enter your name: ")
    if len(raw_input) < 1:
        print("Your name must be at least one letter!")
        return name_input()
    return raw_input.title()


def date_input(prompt):
    # Ask the user for a YYYY-MM-DD date, and only accept that format
    raw_input = input(f"{prompt}: (YYYY-MM-DD) ").strip()
    if not re.search("^\d{4}-\d{2}-\d{2}$", raw_input):
        print("Please follow the correct format when entering the date!")
        return date_input(prompt)

    # Extract the year, month and day form the inputted value
    input_parts = raw_input.split("-")
    year = int(input_parts[0])
    month = int(input_parts[1])
    day = int(input_parts[2])

    # Basic date validation because dates are hard
    current_year = date.today().year
    if year > current_year:
        print(f"The provided year is {year - current_year} years in the future!")
        return date_input(prompt)
    if month > 12:
        print("You cannot have a month number greater than 12!")
        return date_input(prompt)
    if day > 31:
        print("You cannot have a month number greater than 31!")
        return date_input(prompt)

    return [year, month, day]


def text_input(prompt):
    raw_input = input(prompt)
    if not raw_input:
        print("Enter at least one character!")
        return text_input(prompt)
    return raw_input


def genre_input(prompt):
    raw_input = text_input(prompt).lower()
    if not raw_input in GENRES:
        print("That's not a valid genre!")
        print("Available genres:", ", ".join(GENRES))
        return genre_input(prompt)
    return raw_input


def create_account():
    name = name_input()
    birth_date = date_input("Enter your date of birth")
    favourite_artist = text_input("Enter your favourite artist: ")
    favourite_genre = genre_input("Enter your favourite genre: ")
    print("Thank you! Creating your account...")

    accounts_csv = open("accounts.csv", "a")
    account_data = new_record(
        name, iso_date(birth_date), favourite_artist, favourite_genre
    )
    accounts_csv.write(account_data)
    accounts_csv.close()
    print("Successfully created account: welcome to OCRtunes!")


def get_account(username):
    accounts_csv = get_file("accounts.csv")
    reader = csv.reader(accounts_csv)
    for account in reader:
        if account[0] == username:
            return {
                "name": account[0],
                "birth_date": account[1],
                "favourite_artist": account[2],
                "favourite_genre": account[3],
            }
    return None


def pick_account():
    username = text_input("Enter your name: ").title()
    matched_account = get_account(username)
    if not matched_account:
        print("Could not find an account with that name!")
        return pick_account()

    state["user"] = matched_account
    name = state["user"]["name"]
    print(f'Successfully logged in to account "{name}": welcome back to OCRtunes!')
    print(state)


GENRES = ["pop", "rock", "hip hop", "rap"]

state = {}
options = []
add_option("Create an account", create_account, lambda _: not "user" in state)
add_option("Log in", pick_account, lambda _: not "user" in state)
show_menu(options)
