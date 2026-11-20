"""Smoke test des bindings bibliotheque_py (sans GUI)."""

import sys
import tempfile
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD_DIR))

import bibliotheque_py as biblio  # noqa: E402


def test_library():
    library = biblio.Library()
    assert library.get_total_books() == 0

    assert library.add_book(biblio.Book("Titre", "Auteur", "ISBN1"))
    assert not library.add_book(biblio.Book("Doublon", "X", "ISBN1"))

    book = library.find_book_by_isbn("ISBN1")
    assert book is not None and book.get_title() == "Titre"
    assert library.find_book_by_isbn("INCONNU") is None

    assert library.add_user(biblio.User("Marie", "U1"))
    assert not library.add_user(biblio.User("Autre", "U1"))
    assert library.find_user_by_id("U2") is None

    assert library.check_out_book("ISBN1", "U1")
    assert not library.check_out_book("ISBN1", "U1")
    assert library.find_book_by_isbn("ISBN1").get_availability() is False
    assert library.find_user_by_id("U1").has_borrowed_book("ISBN1")
    assert library.get_checked_out_book_count() == 1

    assert library.search_books_by_title("tit")[0].get_isbn() == "ISBN1"
    assert library.search_books_by_author("aut")[0].get_isbn() == "ISBN1"
    assert len(library.get_available_books()) == 0

    assert library.return_book("ISBN1")
    assert library.find_user_by_id("U1").has_borrowed_book("ISBN1") is False
    assert library.get_available_book_count() == 1


def test_persistence_and_import():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        manager = biblio.FileManager(
            str(tmp / "books.txt"), str(tmp / "users.txt")
        )

        library = biblio.Library()
        library.add_book(biblio.Book("Titre", "Auteur", "ISBN1"))
        library.add_user(biblio.User("Marie", "U1"))

        ok, message = manager.save_library_data(library)
        assert ok, message

        restored = biblio.Library()
        ok, message = manager.load_library_data(restored)
        assert ok, message
        assert restored.get_total_books() == 1
        assert restored.get_total_users() == 1

        assert manager.create_backup()[0]

        import_dir = tmp / "import"
        import_dir.mkdir()
        (import_dir / "books.csv").write_text(
            "Titre,Auteur,ISBN,Disponible,Emprunteur\n"
            "Nouveau,Auteur,ISBN2,Oui,\n",
            encoding="utf-8",
        )
        (import_dir / "users.csv").write_text(
            "Nom,ID,Nombre de livres,ISBNs empruntés\n"
            "Jean,U2,0,\n",
            encoding="utf-8",
        )
        imported = biblio.Library()
        ok, message = manager.import_from_csv(imported, str(import_dir))
        assert ok, message
        assert imported.get_total_books() == 1
        assert imported.find_book_by_isbn("ISBN2") is not None
        assert imported.find_user_by_id("U2") is not None


def test_logger_path():
    assert biblio.ActivityLogger().get_log_path().endswith("logs/activity.log")


if __name__ == "__main__":
    test_library()
    test_persistence_and_import()
    test_logger_path()
    print("OK: bindings bibliotheque_py")
