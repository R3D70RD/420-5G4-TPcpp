"""Smoke test de l'interface customtkinter (nécessite un affichage ou xvfb-run)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "gui"))
sys.path.insert(0, str(PROJECT_ROOT / "build"))

GUI_IMPORT_ERROR = None
try:
    import tkinter  # noqa: F401
    import customtkinter  # noqa: F401
    import app as gui_app
except Exception as exc:  # pragma: no cover - dépend de l'environnement
    gui_app = None
    GUI_IMPORT_ERROR = exc


@unittest.skipIf(gui_app is None, f"GUI indisponible : {GUI_IMPORT_ERROR}")
class GuiSmokeTests(unittest.TestCase):
    def test_full_flow(self):
        if not os.environ.get("DISPLAY"):
            self.skipTest("aucun affichage disponible (DISPLAY absent)")

        with tempfile.TemporaryDirectory() as tmp:
            root = gui_app.BibliothequeApp()
            original_askyesno = gui_app.messagebox.askyesno
            gui_app.messagebox.askyesno = lambda *args, **kwargs: True
            try:
                root.after(300, root.quit)
                root.mainloop()

                root.data_dir_var.set(tmp)
                root._load_data_dir()
                self.assertIsNotNone(root.service)

                root.title_entry.insert(0, "Livre GUI")
                root.author_entry.insert(0, "Auteur GUI")
                root.isbn_entry.insert(0, "GUI-ISBN")
                root._add_book()
                self.assertEqual(root.service.statistics()["total_books"], 1)

                root.user_name_entry.insert(0, "Utilisateur GUI")
                root.user_id_entry.insert(0, "GUI-USER")
                root._add_user()
                self.assertEqual(root.service.statistics()["total_users"], 1)

                root.loan_isbn_entry.insert(0, "GUI-ISBN")
                root.loan_user_entry.insert(0, "GUI-USER")
                root._check_out()
                self.assertEqual(root.service.statistics()["checked_out_books"], 1)

                root.return_isbn_entry.insert(0, "GUI-ISBN")
                root._return_book()
                self.assertEqual(root.service.statistics()["checked_out_books"], 0)

                root.search_entry.insert(0, "Livre GUI")
                root._search_title()
                self.assertIn("Livre GUI", root.books_text.get("1.0", "end"))

                root._save()
                self.assertTrue((Path(tmp) / "books.txt").exists())
                self.assertTrue((Path(tmp) / "users.txt").exists())

                root.delete_isbn_entry.insert(0, "GUI-ISBN")
                root._delete_book()
                self.assertEqual(root.service.statistics()["total_books"], 0)
            finally:
                gui_app.messagebox.askyesno = original_askyesno
                root.destroy()


if __name__ == "__main__":
    unittest.main(verbosity=2)
