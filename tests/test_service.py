"""Tests de la couche service (sans GUI)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gui"))

from service import LibraryError, LibraryService  # noqa: E402


class LibraryServiceTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.tmp = Path(self._temporary.name)
        self.service = LibraryService(self.tmp)

    def tearDown(self):
        self._temporary.cleanup()

    def test_add_and_duplicates(self):
        self.service.add_book("Titre", "Auteur", "ISBN1")
        self.service.add_user("Marie", "U1")

        self.assertEqual(self.service.statistics(), {
            "total_books": 1,
            "available_books": 1,
            "checked_out_books": 0,
            "total_users": 1,
        })

        with self.assertRaises(LibraryError):
            self.service.add_book("Doublon", "X", "ISBN1")
        with self.assertRaises(LibraryError):
            self.service.add_user("Autre", "U1")

    def test_validation_errors(self):
        with self.assertRaises(LibraryError):
            self.service.add_book("", "Auteur", "ISBN1")
        with self.assertRaises(LibraryError):
            self.service.add_book("Titre", "Auteur", "ISBN|1")
        with self.assertRaises(LibraryError):
            self.service.add_user("Nom", "U,1")
        with self.assertRaises(LibraryError):
            self.service.check_out("", "U1")

    def test_loan_flow_and_remove_rules(self):
        self.service.add_book("Titre", "Auteur", "ISBN1")
        self.service.add_user("Marie", "U1")

        self.service.check_out("ISBN1", "U1")
        self.assertEqual(self.service.statistics()["checked_out_books"], 1)
        self.assertEqual(len(self.service.checked_out_books()), 1)

        with self.assertRaises(LibraryError):
            self.service.check_out("ISBN1", "U1")
        with self.assertRaises(LibraryError):
            self.service.remove_book("ISBN1")
        with self.assertRaises(LibraryError):
            self.service.return_book("ISBN_INCONNU")

        self.service.return_book("ISBN1")
        self.assertEqual(self.service.statistics()["checked_out_books"], 0)
        self.service.remove_book("ISBN1")
        self.assertEqual(self.service.statistics()["total_books"], 0)

    def test_unknown_book_or_user(self):
        with self.assertRaises(LibraryError):
            self.service.check_out("ISBN_INCONNU", "U1")
        with self.assertRaises(LibraryError):
            self.service.remove_book("ISBN_INCONNU")

        self.service.add_book("Titre", "Auteur", "ISBN1")
        with self.assertRaises(LibraryError):
            self.service.check_out("ISBN1", "U_INCONNU")

    def test_persistence_reload_and_shutdown(self):
        self.service.add_book("Titre", "Auteur", "ISBN1")
        self.service.add_user("Marie", "U1")
        self.assertTrue(self.service.save()[0])

        self.service.add_book("Autre", "Auteur", "ISBN2")
        self.service.reload()
        self.assertEqual(self.service.statistics()["total_books"], 1)

        ok, message = self.service.shutdown()
        self.assertTrue(ok, message)

        reopened = LibraryService(self.tmp)
        self.assertEqual(reopened.statistics()["total_books"], 1)
        self.assertEqual(reopened.statistics()["total_users"], 1)

    def test_csv_import(self):
        csv_dir = self.tmp / "csv"
        csv_dir.mkdir()
        (csv_dir / "books.csv").write_text(
            "Titre,Auteur,ISBN,Disponible,Emprunteur\n"
            "Nouveau,Auteur,ISBN2,Oui,\n",
            encoding="utf-8",
        )
        (csv_dir / "users.csv").write_text(
            "Nom,ID,Nombre de livres,ISBNs empruntés\n"
            "Jean,U2,0,\n",
            encoding="utf-8",
        )

        ok, message = self.service.import_csv(str(csv_dir))
        self.assertTrue(ok, message)
        self.assertEqual(self.service.statistics()["total_books"], 1)
        self.assertEqual(self.service.statistics()["total_users"], 1)

    def test_missing_data_directory(self):
        with self.assertRaises(LibraryError):
            LibraryService(self.tmp / "absent")


if __name__ == "__main__":
    unittest.main(verbosity=2)
