#include <fstream>
#include <iostream>
#include <filesystem>
#include <sstream>
#include <vector>
#include "filemanager.h"

using namespace std;

// Détecte la racine du projet : depuis build/ (ou un dossier CMake), on remonte d'un niveau
string getProjectRoot() {
    filesystem::path cwd = filesystem::current_path();
    bool inBuildDir = cwd.filename() == "build" ||
                      filesystem::exists(cwd / "CMakeCache.txt");
    if (inBuildDir && cwd.has_parent_path()) {
        return cwd.parent_path().string();
    }
    return cwd.string();
}

static string exportDirectory() {
    return (filesystem::path(getProjectRoot()) / "export").string();
}

static const char* NO_DATA_DIR_MESSAGE =
    "Aucun répertoire de données (--data-dir) : ";

// Constructor
FileManager::FileManager(const string& booksFile, const string& usersFile)
    : booksFileName(booksFile), usersFileName(usersFile) {}

bool FileManager::hasDataPaths() const {
    return !booksFileName.empty() && !usersFileName.empty();
}

// Save all library data
bool FileManager::saveLibraryData(Library& library) {
    if (!hasDataPaths()) {
        cout << NO_DATA_DIR_MESSAGE
             << "sauvegarde impossible, les données ne seront pas conservées.\n";
        return false;
    }
    return saveBooksToFile(library) && saveUsersToFile(library);
}

// Load all library data
bool FileManager::loadLibraryData(Library& library) {
    if (!hasDataPaths()) {
        cout << NO_DATA_DIR_MESSAGE
             << "chargement désactivé, démarrage avec une bibliothèque vide.\n";
        return false;
    }
    bool booksLoaded = loadBooksFromFile(library);
    bool usersLoaded = loadUsersFromFile(library);
    library.synchronizeLoans();
    return booksLoaded || usersLoaded;
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
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) {
            Book book;
            book.fromFileFormat(line);
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
bool FileManager::createBackup() {
    if (!hasDataPaths()) {
        cout << NO_DATA_DIR_MESSAGE << "aucune sauvegarde de secours possible.\n";
        return false;
    }
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
        return true;
    } catch (const filesystem::filesystem_error& e) {
        cout << "Erreur lors de la création de la sauvegarde : " << e.what() << "\n";
        return false;
    }
}

// Échappe un champ CSV
static string csvEscape(const string& value) {
    if (value.find_first_of(",\"\n") == string::npos) return value;
    string result = "\"";
    for (char c : value) {
        if (c == '"') result += '"';
        result += c;
    }
    return result + "\"";
}

// Découpe une ligne CSV en champs (gère les guillemets)
static vector<string> parseCsvLine(const string& line) {
    vector<string> fields;
    string current;
    bool inQuotes = false;
    for (size_t i = 0; i < line.size(); ++i) {
        char c = line[i];
        if (inQuotes) {
            if (c == '"') {
                if (i + 1 < line.size() && line[i + 1] == '"') {
                    current += '"';
                    ++i;
                } else {
                    inQuotes = false;
                }
            } else {
                current += c;
            }
        } else if (c == '"') {
            inQuotes = true;
        } else if (c == ',') {
            fields.push_back(current);
            current.clear();
        } else {
            current += c;
        }
    }
    fields.push_back(current);
    return fields;
}

// Lit un fichier CSV (en-tête ignorée). Retourne false si le fichier est introuvable.
static bool readCsvRows(const string& path, vector<vector<string>>& rows) {
    ifstream file(path);
    if (!file.is_open()) return false;

    string line;
    bool header = true;
    while (getline(file, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (header) {
            header = false;
            continue;
        }
        if (!line.empty()) rows.push_back(parseCsvLine(line));
    }
    return true;
}

// Export basique en CSV dans le dossier export/ à la racine du projet
bool FileManager::exportToCSV(Library& library) {
    const string dir = exportDirectory();
    try {
        filesystem::create_directories(dir);
    } catch (const filesystem::filesystem_error& e) {
        cout << "Erreur : impossible de créer le dossier " << dir << " : " << e.what() << "\n";
        return false;
    }

    ofstream booksCsv(dir + "/books.csv");
    ofstream usersCsv(dir + "/users.csv");
    if (!booksCsv.is_open() || !usersCsv.is_open()) {
        cout << "Erreur : impossible d'écrire les fichiers CSV dans " << dir << ".\n";
        return false;
    }

    // BOM UTF-8 pour un affichage correct des accents dans Excel
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

    cout << "Export terminé dans : " << dir << "\n";
    return true;
}

// Import CSV (books.csv et users.csv) : ajoute les nouvelles entrées, ignore doublons et lignes invalides
bool FileManager::importFromCSV(Library& library, const string& directory) {
    const string dir = directory.empty() ? exportDirectory() : directory;

    vector<vector<string>> bookRows, userRows;
    bool booksFound = readCsvRows((filesystem::path(dir) / "books.csv").string(), bookRows);
    bool usersFound = readCsvRows((filesystem::path(dir) / "users.csv").string(), userRows);

    if (!booksFound && !usersFound) {
        cout << "Erreur : aucun fichier books.csv ou users.csv trouvé dans " << dir << ".\n";
        return false;
    }

    int booksAdded = 0, usersAdded = 0, ignored = 0;

    for (const auto& f : bookRows) {
        if (f.size() < 3 || f[0].empty() || f[1].empty() || f[2].empty() ||
            f[0].find('|') != string::npos || f[1].find('|') != string::npos ||
            f[2].find('|') != string::npos) {
            ignored++;
            continue;
        }
        Book book(f[0], f[1], f[2]);
        if (f.size() >= 5 && f[3] == "Non" && !f[4].empty()) {
            book.setAvailability(false);
            book.setBorrowerId(f[4]);
        }
        if (library.addBook(book)) booksAdded++; else ignored++;
    }

    for (const auto& f : userRows) {
        if (f.size() < 2 || f[0].empty() || f[1].empty() ||
            f[0].find('|') != string::npos || f[1].find('|') != string::npos) {
            ignored++;
            continue;
        }
        User user(f[0], f[1]);
        if (f.size() >= 4) {
            stringstream ss(f[3]);
            string isbn;
            while (getline(ss, isbn, ';')) {
                if (!isbn.empty()) user.borrowBook(isbn);
            }
        }
        if (library.addUser(user)) usersAdded++; else ignored++;
    }

    library.synchronizeLoans();

    cout << "Import terminé : " << booksAdded << " livre(s) et " << usersAdded
         << " utilisateur(s) ajouté(s), " << ignored
         << " ligne(s) ignorée(s) (doublons ou invalides).\n";
    return true;
}