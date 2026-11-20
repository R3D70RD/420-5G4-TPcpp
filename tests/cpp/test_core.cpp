#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

#include "activitylogger.h"
#include "filemanager.h"
#include "library.h"

using namespace std;
namespace fs = std::filesystem;

static int failures = 0;

#define CHECK(condition)                                                        \
    do {                                                                        \
        if (!(condition)) {                                                     \
            cerr << "ECHEC " << __FILE__ << ":" << __LINE__                     \
                 << " : " #condition "\n";                                      \
            ++failures;                                                         \
        }                                                                       \
    } while (0)

static fs::path makeTempDir() {
    static int counter = 0;
    const auto stamp = chrono::steady_clock::now().time_since_epoch().count();
    fs::path dir = fs::temp_directory_path() /
                   ("bibliotheque_test_" + to_string(stamp) + "_" + to_string(counter++));
    fs::create_directories(dir);
    return dir;
}

static void testLibraryOperations() {
    Library library;
    CHECK(library.getTotalBooks() == 0);
    CHECK(library.addBook(Book("Titre", "Auteur", "ISBN1")));
    CHECK(!library.addBook(Book("Doublon", "X", "ISBN1")));

    Book* book = library.findBookByISBN("ISBN1");
    CHECK(book != nullptr);
    CHECK(library.findBookByISBN("INCONNU") == nullptr);

    CHECK(library.addUser(User("Marie", "U1")));
    CHECK(!library.addUser(User("Autre", "U1")));
    CHECK(library.findUserById("U2") == nullptr);

    CHECK(library.checkOutBook("ISBN1", "U1"));
    CHECK(!library.checkOutBook("ISBN1", "U1"));
    CHECK(library.getCheckedOutBookCount() == 1);
    CHECK(!library.removeBook("ISBN1"));
    CHECK(library.returnBook("ISBN1"));
    CHECK(library.getAvailableBookCount() == 1);
    CHECK(library.removeBook("ISBN1"));
    CHECK(library.getTotalBooks() == 0);
}

static void testLoanSynchronization() {
    Library library;
    library.addBook(Book("Livre A", "Auteur", "I1"));
    library.addBook(Book("Livre B", "Auteur", "I2"));
    library.addBook(Book("Livre C", "Auteur", "I3"));
    library.addUser(User("Marie", "U1"));

    User* user = library.findUserById("U1");
    CHECK(user != nullptr);
    if (user == nullptr) return;

    user->borrowBook("I1");
    user->borrowBook("INCONNU");

    Book* bookB = library.findBookByISBN("I2");
    CHECK(bookB != nullptr);
    if (bookB != nullptr) {
        bookB->setAvailability(false);
        bookB->setBorrowerId("U1");
    }

    Book* bookC = library.findBookByISBN("I3");
    CHECK(bookC != nullptr);
    if (bookC != nullptr) {
        bookC->setAvailability(false);
        bookC->setBorrowerId("UTILISATEUR_INCONNU");
    }

    library.synchronizeLoans();

    CHECK(!user->hasBorrowedBook("I1"));
    CHECK(!user->hasBorrowedBook("INCONNU"));
    CHECK(user->hasBorrowedBook("I2"));
    if (bookC != nullptr) {
        CHECK(bookC->getAvailability());
    }
}

static void testFileManagerPersistence() {
    const fs::path dir = makeTempDir();
    const string booksFile = (dir / "books.txt").string();
    const string usersFile = (dir / "users.txt").string();
    FileManager manager(booksFile, usersFile);

    Library library;
    library.addBook(Book("Titre", "Auteur", "ISBN1"));
    library.addUser(User("Marie", "U1"));

    CHECK(manager.saveLibraryData(library));
    CHECK(fs::exists(booksFile));
    CHECK(fs::exists(usersFile));
    CHECK(!fs::exists(booksFile + ".tmp"));
    CHECK(manager.createBackup());
    CHECK(fs::exists(booksFile + ".backup"));
    CHECK(fs::exists(usersFile + ".backup"));

    Library restored;
    CHECK(manager.loadLibraryData(restored));
    CHECK(restored.getTotalBooks() == 1);
    CHECK(restored.getTotalUsers() == 1);

    const fs::path oldCwd = fs::current_path();
    fs::current_path(dir);
    CHECK(manager.exportToCSV(library));
    fs::current_path(oldCwd);
    CHECK(fs::exists(dir / "export" / "books.csv"));
    CHECK(fs::exists(dir / "export" / "users.csv"));

    Library imported;
    CHECK(manager.importFromCSV(imported, (dir / "export").string()));
    CHECK(imported.getTotalBooks() == 1);
    CHECK(imported.getTotalUsers() == 1);

    fs::remove_all(dir);
}

static void testInvalidDataIsIgnored() {
    const fs::path dir = makeTempDir();
    const string booksFile = (dir / "books.txt").string();
    const string usersFile = (dir / "users.txt").string();

    {
        ofstream books(booksFile);
        books << "||||\n"
              << "Titre sans ISBN|Auteur\n"
              << "Titre valide|Auteur|ISBN9|1|\n";
    }
    {
        ofstream users(usersFile);
        users << "|\n"
              << "Nom sans ID\n"
              << "Nom valide|U9|\n";
    }

    FileManager manager(booksFile, usersFile);
    Library library;
    manager.loadLibraryData(library);

    CHECK(library.getTotalBooks() == 1);
    CHECK(library.findBookByISBN("ISBN9") != nullptr);
    CHECK(library.getTotalUsers() == 1);
    CHECK(library.findUserById("U9") != nullptr);

    fs::remove_all(dir);
}

static void testSaveFailureDoesNotCrash() {
    const fs::path dir = makeTempDir();
    FileManager manager((dir / "absent" / "books.txt").string(),
                        (dir / "absent" / "users.txt").string());

    Library library;
    library.addBook(Book("Titre", "Auteur", "ISBN1"));
    CHECK(!manager.saveLibraryData(library));

    fs::remove_all(dir);
}

static void testActivityLogger() {
    const fs::path dir = makeTempDir();
    const fs::path oldCwd = fs::current_path();
    fs::current_path(dir);

    ActivityLogger logger;
    logger.log("TEST", "details");
    const vector<string> entries = logger.getLastEntries(5);
    CHECK(!entries.empty());
    if (!entries.empty()) {
        CHECK(entries.back().find("[TEST]") != string::npos);
    }

    fs::current_path(oldCwd);
    fs::remove_all(dir);
}

int main() {
    testLibraryOperations();
    testLoanSynchronization();
    testFileManagerPersistence();
    testInvalidDataIsIgnored();
    testSaveFailureDoesNotCrash();
    testActivityLogger();

    if (failures != 0) {
        cerr << failures << " test(s) C++ en échec.\n";
        return 1;
    }
    cout << "OK: tests C++ du coeur\n";
    return 0;
}
