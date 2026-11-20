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

# Interface graphique (pybind11 + customtkinter)

Prérequis (Ubuntu/Debian) :
```
$ sudo apt-get install -y python3-dev python3-venv python3-tk
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

Compilation du module Python (en plus de l'exe console) :
```
$ cmake -S . -B build -Dpybind11_DIR="$(python3 -m pybind11 --cmakedir)"
$ cmake --build build
```

Lancement de la GUI :
```
$ python gui/app.py
```

L'interface charge par défaut `data/` (livres et utilisateurs) et permet aussi de choisir un
autre dossier. Les exports CSV et le journal restent dans `export/` et `logs/` à la racine.
L'application console reste disponible : `./build/bibliotheque -d data`.

Tests automatisés (C++, bindings, service, smoke GUI) :
```
$ cmake -S . -B build -Dpybind11_DIR="$(python3 -m pybind11 --cmakedir)"
$ cmake --build build
$ ctest --test-dir build --output-on-failure
```

Tests C++ sous AddressSanitizer/UBSan :
```
$ cmake -S . -B build-san -DENABLE_SANITIZERS=ON -DBUILD_PYTHON_BINDINGS=OFF
$ cmake --build build-san
$ ctest --test-dir build-san --output-on-failure
```

Le test GUI est enregistré automatiquement si `xvfb-run` est présent ; sinon il peut être
lancé manuellement avec `xvfb-run -a python tests/test_gui_smoke.py`.

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