#include <iostream>
#include <algorithm>

#include "library.h"

using namespace std;

// Mise en minuscules sûre avec les caractères accentués
static string toLower(string s) {
    transform(s.begin(), s.end(), s.begin(),
              [](unsigned char c) { return static_cast<char>(tolower(c)); });
    return s;
}

// Constructor
Library::Library() {}

// Add book to library (refuse les ISBN en double)
bool Library::addBook(const Book& book) {
    if (findBookByISBN(book.getISBN())) {
        return false;
    }
    books.push_back(make_unique<Book>(book));
    return true;
}

// Remove book from library (impossible si le livre est emprunté)
bool Library::removeBook(const string& isbn) {
    auto it = find_if(books.begin(), books.end(),
        [&isbn](const unique_ptr<Book>& book) {
            return book->getISBN() == isbn;
        });
    
    if (it != books.end() && (*it)->getAvailability()) {
        books.erase(it);
        return true;
    }
    return false;
}

// Find book by ISBN
Book* Library::findBookByISBN(const string& isbn) {
    auto it = find_if(books.begin(), books.end(),
        [&isbn](const unique_ptr<Book>& book) {
            return book->getISBN() == isbn;
        });
    
    return (it != books.end()) ? it->get() : nullptr;
}

// Search books by title (case-insensitive partial match)
vector<Book*> Library::searchBooksByTitle(const string& title) {
    vector<Book*> results;
    string lowerTitle = toLower(title);
    
    for (auto& book : books) {
        if (toLower(book->getTitle()).find(lowerTitle) != string::npos) {
            results.push_back(book.get());
        }
    }
    return results;
}

// Search books by author (case-insensitive partial match)
vector<Book*> Library::searchBooksByAuthor(const string& author) {
    vector<Book*> results;
    string lowerAuthor = toLower(author);
    
    for (auto& book : books) {
        if (toLower(book->getAuthor()).find(lowerAuthor) != string::npos) {
            results.push_back(book.get());
        }
    }
    return results;
}

// Get all available books
vector<Book*> Library::getAvailableBooks() {
    vector<Book*> available;
    for (auto& book : books) {
        if (book->getAvailability()) {
            available.push_back(book.get());
        }
    }
    return available;
}

// Get all books
vector<Book*> Library::getAllBooks() {
    vector<Book*> allBooks;
    for (auto& book : books) {
        allBooks.push_back(book.get());
    }
    return allBooks;
}

// Description d'un livre avec le nom de l'emprunteur
string Library::describeBook(const Book* book) {
    string borrowerName;
    if (!book->getAvailability()) {
        User* user = findUserById(book->getBorrowerId());
        if (user) {
            borrowerName = user->getName();
        }
    }
    return book->toString(borrowerName);
}

// pas de doublons
bool Library::addUser(const User& user) {
    if (findUserById(user.getUserId())) {
        return false;
    }
    users.push_back(make_unique<User>(user));
    return true;
}

// Find user by ID
User* Library::findUserById(const string& userId) {
    auto it = find_if(users.begin(), users.end(),
        [&userId](const unique_ptr<User>& user) {
            return user->getUserId() == userId;
        });
    
    return (it != users.end()) ? it->get() : nullptr;
}

// Get all users
vector<User*> Library::getAllUsers() {
    vector<User*> allUsers;
    for (auto& user : users) {
        allUsers.push_back(user.get());
    }
    return allUsers;
}

// Check out book
bool Library::checkOutBook(const string& isbn, const string& userId) {
    Book* book = findBookByISBN(isbn);
    User* user = findUserById(userId);
    
    if (book && user && book->getAvailability()) {
        book->checkOut(user->getUserId());
        user->borrowBook(isbn);
        return true;
    }
    return false;
}

// Return book
bool Library::returnBook(const string& isbn) {
    Book* book = findBookByISBN(isbn);
    
    if (book && !book->getAvailability()) {
        User* user = findUserById(book->getBorrowerId());
        if (user) {
            user->returnBook(isbn);
        }
        book->returnBook();
        return true;
    }
    return false;
}

// Réconcilie les emprunts des livres et des utilisateurs (les livres font foi)
void Library::synchronizeLoans() {
    for (auto& user : users) {
        for (const string& isbn : user->getBorrowedBooks()) {
            Book* book = findBookByISBN(isbn);
            if (!book || book->getAvailability() ||
                book->getBorrowerId() != user->getUserId()) {
                user->returnBook(isbn);
            }
        }
    }
    for (auto& book : books) {
        if (!book->getAvailability()) {
            User* user = findUserById(book->getBorrowerId());
            if (user) {
                user->borrowBook(book->getISBN());
            } else {
                book->returnBook();
            }
        }
    }
}

// Display all books
void Library::displayAllBooks() {
    if (books.empty()) {
        cout << "Aucun livre dans la bibliothèque.\n";
        return;
    }
    
    cout << "\n=== TOUS LES LIVRES ===\n";
    for (size_t i = 0; i < books.size(); ++i) {
        cout << "\nLivre " << (i + 1) << " :\n";
        cout << describeBook(books[i].get()) << "\n";
        cout << "-------------------------\n";
    }
}

// Display available books
void Library::displayAvailableBooks() {
    auto available = getAvailableBooks();
    
    if (available.empty()) {
        cout << "Aucun livre disponible pour emprunt.\n";
        return;
    }
    
    cout << "\n=== LIVRES DISPONIBLES ===\n";
    for (size_t i = 0; i < available.size(); ++i) {
        cout << "\nLivre " << (i + 1) << " :\n";
        cout << describeBook(available[i]) << "\n";
        cout << "---------------------------\n";
    }
}

// Display all users
void Library::displayAllUsers() {
    if (users.empty()) {
        cout << "Aucun utilisateur enregistré.\n";
        return;
    }
    
    cout << "\n=== TOUS LES UTILISATEURS ===\n";
    for (size_t i = 0; i < users.size(); ++i) {
        cout << "\nUtilisateur " << (i + 1) << " :\n";
        cout << users[i]->toString() << "\n";
        cout << "------------------------------\n";
    }
}

// Statistics
int Library::getTotalBooks() const { return books.size(); }
int Library::getTotalUsers() const { return users.size(); }
int Library::getAvailableBookCount() const {
    return count_if(books.begin(), books.end(),
        [](const unique_ptr<Book>& book) {
            return book->getAvailability();
        });
}
int Library::getCheckedOutBookCount() const { return getTotalBooks() - getAvailableBookCount(); }