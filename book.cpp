#include <sstream>

#include "book.h"

using namespace std;

// Constructeur par défaut
Book::Book() : title(""), author(""), isbn(""), isAvailable(true), borrowerId("") {}

// Paramètres
Book::Book(const string& title, const string& author, const string& isbn)
    : title(title), author(author), isbn(isbn), isAvailable(true), borrowerId("") {}

// Getters
string Book::getTitle() const { return title; }
string Book::getAuthor() const { return author; }
string Book::getISBN() const { return isbn; }
bool Book::getAvailability() const { return isAvailable; }
string Book::getBorrowerId() const { return borrowerId; }

// Setters
void Book::setTitle(const string& title) { this->title = title; }
void Book::setAuthor(const string& author) { this->author = author; }
void Book::setISBN(const string& isbn) { this->isbn = isbn; }
void Book::setAvailability(bool available) { isAvailable = available; }
void Book::setBorrowerId(const string& id) { borrowerId = id; }

// Vérifie le livre à un prêteur
void Book::checkOut(const string& borrowerId) {
    isAvailable = false;
    this->borrowerId = borrowerId;
}

 // Retourne le livre de la librarie
void Book::returnBook() {
    isAvailable = true;
    borrowerId = "";
}

// Affichage du livre (affiche le nom de l'emprunteur s'il est fourni)
string Book::toString(const string& borrowerName) const {
    string result = "Titre: " + title + "\nAuteur: " + author + "\nISBN: " + isbn;
    result += "\nDisponibilité: " + string(isAvailable ? "Disponible" : "Emprunté");
    if (!isAvailable && !borrowerId.empty()) {
        result += "\nEmprunté par: " + (borrowerName.empty() ? borrowerId : borrowerName);
    }
    return result;
}

// Format du journal : titre|auteur|isbn|disponibilité|nom de l'emprunteur
string Book::toLogFormat(const string& borrowerName) const {
    return title + "|" + author + "|" + isbn + "|" +
           (isAvailable ? "1" : "0") + "|" + borrowerName;
}

// Format 
string Book::toFileFormat() const {
    return title + "|" + author + "|" + isbn + "|" +
           (isAvailable ? "1" : "0") + "|" + borrowerId;
}

// Parse from file format
void Book::fromFileFormat(const string& line) {
    stringstream ss(line);
    string availableStr;
    string borrower;

    getline(ss, title, '|');
    getline(ss, author, '|');
    getline(ss, isbn, '|');
    getline(ss, availableStr, '|');
    getline(ss, borrower, '|');

    isAvailable = (availableStr == "1");
    borrowerId = isAvailable ? "" : borrower;
}