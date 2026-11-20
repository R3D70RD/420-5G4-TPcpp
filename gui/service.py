"""Couche de service entre les bindings C++ et l'interface customtkinter."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
EXPORT_DIR = PROJECT_ROOT / "export"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import bibliotheque_py as biblio
except ImportError:
    sys.path.insert(0, str(PROJECT_ROOT / "build"))
    import bibliotheque_py as biblio

FORBIDDEN_CHARS = ("|", ",")


class LibraryError(Exception):
    """Erreur métier destinée à être affichée telle quelle dans la GUI."""


def validate_field(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise LibraryError(f"{label} ne peut pas être vide.")
    if any(char in value for char in FORBIDDEN_CHARS):
        raise LibraryError(f"{label} ne peut pas contenir les caractères '|' ou ','.")
    return value


class LibraryService:
    """Encapsule Library/FileManager/ActivityLogger pour une session GUI.

    Les objets Book/User renvoyés sont des références vers le C++ : ils restent
    valides tant que cette instance (et son Library) existe. La GUI ne doit pas
    les conserver après un rechargement des données.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        resolved_dir: Path | None = None
        if data_dir is not None:
            resolved_dir = Path(data_dir).expanduser()
            if not resolved_dir.is_absolute():
                resolved_dir = (Path.cwd() / resolved_dir).resolve()
            if not resolved_dir.is_dir():
                raise LibraryError(f"Le répertoire {resolved_dir} n'existe pas.")

        # Logs et exports sont résolus depuis la racine du projet.
        os.chdir(PROJECT_ROOT)

        self.data_dir = resolved_dir
        if resolved_dir is None:
            self.file_manager = biblio.FileManager("", "")
        else:
            self.file_manager = biblio.FileManager(
                str(resolved_dir / "books.txt"),
                str(resolved_dir / "users.txt"),
            )

        self.library = biblio.Library()
        self.logger = biblio.ActivityLogger()
        self.last_load_message = ""
        self._load()
        self.logger.log("DEMARRAGE")

    # --- Chargement / sauvegarde -----------------------------------------

    @property
    def has_data_dir(self) -> bool:
        return self.file_manager.has_data_paths()

    def _load(self) -> None:
        self.library = biblio.Library()
        _ok, message = self.file_manager.load_library_data(self.library)
        self.last_load_message = message.strip()

    def reload(self) -> str:
        self._load()
        return self.last_load_message

    def save(self) -> tuple[bool, str]:
        ok, message = self.file_manager.save_library_data(self.library)
        return ok, message.strip()

    def create_backup(self) -> tuple[bool, str]:
        return self.file_manager.create_backup()

    def export_csv(self) -> tuple[bool, str]:
        return self.file_manager.export_to_csv(self.library)

    def import_csv(self, directory: str = "") -> tuple[bool, str]:
        return self.file_manager.import_from_csv(self.library, directory)

    def shutdown(self) -> tuple[bool, str]:
        ok, message = (True, "")
        if self.has_data_dir:
            ok, message = self.save()
        self.logger.log("QUITTER")
        return ok, message

    # --- Livres -----------------------------------------------------------

    def add_book(self, title: str, author: str, isbn: str) -> None:
        title = validate_field(title, "Le titre")
        author = validate_field(author, "L'auteur")
        isbn = validate_field(isbn, "L'ISBN")

        if self.library.find_book_by_isbn(isbn) is not None:
            raise LibraryError(f"Un livre avec l'ISBN {isbn} existe déjà.")

        book = biblio.Book(title, author, isbn)
        if not self.library.add_book(book):
            raise LibraryError("Impossible d'ajouter ce livre.")
        self.logger.log("AJOUT LIVRE", book.to_log_format(""))

    def remove_book(self, isbn: str) -> None:
        isbn = validate_field(isbn, "L'ISBN")
        book = self.library.find_book_by_isbn(isbn)
        if book is None:
            raise LibraryError(f"Aucun livre avec l'ISBN {isbn}.")
        if not book.get_availability():
            raise LibraryError("Ce livre est actuellement emprunté, impossible de le supprimer.")

        log_line = book.to_log_format("")
        if not self.library.remove_book(isbn):
            raise LibraryError("La suppression du livre a échoué.")
        self.logger.log("SUPPRESSION LIVRE", log_line)

    def all_books(self) -> list:
        return self.library.get_all_books()

    def available_books(self) -> list:
        return self.library.get_available_books()

    def search_books_by_title(self, term: str) -> list:
        return self.library.search_books_by_title(term.strip())

    def search_books_by_author(self, term: str) -> list:
        return self.library.search_books_by_author(term.strip())

    def describe_book(self, book) -> str:
        return self.library.describe_book(book)

    # --- Utilisateurs -----------------------------------------------------

    def add_user(self, name: str, user_id: str) -> None:
        name = validate_field(name, "Le nom")
        user_id = validate_field(user_id, "L'ID")

        if self.library.find_user_by_id(user_id) is not None:
            raise LibraryError(f"Un utilisateur avec l'ID {user_id} existe déjà.")

        user = biblio.User(name, user_id)
        if not self.library.add_user(user):
            raise LibraryError("Impossible d'ajouter cet utilisateur.")
        self.logger.log("AJOUT UTILISATEUR", f"{name}|{user_id}")

    def all_users(self) -> list:
        return self.library.get_all_users()

    # --- Emprunts ---------------------------------------------------------

    def check_out(self, isbn: str, user_id: str) -> None:
        isbn = validate_field(isbn, "L'ISBN")
        user_id = validate_field(user_id, "L'ID utilisateur")

        book = self.library.find_book_by_isbn(isbn)
        if book is None:
            raise LibraryError(f"Aucun livre avec l'ISBN {isbn}.")
        user = self.library.find_user_by_id(user_id)
        if user is None:
            raise LibraryError(f"Aucun utilisateur avec l'ID {user_id}.")
        if not book.get_availability():
            raise LibraryError("Ce livre est déjà emprunté.")

        if not self.library.check_out_book(isbn, user_id):
            raise LibraryError("L'emprunt a échoué.")
        self.logger.log("EMPRUNT", book.to_log_format(user.get_name()))

    def return_book(self, isbn: str) -> None:
        isbn = validate_field(isbn, "L'ISBN")
        book = self.library.find_book_by_isbn(isbn)
        if book is None:
            raise LibraryError(f"Aucun livre avec l'ISBN {isbn}.")
        if book.get_availability():
            raise LibraryError("Ce livre n'est pas emprunté.")

        borrower = self.library.find_user_by_id(book.get_borrower_id())
        borrower_name = borrower.get_name() if borrower is not None else book.get_borrower_id()
        log_line = book.to_log_format(borrower_name)

        if not self.library.return_book(isbn):
            raise LibraryError("Le retour a échoué.")
        self.logger.log("RETOUR", log_line)

    def checked_out_books(self) -> list:
        return [book for book in self.library.get_all_books() if not book.get_availability()]

    # --- Statistiques / journal ------------------------------------------

    def statistics(self) -> dict[str, int]:
        return {
            "total_books": self.library.get_total_books(),
            "available_books": self.library.get_available_book_count(),
            "checked_out_books": self.library.get_checked_out_book_count(),
            "total_users": self.library.get_total_users(),
        }

    def activity(self, count: int = 20) -> list[str]:
        return self.logger.get_last_entries(count)

    def log_path(self) -> str:
        return self.logger.get_log_path()
