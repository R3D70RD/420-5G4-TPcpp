"""Smoke test de la couche service (sans GUI)."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gui"))

from service import LibraryError, LibraryService  # noqa: E402


def test_service_flow():
    with tempfile.TemporaryDirectory() as tmp:
        service = LibraryService(tmp)

        service.add_book("Titre", "Auteur", "ISBN1")
        service.add_user("Marie", "U1")
        assert service.statistics() == {
            "total_books": 1,
            "available_books": 1,
            "checked_out_books": 0,
            "total_users": 1,
        }

        try:
            service.add_book("Doublon", "X", "ISBN1")
            raise AssertionError("doublon ISBN accepté")
        except LibraryError:
            pass

        try:
            service.add_book("", "Auteur", "ISBN2")
            raise AssertionError("champ vide accepté")
        except LibraryError:
            pass

        try:
            service.add_book("Bad|Title", "Auteur", "ISBN2")
            raise AssertionError("caractère interdit accepté")
        except LibraryError:
            pass

        service.check_out("ISBN1", "U1")
        assert service.statistics()["checked_out_books"] == 1
        assert len(service.checked_out_books()) == 1

        try:
            service.remove_book("ISBN1")
            raise AssertionError("suppression d'un livre emprunté acceptée")
        except LibraryError:
            pass

        service.return_book("ISBN1")
        assert service.statistics()["checked_out_books"] == 0

        assert service.save()[0]
        assert (Path(tmp) / "books.txt").exists()
        assert (Path(tmp) / "users.txt").exists()

        reloaded = LibraryService(tmp)
        assert reloaded.statistics()["total_books"] == 1
        assert reloaded.statistics()["total_users"] == 1

        reloaded.remove_book("ISBN1")
        assert reloaded.statistics()["total_books"] == 0


if __name__ == "__main__":
    test_service_flow()
    print("OK: service bibliotheque")
