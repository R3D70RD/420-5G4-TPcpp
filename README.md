# Construire le projet
Vous pouvez utiliser un dev container de base C++ de VScode.
Le projet utilise cmake, pensez à l'inclure dans votre dev container.

Voici les lignes de commandes pour compiler le projet:
```
$ mkdir build
$ cd build
$ cmake ..
$ make
```

# Répertoire data

Il contient 2 fichiers `books.txt`et `users.txt` que vous pouvez utilisez pour tester votre code.
Pour ca il suffit de donner chemin vers le repertoire data avec l'application `bibliotheque -d <chemin verrs data>`


# Veille Technologique : 
## Question 1. 
Nous avons pas en cours l'importation et l'exportation avec le C++. 
```
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
```

Dans cet extrait, le code extrait les données qui ont été sauvegardé dans la mémoire ram vers le disque ssd sous le format CSV.
1. const string dir = exportDirectory(); 
vérifie si le dossier existe sur le disque et ensuite utilise ofstream booksCsv(dir + "/books.csv"); pour écrire dans le fichier CSV les informations 1 par 1.
Il y a 3 étapes : 
1. la vérification/cération du dossier
2. la gestion des erreurs 
3. l'écriture

## Question 2.
Vu que ce projet est pratiquement une gestion de base de données de livres, utiliser une technologie de base de données pourrait être beaucoup mieux
que la sauvegarde sur un fichier CSV/txt. SQL ou même MangoDB intégration avec c++. Rendu là, probablement un API ferait du projet un meilleur succès, un site web,
une application mobile, tout cela pour une veille technologique.

> Projet terminé par Redford S. ST-M - 2235843
> - Fonctionnalitées : Export/Import CSV, Validation avant supprimer, Correction de bugs et Journal d'activités