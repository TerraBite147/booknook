# imports
import os
import gspread
from gspread.exceptions import APIError
from google.oauth2 import service_account
from tabulate import tabulate

# Define the scope for Google Sheets API
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

# Google Sheets connection
creds = service_account.Credentials.from_service_account_file(
    "creds.json", scopes=scope
)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("booknook-library").sheet1


def clear_screen():
    """Clear the terminal screen."""
    os.system("clear")


def display_options_in_columns(options):
    """Displays menu options in two columns."""

    # Split the options into two columns
    half_length = len(options) // 2
    col1 = options[:half_length]
    col2 = options[half_length:]

    # Calculate the maximum length of options in the first column
    max_length_col1 = max(len(option) for option in col1)

    # Display each pair of options side-by-side
    for i in range(half_length):
        if i < len(col2):
            print(
                f"{i+1}. {col1[i].ljust(max_length_col1 + 5)}"
                f" {i+half_length+1}. {col2[i]}"
            )
        else:
            print(f"{i+1}. {col1[i]}")


def fetch_books_from_sheet():
    """
    Fetch all books from Google Sheets
    and return as a list of Book objects.
    """
    rows = sheet.get_all_records()  # Returns a list of dictionaries
    books = [
        Book(
            row["Title"], row["Author"],
            row["Status"] == "Read", row.get("Rating")
        )
        for row in rows
    ]
    return books


def add_book_to_sheet(book):
    """Add a book to the Google Sheet."""
    read_status = "Read" if book.read else "Unread"
    sheet.append_row(
        [book.title, book.author, read_status, book.rating or "Unrated"]
    )


def remove_book_from_sheet(book_to_remove):
    try:
        cell = sheet.find(book_to_remove.title)
        sheet.delete_rows(cell.row)
    except APIError as e:
        print((
            "An error occurred while trying to"
            " remove the book from the Google Sheet:", e)
        )


# classes
class Book:
    """Represents a book in the library."""

    def __init__(self, title, author, read=False, rating=None):
        self.title = title
        self.author = author
        self.read = read
        self.rating = rating

    def display(self):
        """Displays the book's title, author, read status, and rating."""
        read_status = "Read" if self.read else "Unread"
        rating = self.rating if self.rating else "Unrated"

        # Using string formatting
        return "{:<30} | {:<25} | {:<10} | {:<10}".format(
            f"Title: {self.title}",
            f"Author: {self.author}",
            f"\nStatus: {read_status}",
            f"Rating: {rating}",
        )


# Pulls library from Google Sheets
library = fetch_books_from_sheet()


def sort_books_by_criteria(criteria):
    """Sorts the books by given criteria."""

    def sort_key(item):
        value = getattr(item, criteria)
        if value is None:
            return (0,)
        if isinstance(value, str):
            return (1, value)
        if isinstance(value, (int, float)):
            return (2, value)

    library.sort(key=sort_key)


def sort_library():
    """Sorts the library by title, author, read status, or rating."""
    if not library:
        print("Your library is empty.")
        return

    options = [
        "Sort by title",
        "Sort by author",
        "Sort by read status",
        "Sort by rating",
        "Return to main menu",
    ]

    display_options_in_columns(options)
    while True:
        try:
            choice = input("\nEnter your choice: ")
            choice = int(choice)

            if choice not in range(1, len(options) + 1):
                raise ValueError

            break
        except ValueError:
            print("Invalid choice. Please enter a number from the options.")

    sort_criteria = ["title", "author", "read", "rating"]

    if choice in [1, 2, 3, 4]:
        sort_books_by_criteria(sort_criteria[choice - 1])
        view_library(library)
    elif choice == 5:
        main_menu(library, view_library)


def get_book_details():
    title = input("Enter the title of the book: ").strip()
    author = input("Enter the author of the book: ").strip()
    return title, author


def check_duplicate_book(title, author):
    for book in library:
        if (
            book.title.lower() == title.lower()
            and book.author.lower() == author.lower()
        ):
            return True
    return False


def get_read_status():
    read_status = input("Have you read this book? (yes/no): ").lower()
    if read_status not in ["yes", "no"]:
        raise ValueError("Invalid response. Please enter 'yes' or 'no'.")
    return read_status == "yes"


def get_book_rating():
    while True:
        rating = input((
            "Rate the book (1-5) or type 'skip' to skip rating: "
            )).lower()
        if rating == "skip":
            return None
        elif rating in ["1", "2", "3", "4", "5"]:
            return int(rating)
        else:
            print("Invalid rating. Please choose between 1-5 or type 'skip'.")


def add_book():
    """Adds a book to the library."""
    try:
        title, author = get_book_details()

        # Check for duplicates
        if check_duplicate_book(title, author):
            print((
                "\nThe book with this title and "
                "author already exists in the library."
            ))
            input("\nPress enter to continue...\n")
            return

        read = get_read_status()
        rating = get_book_rating()

        # Create a Book object and add to the library
        new_book = Book(title, author, read, rating)
        library.append(new_book)

        # Add the book to the Google Sheet
        add_book_to_sheet(new_book)

        print(f"\n'{title}' by {author} has been added to the library!")
        input("\nPress enter to continue...\n")

    except ValueError as e:
        print(f"Error: {e}")
        input("\nPress enter to continue...\n")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        input("\nPress enter to continue...\n")


def remove_book():
    """Removes a book from the library."""
    global library  # Ensure we are using the global library variable

    if not library:
        print("The library is empty.")
        input("\nPress enter to continue...\n")
        return

    # If there are more than 10 books, display them in columns
    if len(library) > 10:
        book_options = [f"{book.title} by {book.author}" for book in library]
        display_options_in_columns(book_options)
    else:
        for idx, book in enumerate(library, 1):
            print(f"{idx}. {book.title} by {book.author}")

    while True:
        try:
            choice = int(
                input("\nEnter the number of the book you want to remove: \n")
                )
            if 1 <= choice <= len(library):
                removed_book = library.pop(choice - 1)
                break
            else:
                print(f"Please select a number between 1 and {len(library)}.")
        except ValueError:
            print("Please enter a valid number.")

    while True:
        confirmation = input(
            "\nAre you sure you want to remove"
            f" '{removed_book.title}' by {removed_book.author}? (yes/no): \n"
        ).lower()
        if confirmation == "yes":
            remove_book_from_sheet(removed_book)
            print(
                f"'{removed_book.title}' by {removed_book.author}"
                " has been removed from the library!"
            )
            break
        elif confirmation == "no":
            library.insert(choice - 1, removed_book)
            print(
                f"'{removed_book.title}' by {removed_book.author}"
                " was not removed."
                )
            break
        else:
            print("Please respond with 'yes' or 'no'.")

    input("\nPress enter to continue...\n")


def search_for_book(library):
    """Searches for a book by title or author."""
    while True:
        options = [
            "Search by Title", "Search by Author", "Return to main menu"
        ]

        print("\n--- Search Menu ---")
        for index, option in enumerate(options, start=1):
            print(f"{index}. {option}")

        choice = input("\nEnter your choice: \n")

        if not choice.isdigit():
            print("Please enter a valid option.")
            continue

        choice = int(choice)
        if choice in [1, 2]:
            keyword = (
                input("Enter the title keyword: \n").lower()
                if choice == 1
                else input("Enter the author keyword: \n").lower()
            )
            matches = [
                book
                for book in library
                if keyword
                in getattr(book, "title" if choice == 1 else "author").lower()
            ]

            clear_screen()
            if matches:
                for index, book in enumerate(matches, start=1):
                    print(f"{index}. {book.display()}")
                print("\nOptions:")
                print("1. Edit a book")
                print("2. Remove a book")
                print("3. Return to search menu")

                action_choice = input(
                    "\nEnter your choice, or enter to continue: \n"
                )
                if action_choice.isdigit():
                    action_choice = int(action_choice)
                    if action_choice == 1:
                        book_index = (
                            int(input(
                                "Enter the index of "
                                "the book you want to edit: "
                            ))
                            - 1
                        )
                        if 0 <= book_index < len(matches):
                            edit_book(matches[book_index])
                        else:
                            print("Invalid index!")

                    elif action_choice == 2:
                        book_index = (
                            int(input(
                                "Enter the index of the "
                                "book you want to remove: "
                                )) - 1
                        )
                        if 0 <= book_index < len(matches):
                            book_to_remove = matches[book_index]
                            library = [
                                book for book in library
                                if book != book_to_remove
                                ]
                            print(
                                f"Book '{book_to_remove.title}'"
                                " has been removed from the library."
                            )
                        else:
                            print("Invalid index!")
                    elif action_choice == 3:
                        return
                else:
                    input("\nPress enter to continue...\n")
                    return
            else:
                action = input(
                    "Enter another title/author or press 'Q' to return: \n"
                ).lower()
                if action == "q":
                    return
        elif choice == 3:
            return


def about_booknook():
    """Displays information about the library system."""
    clear_screen()
    print("Welcome to BookNook: Your Personal Library Management System!")
    print("-" * 80)  # prints a divider line

    print(
        "\nBookNook is designed to help you manage and keep track of your"
        " personal collection of books."
        "\nWith BookNook, you can:"
        "\n\n1. Manage your book collection."
        "\n2. View your entire library."
        "\n3. Record if you've read a book and rate it on a scale of 1-5."
        "\n4. Integrated with Google Sheets to ensure BookNook is portable."
        "\n5. Easily search, update, add or remove books from your collection."
        "\n\nOur system is user-friendly and aims to make your reading journey"
        " more organized and enjoyable!"
    )

    print("\nTechnical Details:")
    print("- Developed in Python with a focus on user experience.")
    print("- Utilizes object-oriented programming principles.")
    print("- Integration capability with Google Sheets using relevant APIs.")

    print(
        "\nWe continuously aim to improve BookNook."
        " Your feedback is valuable!")

    input("\nPress Enter to return to the main menu.")
    clear_screen()


def edit_book(book):
    try:
        new_title = input(
            f"Current title is '{book.title}'. Enter new title or press"
            " Enter to keep it: "
        )

        new_author = input(
            f"Current author is '{book.author}'. Enter new author or press"
            " Enter to keep it: "
        )

        # Validate read status input
        while True:
            read_status = input(
                "Is the book read? (current: "
                f"{'Read' if book.read else 'Unread'}). Enter 'yes' or 'no': "
            ).lower()
            if read_status in ["yes", "no", ""]:
                break
            else:
                print("Invalid input! Please enter 'yes' or 'no'.")

        # Validate rating input
        while True:
            rating = input(
                "Enter your rating for the book (1-5)"
                " or press Enter to keep it: "
            )
            if rating.isdigit() and 1 <= int(rating) <= 5 or rating == "":
                break
            else:
                print("Invalid input! Please enter a number between 1 and 5.")

        # Confirmation prompt
        print("\nPlease confirm the following changes:")
        print(f"Title: {new_title if new_title else book.title}")
        print(f"Author: {new_author if new_author else book.author}")
        print(
            "Read Status: "
            f"{'Read' if read_status.lower() == 'yes' else 'Unread'}")
        # cannot make below less than 80 characters
        print(
            f"Rating: "
            f"{rating if rating.isdigit() and 1 <= int(rating) <= 5 else 'Unchanged'}"
        )

        confirm = input("Are these changes correct? (yes/no): ")

        if confirm.lower() == "yes":
            # Apply changes if confirmed
            if new_title:
                book.title = new_title
            if new_author:
                book.author = new_author
            if read_status.lower() == "yes":
                book.read = True
            elif read_status.lower() == "no":
                book.read = False
            if rating.isdigit() and 1 <= int(rating) <= 5:
                book.rating = int(rating)
            print(f"Book '{book.title}' has been updated.")
        else:
            print("Edit cancelled. No changes were made.")
    except ValueError:
        print("Invalid input! Please enter a valid number.")


def main_menu(library, view_library_fn):
    """Displays Main Menu"""
    while True:
        clear_screen()
        print("""
 |  _ \            | |  | \ | |           | |
 | |_) | ___   ___ | | _|  \| | ___   ___ | | __
 |  _ < / _ \ / _ \| |/ | . ` |/ _ \ / _ \| |/ /
 | |_) | (_) | (_) |   <| |\  | (_) | (_) |   <
 |____/ \___/ \___/|_|\_|_| \_|\___/ \___/|_|\_\ """)
        print("\n--- Personal Library Management System ---")

        options = ["View Library", "Search for a Book", "About", "Exit"]

        display_options_in_columns(options)

        choice = input("\nEnter your choice: \n")
        if not choice.isdigit():
            print("Please enter a number corresponding to the options.")
            continue

        choice = int(choice)
        if choice == 1:
            view_library_fn(library)
        elif choice == 2:
            search_for_book(library)
        elif choice == 3:
            about_booknook()
        elif choice == 4:
            print(
                "Exiting... Thank you for using the Personal"
                " Library Management System!"
            )
            break
        else:
            print("Invalid choice. Please try again.")


def view_library(library):
    """Displays all books in the library and provides library options."""
    clear_screen()

    if not library:
        print("Your library is empty!")
    else:
        # Prepare data for tabulate
        table_data = []
        headers = ["#", "Title", "Author", "Status", "Rating"]

        for index, book in enumerate(library, start=1):
            read_status = "Read" if book.read else "Unread"
            rating = book.rating if book.rating else "Unrated"
            table_data.append(
                [index, book.title, book.author, read_status, rating]
                )

        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    print("\n--- Library Menu ---")
    options = [
        "Sort Library",
        "Add a Book",
        "Remove a Book",
        "Edit a Book",
        "Return to main menu",
    ]
    display_options_in_columns(options)
    print("5. Main Menu")

    choice = int(input("\nEnter your choice: \n"))

    if choice == 1:
        sort_library()
    elif choice == 2:
        add_book()
    elif choice == 3:
        remove_book()
    elif choice == 4:
        book_index = int(
            input("Enter the number of the book you want to edit: ")
            ) - 1
        if 0 <= book_index < len(library):
            edit_book(library[book_index])
        else:
            print("Invalid book number!")
    elif choice == 5:
        return
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main_menu(library, view_library)
