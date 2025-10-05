#!/usr/bin/env python
# coding: utf-8

# In[1]:


# library Management System (Python)
import os
import csv
from datetime import datetime, timedelta

def normalize_title(s: str) -> str:
    """Canonicalize a title for dictionary keys: trim, collapse inner spaces, case-insensitive."""
    # collapse multiple spaces, strip, and casefold (better than lower for unicode)
    return " ".join(s.split()).casefold()

# UserAccount Class to manage user data and borrowed books
class UserAccount:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.borrowed_books = []  # List of original titles (for display)
    
    def borrow_book(self, book_title):
        """Adds a book to the borrowed_books list."""
        self.borrowed_books.append(book_title)
    
    def return_book(self, book_title):
        """Removes a book from the borrowed_books list if exists."""
        if book_title in self.borrowed_books:
            self.borrowed_books.remove(book_title)
        else:
            raise ValueError("Book not found in borrowed list.")

# Librarian class inherits from UserAccount and manages book additions and removals
class Librarian(UserAccount):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)
    
    def add_book(self, book_manager, book_title):
        """Adds a new book to the library system (idempotent for same title)."""
        norm = normalize_title(book_title)
        book_manager.books[norm] = {"title": book_title.strip(), "status": "available"}
        book_manager.save_books()
    
    def remove_book(self, book_manager, book_title):
        """Removes a book from the system."""
        norm = normalize_title(book_title)
        if norm in book_manager.books:
            del book_manager.books[norm]
            book_manager.save_books()
        else:
            raise ValueError("Book not found in the system.")

# ManageBookLending class handles book lending and file operations
class ManageBookLending:
    def __init__(self, file_path='books.csv'):
        self.file_path = file_path
        self.books = self.load_books()  # dict: norm_title -> {"title": original_title, "status": str}
    
    def load_books(self):
        """Loads books from the CSV file into a normalized dictionary."""
        books = {}
        if os.path.exists(self.file_path):
            with open(self.file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    # skip empty/short rows
                    if not row or len(row) < 2:
                        continue
                    # skip header if present
                    if row[0].strip().lower() == "title" and row[1].strip().lower() == "status":
                        continue
                    title = row[0].strip()
                    status = row[1].strip().casefold()
                    if status not in ("available", "borrowed"):
                        # default to available if malformed
                        status = "available"
                    books[normalize_title(title)] = {"title": title, "status": status}
        else:
            print("No existing books file found. Creating a new one.")
        return books
    
    def save_books(self):
        """Saves the books dictionary to the CSV file with a header."""
        try:
            with open(self.file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["title", "status"])
                for data in self.books.values():
                    writer.writerow([data["title"], data["status"]])
        except Exception as e:
            print(f"Error saving books: {e}")
    
    def lend_book(self, user, book_title):
        """Handles lending a book to a user."""
        norm = normalize_title(book_title)
        if norm in self.books and self.books[norm]["status"] == "available":
            self.books[norm]["status"] = "borrowed"
            user.borrow_book(self.books[norm]["title"])  # store original title for display
            self.save_books()
        else:
            raise ValueError("Book is not available.")
    
    def mark_returned(self, book_title):
        """Marks a book as returned in the catalog."""
        norm = normalize_title(book_title)
        if norm in self.books:
            self.books[norm]["status"] = "available"
            self.save_books()

# ReturnsAndOverduePenalties class handles book returns and calculates penalties
class ReturnsAndOverduePenalties:
    def __init__(self, book_manager: ManageBookLending):
        self.return_records = {}
        self.book_manager = book_manager
    
    def return_book(self, user, book_title, borrow_date):
        """Handles returning of books and calculating overdue penalties."""
        try:
            user.return_book(book_title)
            self.book_manager.mark_returned(book_title)
            return_date = datetime.now()
            self.return_records[user.user_id] = return_date
            overdue_penalty = self.calculate_penalty(borrow_date)
            if overdue_penalty > 0:
                print(f"Overdue penalty for '{book_title}': ${overdue_penalty}")
            else:
                print(f"Book '{book_title}' returned successfully.")
        except ValueError as e:
            print(f"Error: {e}")
    
    def calculate_penalty(self, borrow_date):
        """Calculates overdue penalty based on the borrow date."""
        due_date = borrow_date + timedelta(days=14)
        overdue_days = (datetime.now() - due_date).days
        penalty_rate = 1
        return max(0, overdue_days * penalty_rate)

# Main function to interact with the user through the console
def main():
    # Initialize user, librarian, and book manager
    user = UserAccount("U001", "Alice")
    book_manager = ManageBookLending()
    return_manager = ReturnsAndOverduePenalties(book_manager)

    while True:
        # Display menu for user interaction
        print("\nLibrary Management System")
        print("1. View Available Books")
        print("2. Borrow Book")
        print("3. Return Book")
        print("4. View Borrowed Books")
        print("5. Add Book (Librarian)")
        print("6. Remove Book (Librarian)")
        print("7. Exit")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            # View available books
            if not book_manager.books:
                print("\nAvailable Books:\nNo books available")
            else:
                print("\nAvailable Books:")
                for data in book_manager.books.values():
                    print(f"- {data['title']} ({data['status']})")
        
        elif choice == '2':
            # Borrow a book
            book_title = input("Enter the book title to borrow: ").strip()
            try:
                book_manager.lend_book(user, book_title)
                print(f"You borrowed '{book_title.strip()}'")
            except ValueError as e:
                print(f"Error: {e}")
        
        elif choice == '3':
            # Return a book
            book_title = input("Enter the book title to return: ").strip()
            # In a real app you'd track/lookup the true borrow date per book.
            borrow_date = datetime.now()  # demo value
            return_manager.return_book(user, book_title, borrow_date)
        
        elif choice == '4':
            # View borrowed books
            if not user.borrowed_books:
                print("\nBorrowed Books:\nNo books borrowed")
            else:
                print("\nBorrowed Books:")
                for t in user.borrowed_books:
                    print(f"- {t}")
        
        elif choice == '5':
            # Add a book (Librarian)
            book_title = input("Enter the book title to add: ").strip()
            if not book_title:
                print("Title cannot be empty.")
                continue
            Librarian("L001", "Admin").add_book(book_manager, book_title)
            print(f"Book '{book_title}' added")
        
        elif choice == '6':
            # Remove a book (Librarian)
            book_title = input("Enter the book title to remove: ").strip()
            try:
                Librarian("L001", "Admin").remove_book(book_manager, book_title)
                print(f"Book '{book_title}' removed")
            except ValueError as e:
                print(f"Error: {e}")
        
        elif choice == '7':
            # Exit the program
            print("Exiting the Library Management System.")
            break
        
        else:
            print("Invalid choice. Please try again.")

# Run the main function
if __name__ == "__main__":
    main()


# In[ ]:




