import re
from datetime import date
import csv


def iso_date(parts):
    return "-".join([str(part) for part in parts])


def create_menu(title=None):
    options = []

    def add_option(name, callback, show=None):
        options.append({"name": name, "callback": callback, "show": show})

    def show_menu(loop=False):
        relevant_options = []
        for option in options:
            if option["show"]:
                shouldShow = option["show"](state)
                if shouldShow:
                    relevant_options.append(option)
            else:
                relevant_options.append(option)

        if len(relevant_options) == 0:
            print("No options available. Goodbye!")
            return

        if title:
            print(title)
        for i, option in enumerate(relevant_options):
            print(f"{i+1}) {option['name']}")

        selection = get_selection(len(options))
        if selection == 0:
            return

        print()
        index = selection - 1
        relevant_options[index]["callback"]()

        if not loop:
            return
        print("\n")
        show_menu(loop)

    return add_option, show_menu


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


def update_user(column, value):
    accounts_csv = get_file("accounts.csv")
    reader = csv.reader(accounts_csv)
    new_rows = [row for row in reader]
    for i, row in enumerate(new_rows):
        if i != column:
            new_rows.append(row)
        new_rows[column] = value
    accounts_csv.close()

    accounts_csv = open("accounts.csv", "w")
    writer = csv.writer(accounts_csv)
    writer.writerows(new_rows)
    accounts_csv.close()


def get_selection(max):
    raw_input = input("Make a selection: ")
    if not raw_input.isnumeric():
        print("Your selection must be a positive number!")
        return get_selection(max)

    selection = int(raw_input)
    if selection < 0:
        print("Select a positive number!")
        return get_selection(max)
    if selection > max:
        print("Selection out of bounds: Must be below", max)
        return get_selection(max)

    return selection


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


def edit_artist():
    current_artist = state["user"]["favourite_artist"]
    print(f'Your favourite artist is currently set to "{current_artist}"')
    new_artist = text_input("Enter your new favourite artist: ")

    # Update local (in-memory) user data
    state["user"]["favourite_artist"] = new_artist
    # 2 is the index of the favourite artist column
    update_user(2, new_artist)
    print(f'Successfully changed your favourite artist to "{new_artist}"')


def edit_genre():
    pass


def edit_interests():
    add_option, show_menu = create_menu()
    add_option("Edit favourite artist", edit_artist)
    add_option("Edit favourite genre", edit_genre)
    show_menu()


GENRES = ["pop", "rock", "hip hop", "rap"]
TAGLINES = [
    "Find your new favourite artist with OCRtunes.",
    "If you can't find it on OCtunes, it doesn't exist.",
    "Music to your ears",
    "Your perfect playlist, every time.",
]

state = {}

add_option, show_menu = create_menu("=== OCRtunes Main Menu ===")
add_option("Create an account", create_account, lambda _: not "user" in state)
add_option("Log in", pick_account, lambda _: not "user" in state)
add_option("Edit interests", edit_interests, lambda _: "user" in state)
show_menu(True)
