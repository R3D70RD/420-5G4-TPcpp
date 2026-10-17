#include <sstream>
#include <algorithm>

#include "user.h"

using namespace std;

// Default constructor
User::User() : name(""), userId("") {}

// Parameterized constructor
User::User(const string& name, const string& userId) 
    : name(name), userId(userId) {}

// Getters
string User::getName() const { return name; }
string User::getUserId() const { return userId; }
vector<string> User::getBorrowedBooks() const { return borrowedBooks; }

// Setters
void User::setName(const string& name) { this->name = name; }
void User::setUserId(const string& userId) { this->userId = userId; }

// Borrow a book
void User::borrowBook(const string& isbn) {
    if (!hasBorrowedBook(isbn)) {
        borrowedBooks.push_back(isbn);
    }
}

// Return a book
void User::returnBook(const string& isbn) {
    auto it = find(borrowedBooks.begin(), borrowedBooks.end(), isbn);
    if (it != borrowedBooks.end()) {
        borrowedBooks.erase(it);
    }
}

// Check if user has borrowed a specific book
bool User::hasBorrowedBook(const string& isbn) const {
    return find(borrowedBooks.begin(), borrowedBooks.end(), isbn) != borrowedBooks.end();
}

// Get number of borrowed books
int User::getNumberOfBorrowedBooks() const {
    return borrowedBooks.size();
}

// Display user information
string User::toString() const {
    string result = "Nom: " + name + "\nID: " + userId + 
                        "\nLivres empruntés : " + to_string(borrowedBooks.size());
    
    if (!borrowedBooks.empty()) {
        result += "\nISBNs: ";
        for (size_t i = 0; i < borrowedBooks.size(); ++i) {
            result += borrowedBooks[i];
            if (i < borrowedBooks.size() - 1) result += ", ";
        }
    }
    return result;
}

// Format for file storage
string User::toFileFormat() const {
    string result = name + "|" + userId + "|";
    for (size_t i = 0; i < borrowedBooks.size(); ++i) {
        result += borrowedBooks[i];
        if (i < borrowedBooks.size() - 1) result += ",";
    }
    return result;
}

// Parse from file format
void User::fromFileFormat(const string& line) {
    stringstream ss(line);
    
    getline(ss, name, '|');
    getline(ss, userId, '|');
    
    string booksStr;
    getline(ss, booksStr, '|');
    
    borrowedBooks.clear();
    if (!booksStr.empty()) {
        stringstream booksSs(booksStr);
        string isbn;
        while (getline(booksSs, isbn, ',')) {
            if (!isbn.empty()) {
                borrowedBooks.push_back(isbn);
            }
        }
    }
}