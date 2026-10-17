#include <fstream>
#include <iostream>
#include <filesystem>
#include "filemanager.h"

using namespace std;

// Constructor
FileManager::FileManager(const string& booksFile, const string& usersFile)
    : booksFileName(booksFile), usersFileName(usersFile) {}

// Save all library data
bool FileManager::saveLibraryData(Library& library) {
    return saveBooksToFile(library) && saveUsersToFile(library);
}

// Load all library data
bool FileManager::loadLibraryData(Library& library) {
    bool booksLoaded = loadBooksFromFile(library);
    bool usersLoaded = loadUsersFromFile(library);
    // fix : cohérence entre les emprunts des livres et ceux des utilisateurs
    library.synchronizeLoans();
    return booksLoaded || usersLoaded; // Return true if at least one file was loaded
}

// Save books to file
bool FileManager::saveBooksToFile(Library& library) {
    ofstream file(booksFileName);
    if (!file.is_open()) {
        cout << "Erreur : Impossible d'ouvrir " << booksFileName << " en écriture.\n";
        return false;
    }
    
    auto books = library.getAllBooks();
    for (Book* book : books) {
        file << book->toFileFormat() << "\n";
    }
    
    file.close();
    return true;
}

// Save users to file
bool FileManager::saveUsersToFile(Library& library) {
    ofstream file(usersFileName);
    if (!file.is_open()) {
        cout << "Erreur : Impossible d'ouvrir " << usersFileName << " en écriture.\n";
        return false;
    }
    
    auto users = library.getAllUsers();
    for (User* user : users) {
        file << user->toFileFormat() << "\n";
    }
    
    file.close();
    return true;
}

// Load books from file
bool FileManager::loadBooksFromFile(Library& library) {
    ifstream file(booksFileName);
    if (!file.is_open()) {
        cout << "Aucun fichier de livres existant trouvé. Démarrage avec une bibliothèque vide.\n";
        return false;
    }
    
    string line;
    int count = 0;
    while (getline(file, line)) {
        // Retire le '\r' des fichiers au format Windows
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) {
            Book book;
            book.fromFileFormat(line);
            // on ne compte que les livres réellement ajoutés (pas de doublons)
            if (library.addBook(book)) {
                count++;
            } else {
                cout << "Avertissement : ISBN en double ignoré (" << book.getISBN() << ").\n";
            }
        }
    }
    
    file.close();
    cout << "Chargé " << count << " livre(s) depuis le fichier.\n";
    return true;
}

// Load users from file
bool FileManager::loadUsersFromFile(Library& library) {
    ifstream file(usersFileName);
    if (!file.is_open()) {
        cout << "Aucun fichier d'utilisateurs existant trouvé. Démarrage sans utilisateurs enregistrés.\n";
        return false;
    }
    
    string line;
    int count = 0;
    while (getline(file, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) {
            User user;
            user.fromFileFormat(line);
            // fix pas de doublons d'ID
            if (library.addUser(user)) {
                count++;
            } else {
                cout << "Avertissement : ID en double ignoré (" << user.getUserId() << ").\n";
            }
        }
    }
    
    file.close();
    cout << "Chargé " << count << " utilisateur(s) depuis le fichier.\n";
    return true;
}

// Check if file exists
bool FileManager::fileExists(const string& filename) {
    ifstream file(filename);
    return file.good();
}

// Create backup
void FileManager::createBackup() {
    // fix : copy_file lançait une exception
    // si le .backup existait déjà)
    try {
        if (fileExists(booksFileName)) {
            filesystem::copy_file(booksFileName, booksFileName + ".backup",
                                  filesystem::copy_options::overwrite_existing);
        }
        
        if (fileExists(usersFileName)) {
            filesystem::copy_file(usersFileName, usersFileName + ".backup",
                                  filesystem::copy_options::overwrite_existing);
        }
        
        cout << "Fichiers de sauvegarde créés.\n";
    } catch (const filesystem::filesystem_error& e) {
        cout << "Erreur lors de la création de la sauvegarde : " << e.what() << "\n";
    }
}

// Nouvelle fonctionnalitée: Export en CSV, option 14
static string csvEscape(const string& value) {
    if (value.find_first_of(",\"\n") == string::npos) return value;
    string result = "\"";
    for (char c : value) {
        if (c == '"') result += '"';
        result += c;
    }
    return result + "\"";
}

// CSV dans le dossier export/
bool FileManager::exportToCSV(Library& library) {
    const string dir = "export";
    try {
        filesystem::create_directories(dir);
    } catch (const filesystem::filesystem_error& e) {
        cout << "Erreur : impossible de créer le dossier " << dir << " : " << e.what() << "\n";
        return false;
    }

    ofstream booksCsv(dir + "/books.csv");
    ofstream usersCsv(dir + "/users.csv");
    if (!booksCsv.is_open() || !usersCsv.is_open()) {
        cout << "Erreur : impossible d'écrire les fichiers CSV dans " << dir << "/.\n";
        return false;
    }

    // BOM UTF-8 pour que les accents s'affichent bien dans Excel
    booksCsv << "\xEF\xBB\xBF" << "Titre,Auteur,ISBN,Disponible,Emprunteur\n";
    for (Book* book : library.getAllBooks()) {
        booksCsv << csvEscape(book->getTitle()) << ","
                 << csvEscape(book->getAuthor()) << ","
                 << csvEscape(book->getISBN()) << ","
                 << (book->getAvailability() ? "Oui" : "Non") << ","
                 << csvEscape(book->getBorrowerId()) << "\n";
    }

    usersCsv << "\xEF\xBB\xBF" << "Nom,ID,Nombre de livres,ISBNs empruntés\n";
    for (User* user : library.getAllUsers()) {
        string isbns;
        for (const string& isbn : user->getBorrowedBooks()) {
            if (!isbns.empty()) isbns += ";";
            isbns += isbn;
        }
        usersCsv << csvEscape(user->getName()) << ","
                 << csvEscape(user->getUserId()) << ","
                 << user->getNumberOfBorrowedBooks() << ","
                 << csvEscape(isbns) << "\n";
    }

    cout << "Export terminé : " << dir << "/books.csv et " << dir << "/users.csv\n";
    return true;
}