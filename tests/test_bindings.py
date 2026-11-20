"""Tests des bindings bibliotheque_py (sans GUI)."""

import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD_DIR))

import bibliotheque_py as biblio  # noqa: E402


@contextmanager
def working_directory(path):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class LibraryTests(unittest.TestCase):
    def test_books_users_and_loans(self):
        library = biblio.Library()
        self.assertEqual(library.get_total_books(), 0)

        self.assertTrue(library.add_book(biblio.Book("Titre", "Auteur", "ISBN1")))
        self.assertFalse(library.add_book(biblio.Book("Doublon", "X", "ISBN1")))

        book = library.find_book_by_isbn("ISBN1")
        self.assertIsNotNone(book)
        self.assertEqual(book.get_title(), "Titre")
        self.assertIsNone(library.find_book_by_isbn("INCONNU"))

        self.assertTrue(library.add_user(biblio.User("Marie", "U1")))
        self.assertFalse(library.add_user(biblio.User("Autre", "U1")))
        self.assertIsNone(library.find_user_by_id("U2"))

        self.assertTrue(library.check_out_book("ISBN1", "U1"))
        self.assertFalse(library.check_out_book("ISBN1", "U1"))
        self.assertFalse(book.get_availability())
        self.assertTrue(library.find_user_by_id("U1").has_borrowed_book("ISBN1"))
        self.assertEqual(library.get_checked_out_book_count(), 1)
        self.assertFalse(library.remove_book("ISBN1"))

        self.assertTrue(library.return_book("ISBN1"))
        self.assertFalse(library.find_user_by_id("U1").has_borrowed_book("ISBN1"))
        self.assertEqual(library.get_available_book_count(), 1)
        self.assertTrue(library.remove_book("ISBN1"))
        self.assertEqual(library.get_total_books(), 0)

    def test_search_and_describe(self):
        library = biblio.Library()
        library.add_book(biblio.Book("Le Petit Prince", "Antoine", "ISBN1"))
        library.add_book(biblio.Book("Les Misérables", "Victor Hugo", "ISBN2"))

        self.assertEqual(
            [book.get_isbn() for book in library.search_books_by_title("petit")],
            ["ISBN1"],
        )
        self.assertEqual(
            [book.get_isbn() for book in library.search_books_by_author("victor")],
            ["ISBN2"],
        )
        self.assertIn("Le Petit Prince", library.describe_book(
            library.find_book_by_isbn("ISBN1")
        ))

    def test_synchronize_loans(self):
        library = biblio.Library()
        library.add_book(biblio.Book("Titre", "Auteur", "ISBN1"))
        library.add_user(biblio.User("Marie", "U1"))

        book = library.find_book_by_isbn("ISBN1")
        book.set_availability(False)
        book.set_borrower_id("UTILISATEUR_INCONNU")
        library.synchronize_loans()

        self.assertTrue(book.get_availability())
        self.assertEqual(book.get_borrower_id(), "")


class FileManagerTests(unittest.TestCase):
    def make_manager(self, tmp: Path):
        return biblio.FileManager(
            str(tmp / "books.txt"), str(tmp / "users.txt")
        )

    def test_persistence_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manager = self.make_manager(tmp)
            library = biblio.Library()
            library.add_book(biblio.Book("Titre", "Auteur", "ISBN1"))
            library.add_user(biblio.User("Marie", "U1"))

            ok, message = manager.save_library_data(library)
            self.assertTrue(ok, message)
            self.assertTrue((tmp / "books.txt").exists())
            self.assertTrue((tmp / "users.txt").exists())
            self.assertFalse((tmp / "books.txt.tmp").exists())

            self.assertTrue(manager.create_backup()[0])
            self.assertTrue((tmp / "books.txt.backup").exists())
            self.assertTrue((tmp / "users.txt.backup").exists())

            restored = biblio.Library()
            ok, message = manager.load_library_data(restored)
            self.assertTrue(ok, message)
            self.assertEqual(restored.get_total_books(), 1)
            self.assertEqual(restored.get_total_users(), 1)

    def test_export_import_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manager = self.make_manager(tmp)
            library = biblio.Library()
            library.add_book(biblio.Book("Titre", "Auteur", "ISBN1"))
            library.add_user(biblio.User("Marie", "U1"))

            with working_directory(tmp):
                ok, message = manager.export_to_csv(library)
            self.assertTrue(ok, message)

            export_dir = tmp / "export"
            self.assertTrue((export_dir / "books.csv").exists())
            self.assertTrue((export_dir / "users.csv").exists())
            self.assertTrue(
                (export_dir / "books.csv").read_bytes().startswith(b"\xef\xbb\xbf")
            )

            imported = biblio.Library()
            ok, message = manager.import_from_csv(imported, str(export_dir))
            self.assertTrue(ok, message)
            self.assertEqual(imported.get_total_books(), 1)
            self.assertEqual(imported.get_total_users(), 1)
            self.assertIsNotNone(imported.find_book_by_isbn("ISBN1"))
            self.assertIsNotNone(imported.find_user_by_id("U1"))

            ok, message = manager.import_from_csv(imported, str(export_dir))
            self.assertTrue(ok, message)
            self.assertEqual(imported.get_total_books(), 1)
            self.assertEqual(imported.get_total_users(), 1)

    def test_invalid_data_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "books.txt").write_text(
                "||||\n"
                "Titre sans ISBN|Auteur\n"
                "Titre valide|Auteur|ISBN9|1|\n",
                encoding="utf-8",
            )
            (tmp / "users.txt").write_text(
                "|\n"
                "Nom sans ID\n"
                "Nom valide|U9|\n",
                encoding="utf-8",
            )

            manager = self.make_manager(tmp)
            library = biblio.Library()
            manager.load_library_data(library)

            self.assertEqual(library.get_total_books(), 1)
            self.assertIsNotNone(library.find_book_by_isbn("ISBN9"))
            self.assertEqual(library.get_total_users(), 1)
            self.assertIsNotNone(library.find_user_by_id("U9"))

    def test_invalid_csv_rows_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            csv_dir = tmp / "csv"
            csv_dir.mkdir()
            (csv_dir / "books.csv").write_text(
                "Titre,Auteur,ISBN,Disponible,Emprunteur\n"
                ",,,\n"
                "Titre|pipe,Auteur,ISBNX,Oui,\n"
                "Titre valide,Auteur,ISBN1,Oui,\n",
                encoding="utf-8",
            )
            (csv_dir / "users.csv").write_text(
                "Nom,ID,Nombre de livres,ISBNs empruntés\n"
                ",,\n"
                "Nom valide,U1,0,\n",
                encoding="utf-8",
            )

            manager = self.make_manager(tmp)
            imported = biblio.Library()
            ok, message = manager.import_from_csv(imported, str(csv_dir))
            self.assertTrue(ok, message)
            self.assertEqual(imported.get_total_books(), 1)
            self.assertEqual(imported.get_total_users(), 1)

    def test_save_failure_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manager = biblio.FileManager(
                str(tmp / "absent" / "books.txt"),
                str(tmp / "absent" / "users.txt"),
            )
            library = biblio.Library()
            library.add_book(biblio.Book("Titre", "Auteur", "ISBN1"))
            ok, message = manager.save_library_data(library)
            self.assertFalse(ok)
            self.assertIn("Erreur", message)


class ActivityLoggerTests(unittest.TestCase):
    def test_log_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                logger = biblio.ActivityLogger()
                logger.log("TEST", "details")
                entries = logger.get_last_entries(5)
                self.assertTrue(entries)
                self.assertIn("[TEST]", entries[-1])
                self.assertTrue(Path(logger.get_log_path()).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
