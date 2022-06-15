from inspect import signature
from datetime import date
import re
import csv
import random
import os


def iso_date(parts):
    return "-".join([str(part) for part in parts])


def parse_seconds(seconds):
    seconds = int(seconds)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02}"


def color_wrap(string, color):
    return f"{color}{string}\033[0m"


def create_menu(title=None):
    options = []

    def add_option(name, callback, show=None):
        options.append({"name": name, "callback": callback, "show": show})

    def show_menu(loop=False):
        def add_cleanup(cleanup):
            cleanups.append(cleanup)

        cleanups = []

        relevant_options = []
        for option in options:
            if option["show"]:
                shouldShow = option["show"]()
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

        selection = get_selection(len(relevant_options))
        if selection == 0:
            return

        print()
        index = selection - 1
        callback = relevant_options[index]["callback"]
        try:
            # Only give the callback function an argument if it wants one
            parameters = len(signature(callback).parameters)
            callback() if parameters == 0 else callback(add_cleanup)
        except KeyboardInterrupt:
            message = "Aborting..." if len(cleanups) else "Aborted!"
            print(color_wrap("\n" + message, COLOR_RED))
        finally:
            for cleanup in cleanups:
                cleanup()

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


def reload_user():
    """Brings the in-memory state up-to-date with the accounts.csv"""
    username = state["user"]["name"]
    matched_account = get_account(username)

    if not matched_account:
        raise LookupError(f'Couldn\'t find an account with the name "{username}"!')

    state["user"] = matched_account


def update_user(column, value):
    accounts_csv = get_file("accounts.csv")
    old_rows = accounts_csv.readlines()
    new_rows = []
    matched = False

    for row in old_rows:
        columns = row.strip().split(",")

        if columns[0] != state["user"]["name"]:
            new_rows.append(row)
            continue

        matched = True

        if len(columns) <= column:
            raise IndexError(
                f"Cannot modify column number {column} in a row with {len(columns)} columns!"
            )

        columns[column] = value
        new_rows.append(",".join(columns) + "\n")
    accounts_csv.close()

    if not matched:
        raise LookupError(f"Account no longer exists in the accounts.csv file!")

    # Overwrite the file with all the new rows
    accounts_csv = open("accounts.csv", "w")
    for row in new_rows:
        accounts_csv.write(row)
    accounts_csv.close()


def get_selection(max):
    try:
        raw_input = input("Make a selection: ")
    except KeyboardInterrupt:
        print(color_wrap(" Selection cancelled!", COLOR_RED))
        return 0

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


def text_input(prompt, default=None):
    raw_input = input(prompt)
    if default and raw_input == "":
        return default
    if not raw_input:
        print("Enter at least one character!")
        return text_input(prompt)
    return raw_input


def time_input(prompt):
    minutes = 0
    seconds = 0
    raw_input = input(f"{prompt}: (mins) ")
    
    if not raw_input:
        print("You have to enter something!")
        return time_input(prompt)
    elif re.search("\d+:\d+", raw_input):
        parts = raw_input.split(":")
        minutes = int(parts[0])
        seconds = int(parts[1])
    elif raw_input.replace(".", "").isnumeric():
        minutes = float(raw_input)
    else:
        print("Enter a number!")
        return time_input(prompt)

    return minutes + (seconds / 60)


def genre_input(prompt):
    raw_input = text_input(prompt).lower()
    if not raw_input in GENRES:
        print("That's not a valid genre!")
        print("Available genres:", ", ".join(GENRES))
        return genre_input(prompt)
    return raw_input


def artist_input(prompt):
    library = get_library()
    valid_artists = set()

    for song in library:
        valid_artists.add(song["artist"])
    
    raw_input = text_input(prompt)
    if raw_input not in valid_artists:
        artists_sample = list(valid_artists)[5:]
        print("There aren't any songs with that artist!")
        print("Some possible artists include:", ", ".join(artists_sample))
        artist_input(prompt)


def new_file_input(prompt):
    raw_input = text_input(prompt)
    
    if os.path.isfile(raw_input):
        print("There's already a file at that location!")
    elif os.path.exists(raw_input):
        print("That filepath is a directory!")

    return raw_input


def get_account(username):
    accounts_csv = get_file("accounts.csv")
    reader = csv.reader(accounts_csv)
    for account in reader:
        if account[0] == username:
            accounts_csv.close()
            return {
                "name": account[0],
                "birth_date": account[1],
                "favourite_artist": account[2],
                "favourite_genre": account[3],
            }
    accounts_csv.close()
    return None


def get_library():
    try:
        library_csv = open("library.csv", "r")
    except FileNotFoundError:
        raise FileNotFoundError("Could not access library.csv!")

    songs = []

    for song in csv.reader(library_csv):
        if len(song) < 5:
            raise LookupError(
                f"Song {song[0]} in library.csv does not have all the required fields!"
            )

        songs.append(
            {
                "id": int(song[0]),
                "artist": song[1],
                "title": song[2],
                "length": int(song[3]),
                "genre": song[4],
            }
        )

    library_csv.close()
    return songs

def get_song(id):
    songs = get_library()
    for song in songs:
        if song["id"] == id:
            return song
    raise LookupError(f"Could not find a song in the library with an ID of {id}")

def get_songs_from_artist(artist):
    songs = get_library()
    matching_songs = []
    
    for song in songs:
        if song["artist"] == id:
            matching_songs.append(song)

    return matching_songs


def print_heading():
    cyan = "\x1b[36m"
    reset = "\x1b[0m"
    blue = "\x1b[1;34m"
    ASCII_ART = """\
 _____  _____ ______  _                            
|  _  |/  __ \| ___ \| |                           
| | | || /  \/| |_/ /| |_  _   _  _ __    ___  ___ 
| | | || |    |    / | __|| | | || '_ \  / _ \/ __|
\ \_/ /| \__/\| |\ \ | |_ | |_| || | | ||  __/\__ \\
 \___/  \____/\_| \_| \__| \__,_||_| |_| \___||___/"""
    TAGLINES = [
        "Find your new favourite artist with OCRtunes.",
        "If you can't find it on OCtunes, it doesn't exist.",
        "Music to your ears",
        "Your perfect playlist, every time.",
    ]
    print(blue + ASCII_ART + reset)
    ascii_art_width = 51
    tagline = random.choice(TAGLINES)
    padding_width = (ascii_art_width - len(tagline)) // 2
    print(padding_width * " " + cyan + tagline + reset)
    print()


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


def pick_account():
    default = state["old_user"] if "old_user" in state else ""
    prompt_suffix = f"({default}) " if default else ""
    prompt = "Enter your name: " + prompt_suffix

    username = text_input(prompt, default).title()
    matched_account = get_account(username)
    if not matched_account:
        print("Could not find an account with that name!")
        return pick_account()

    state["user"] = matched_account
    name = state["user"]["name"]
    print(f'Successfully logged in to account "{name}": welcome back to OCRtunes!')


def log_out():
    try:
        input("Press enter to log out...")
    except KeyboardInterrupt:
        return print(color_wrap(" Aborted!", COLOR_RED))

    state["old_user"] = state["user"]["name"]
    state.pop("user")
    print("Successfully logged out!")


def edit_artist():
    current_artist = state["user"]["favourite_artist"]
    print(f'Your favourite artist is currently set to "{current_artist}"')
    new_artist = text_input("Enter your new favourite artist: ")

    update_user(2, new_artist)  # 2 is the index of the favourite artist column
    reload_user()
    print(f'Successfully changed your favourite artist to "{new_artist}"')


def edit_genre():
    current_genre = state["user"]["favourite_genre"]
    print(f'Your favourite genre is currently set to "{current_genre}"')
    new_genre = genre_input("Enter your new favourite genre: ")

    update_user(3, new_genre)  # 3 is the index of the favourite genre column
    reload_user()
    print(f'Successfully changed your favourite genre to "{new_genre}"')


def edit_interests():
    add_option, show_menu = create_menu()
    add_option("Edit favourite artist", edit_artist)
    add_option("Edit favourite genre", edit_genre)
    show_menu()


def sort_library():
    library_data = get_library()
    library_data.sort(key=lambda song: song["title"].lower())
    return library_data


def print_song(song):
    print(f"{song['title']} ({song['artist']}) ({parse_seconds(song['length'])})")


def song_library():
    library = sort_library()
    for song in library:
        print_song(song)


def get_short_songs(max_length):
    songs = get_library()
    matching_songs = []
    for song in songs:
        if song["length"] <= max_length:
            matching_songs.append(song)
    return matching_songs


def generate_playlist():
    playlist = []
    songs = get_library()
    time_limit = time_input("Maximum run time of playlist")
    max_seconds = time_limit * 60
    full_run_time = 0
    done = False
    checked_songs = 0
    print()
    print("Generating playlist...")
    while not done:
        possible_songs = get_short_songs(max_seconds)
        
        if len(possible_songs) == 0:
            print("Couldn't find any songs that are that short!")
            return
        
        chosen_song = random.choice(songs)
        checked_songs += 1
        if checked_songs == len(songs):
            # We've run out of songs!
            break
        if full_run_time + chosen_song['length'] > max_seconds:
            # Adding this song would make the playlist too long
            break
        playlist.append(chosen_song["id"])
        full_run_time += chosen_song['length']

    print(f"Successfully made a playlist with {len(playlist)} songs!")
    print(f"Playlist run time is {parse_seconds(full_run_time)}")
    input("Press enter to view playlist...")

    for song_id in playlist:
        print_song(get_song(song_id))


def export_songs():
    print("This allows you to enter an artist's name and save all their songs to  a text file.")
    artist = artist_input("Artist: ")
    filename = new_file_input("Filename: ")
    artist_input("Artist: ")


GENRES = ["pop", "rock", "hip hop", "rap"]

COLOR_RED = "\x1b[31m"

# Global store for the state of the program (e.g. currently logged-in user)
state = {}

print_heading()
add_option, show_menu = create_menu("=== OCRtunes Main Menu ===")
add_option("Create an account", create_account, lambda: not "user" in state)
add_option("Log in", pick_account, lambda: not "user" in state)
add_option("Log out", log_out, lambda: "user" in state)
add_option("Edit interests", edit_interests, lambda: "user" in state)
add_option("Display song library", song_library)
add_option("Generate playlist", generate_playlist, lambda: "user" in state)
add_option("Export songs from an artist", export_songs)
show_menu(True)
