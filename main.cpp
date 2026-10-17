// Biblios
#include <iostream>
#include <limits>
#include <string>
#include <filesystem>
// inclure ces classes
#include "library.h"
#include "filemanager.h"
#include "activitylogger.h" 

using namespace std;

// méthode qui efface l'écran (Windows/Linux)
void clearScreen() {
    system("cls || clear");
}

// fix du double "Entrée"
// méthode qui pause l'éxécution jusqu'à "Entrée"
void pauseForInput() {
    cout << "\nAppuyez sur Entrée pour continuer...";
    string dummy;
    getline(cin, dummy);
}

// méthode que affiche le menu principal
void displayMenu() {
    cout << "\n=== SYSTÈME DE GESTION DE BIBLIOTHÈQUE PERSONNELLE ===\n";
    cout << "1.  Ajouter un Livre\n";
    cout << "2.  Supprimer un Livre\n";
    cout << "3.  Rechercher des Livres par Titre\n";
    cout << "4.  Rechercher des Livres par Auteur\n";
    cout << "5.  Afficher Tous les Livres\n";
    cout << "6.  Afficher les Livres Disponibles\n";
    cout << "7.  Ajouter un Utilisateur\n";
    cout << "8.  Afficher Tous les Utilisateurs\n";
    cout << "9.  Emprunter un Livre\n";
    cout << "10. Retourner un Livre\n";
    cout << "11. Statistiques de la Bibliothèque\n";
    cout << "12. Sauvegarder les Données\n";
    cout << "13. Créer une Sauvegarde\n";
    cout << "14. Exporter en CSV\n"; // Nouvelle fonctionnalitée
    cout << "15. Consulter le journal d'activités\n"; // Nouvelle fonctionnalitée
    cout << "0.  Quitter\n";
    cout << "======================================================\n";
    cout << "Entrez votre choix : ";
}

// CORRECTION : retire les espaces en début/fin de saisie
static string trim(const string& s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    if (start == string::npos) return "";
    size_t end = s.find_last_not_of(" \t\r\n");
    return s.substr(start, end - start + 1);
}

// méthode qui recoit un argument de l'user
string getInput(const string& prompt) {
    string input;
    cout << prompt;
    getline(cin, input);
    return trim(input);
}

// '|' et ',' casseraient le format des fichiers ; champ vide interdit
static bool isValidField(const string& value, const string& label) {
    if (value.empty()) {
        cout << "Erreur : " << label << " ne peut pas être vide.\n";
        return false;
    }
    if (value.find('|') != string::npos || value.find(',') != string::npos) {
        cout << "Erreur : " << label << " ne peut pas contenir les caractères '|' ou ','.\n";
        return false;
    }
    return true;
}

// fonctionalité ajoutée : demande de confirmation (o/n).
static bool confirmAction(const string& message) {
    string answer = getInput(message + " (o/n) : ");
    for (char& c : answer) c = static_cast<char>(tolower(static_cast<unsigned char>(c)));
    return answer == "o" || answer == "oui";
}

// lecture du choix par ligne complète.
// Retourne -1 si saisie invalide, -2 si fin de flux (EOF).
static int readChoice() {
    string line;
    if (!getline(cin, line)) return -2;
    line = trim(line);
    try {
        size_t pos = 0;
        int value = stoi(line, &pos);
        if (pos != line.size()) return -1; // ex: "12abc"
        return value;
    } catch (...) {
        return -1;
    }
}

// 
void printUsage(const char* programName) {
    cerr << "Usage: " << programName << " [--data-dir|-d <répertoire>]\n";
}

int main(int argc, char* argv[]) {
    string dataDir;

    for (int i = 1; i < argc; ++i) {
        string arg = argv[i];
        if (arg == "--data-dir" || arg == "-d") {
            if (i + 1 >= argc) {
                cerr << "Erreur : " << arg << " nécessite un répertoire.\n";
                printUsage(argv[0]);
                return 1;
            }
            dataDir = argv[++i];
        } else {
            cerr << "Erreur : argument inconnu '" << arg << "'.\n";
            printUsage(argv[0]);
            return 1;
        }
    }

    // CORRECTION : noms de fichiers par défaut (étaient vides sans --data-dir)
    string booksFile = "books.txt";
    string usersFile = "users.txt";
    if (!dataDir.empty()) {
        if (!filesystem::is_directory(dataDir)) {
            cerr << "Erreur : le répertoire " << dataDir << " n'existe pas.\n";
            printUsage(argv[0]);
            return 1;
        }
        booksFile = (filesystem::path(dataDir) / "books.txt").string();
        usersFile = (filesystem::path(dataDir) / "users.txt").string();
    }

    Library library;
    FileManager fileManager(booksFile, usersFile);
    ActivityLogger logger; // NOUVEAU
    
    // Load existing data
    cout << "Chargement des données de la bibliothèque...\n";
    fileManager.loadLibraryData(library);
    logger.log("DEMARRAGE"); // NOUVEAU
    
    bool running = true;
    
    while (running) {
        displayMenu();
        
        // CORRECTION : lecture robuste du choix + gestion de l'EOF
        int choice = readChoice();
        if (choice == -2) { // fin de l'entrée : on quitte proprement
            cout << "\nFin de l'entrée. Sauvegarde des données...\n";
            fileManager.saveLibraryData(library);
            break;
        }
        if (choice == -1) {
            cout << "Saisie invalide. Veuillez entrer un nombre.\n";
            pauseForInput();
            continue;
        }
        
        switch (choice) {
            case 1: { // Add Book
                string title = getInput("Entrez le titre du livre : ");
                string author = getInput("Entrez l'auteur du livre : ");
                string isbn = getInput("Entrez l'ISBN du livre : ");
                
                // CORRECTION : validation des champs
                if (!isValidField(title, "Le titre") ||
                    !isValidField(author, "L'auteur") ||
                    !isValidField(isbn, "L'ISBN")) {
                    // message déjà affiché
                } else if (library.findBookByISBN(isbn)) {
                    cout << "Erreur : Un livre avec l'ISBN " << isbn << " existe déjà.\n";
                } else {
                    Book newBook(title, author, isbn);
                    library.addBook(newBook);
                    logger.log("AJOUT_LIVRE", "ISBN " + isbn + " - " + title); // NOUVEAU
                    cout << "Livre ajouté avec succès !\n";
                }
                pauseForInput();
                break;
            }
            
            case 2: { // Remove Book
                string isbn = getInput("Entrez l'ISBN du livre à supprimer : ");
                Book* book = library.findBookByISBN(isbn);
                
                // CORRECTION : message distinct si le livre est emprunté
                if (!book) {
                    cout << "Livre non trouvé.\n";
                } else if (!book->getAvailability()) {
                    cout << "Erreur : ce livre est actuellement emprunté, impossible de le supprimer.\n";
                } else if (!confirmAction("Supprimer « " + book->getTitle() + " » ?")) {
                    
                    // confirmation avant suppression
                    cout << "Suppression annulée.\n";
                } else if (library.removeBook(isbn)) {
                    logger.log("SUPPRESSION_LIVRE", "ISBN " + isbn); // NOUVEAU
                    cout << "Livre supprimé avec succès !\n";
                } else {
                    cout << "Livre non trouvé.\n";
                }
                pauseForInput();
                break;
            }
            
            case 3: { // Search by Title
                string title = getInput("Entrez le titre à rechercher : ");
                auto results = library.searchBooksByTitle(title);
                
                if (results.empty()) {
                    cout << "Aucun livre trouvé avec ce titre.\n";
                } else {
                    cout << "\n=== RÉSULTATS DE RECHERCHE ===\n";
                    for (size_t i = 0; i < results.size(); ++i) {
                        cout << "\nRésultat " << (i + 1) << " :\n";
                        cout << results[i]->toString() << "\n";
                        cout << "-----------------------------\n";
                    }
                }
                pauseForInput();
                break;
            }
            
            case 4: { // Search by Author
                string author = getInput("Entrez l'auteur à rechercher : ");
                auto results = library.searchBooksByAuthor(author);
                
                if (results.empty()) {
                    cout << "Aucun livre trouvé de cet auteur.\n";
                } else {
                    cout << "\n=== RÉSULTATS DE RECHERCHE ===\n";
                    for (size_t i = 0; i < results.size(); ++i) {
                        cout << "\nRésultat " << (i + 1) << " :\n";
                        cout << results[i]->toString() << "\n";
                        cout << "-----------------------------\n";
                    }
                }
                pauseForInput();
                break;
            }
            
            case 5: // Display All Books
                library.displayAllBooks();
                pauseForInput();
                break;
            
            case 6: // Display Available Books
                library.displayAvailableBooks();
                pauseForInput();
                break;
            
            case 7: { // Add User
                string name = getInput("Entrez le nom de l'utilisateur : ");
                string userId = getInput("Entrez l'ID de l'utilisateur : ");
                
                // CORRECTION : validation des champs
                if (!isValidField(name, "Le nom") ||
                    !isValidField(userId, "L'ID")) {
                    // message déjà affiché
                } else if (library.findUserById(userId)) {
                    cout << "Erreur : Un utilisateur avec l'ID " << userId << " existe déjà.\n";
                } else {
                    User newUser(name, userId);
                    library.addUser(newUser);
                    logger.log("AJOUT_UTILISATEUR", "ID " + userId + " - " + name); // NOUVEAU
                    cout << "Utilisateur ajouté avec succès !\n";
                }
                pauseForInput();
                break;
            }
            
            case 8: // Display All Users
                library.displayAllUsers();
                pauseForInput();
                break;
            
            case 9: { // Check Out Book
                string isbn = getInput("Entrez l'ISBN du livre à emprunter : ");
                string userId = getInput("Entrez l'ID de l'utilisateur : ");
                
                if (library.checkOutBook(isbn, userId)) {
                    cout << "Livre emprunté avec succès !\n";
                    logger.log("EMPRUNT", "ISBN " + isbn + " - utilisateur " + userId); // NOUVEAU
                } else {
                    cout << "Erreur : Impossible d'emprunter le livre. Vérifiez l'ISBN, l'ID utilisateur et la disponibilité du livre.\n";
                }
                pauseForInput();
                break;
            }
            
            case 10: { // Return Book
                string isbn = getInput("Entrez l'ISBN du livre à retourner : ");
                // NOUVEAU : retenir l'emprunteur avant le retour (pour le journal)
                Book* borrowedBook = library.findBookByISBN(isbn);
                string borrower = borrowedBook ? borrowedBook->getBorrowerId() : "";
                
                if (library.returnBook(isbn)) {
                    cout << "Livre retourné avec succès !\n";
                    logger.log("RETOUR", "ISBN " + isbn + " - utilisateur " + borrower); // NOUVEAU
                } else {
                    cout << "Erreur : Impossible de retourner le livre. Vérifiez l'ISBN et que le livre est bien emprunté.\n";
                }
                pauseForInput();
                break;
            }
            
            case 11: { // Library Statistics
                cout << "\n=== STATISTIQUES DE LA BIBLIOTHÈQUE ===\n";
                cout << "Total des Livres : " << library.getTotalBooks() << "\n";
                cout << "Livres Disponibles : " << library.getAvailableBookCount() << "\n";
                cout << "Livres Empruntés : " << library.getCheckedOutBookCount() << "\n";
                cout << "Total des Utilisateurs : " << library.getTotalUsers() << "\n"; // CORRECTION
                pauseForInput();
                break;
            }
            
            case 12: { // Save Data
                if (fileManager.saveLibraryData(library)) {
                    cout << "Données de la bibliothèque sauvegardées avec succès !\n";
                    logger.log("SAUVEGARDE"); // NOUVEAU
                } else {
                    cout << "Erreur lors de la sauvegarde des données de la bibliothèque.\n";
                }
                pauseForInput();
                break;
            }
            
            case 13: { // Create Backup
                fileManager.createBackup();
                logger.log("SAUVEGARDE_SECOURS"); // NOUVEAU
                pauseForInput();
                break;
            }
            
            case 14: { // Export CSV 
                if (fileManager.exportToCSV(library)) {
                    logger.log("EXPORT_CSV"); // NOUVEAU
                }
                pauseForInput();
                break;
            }
            
            case 15: { // Journal d'activités 
                auto entries = logger.getLastEntries(20);
                if (entries.empty()) {
                    cout << "Le journal est vide.\n";
                } else {
                    cout << "\n=== JOURNAL D'ACTIVITÉS (20 dernières entrées) ===\n";
                    for (const string& entry : entries) {
                        cout << entry << "\n";
                    }
                }
                pauseForInput();
                break;
            }
            
            case 0: // Exit
                cout << "Sauvegarde des données avant la fermeture...\n";
                // Signaler un échec de sauvegarde
                if (!fileManager.saveLibraryData(library)) {
                    cout << "Attention : la sauvegarde a échoué !\n";
                }
                logger.log("QUITTER"); // NOUVEAU
                cout << "Merci d'avoir utilisé le Système de Gestion de Bibliothèque Personnelle !\n";
                running = false;
                break;
            
            default:
                cout << "Choix invalide. Veuillez réessayer.\n";
                pauseForInput();
                break;
        }
    }
    
    return 0;
}