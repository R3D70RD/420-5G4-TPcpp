#ifndef FILEMANAGER_H
#define FILEMANAGER_H

#include <string>

#include "library.h"

using namespace std;

// Racine du projet (si lancé depuis build/, on remonte d'un niveau)
string getProjectRoot();

class FileManager {
private:
    string booksFileName;
    string usersFileName;

public:
    // Constructor
    FileManager(const string& booksFile, const string& usersFile);
    
    // Indique si un répertoire de données a été fourni
    bool hasDataPaths() const;
    
    // File operations
    bool saveLibraryData(Library& library);
    bool loadLibraryData(Library& library);
    
    // Individual file operations
    bool saveBooksToFile(Library& library);
    bool saveUsersToFile(Library& library);
    bool loadBooksFromFile(Library& library);
    bool loadUsersFromFile(Library& library);
    
    // Utility methods
    bool fileExists(const string& filename);
    bool createBackup();
    
    // CSV
    bool exportToCSV(Library& library);
    bool importFromCSV(Library& library, const string& directory = "");
};

#endif