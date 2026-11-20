"""Interface graphique customtkinter pour la bibliotheque personnelle."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError as exc:
    raise SystemExit(
        "customtkinter est requis : pip install customtkinter\n"
        f"Détail : {exc}"
    ) from exc

try:
    from service import EXPORT_DIR, PROJECT_ROOT, LibraryError, LibraryService
except ImportError as exc:
    raise SystemExit(
        "Impossible d'importer le module 'bibliotheque_py'. "
        "Compilez le projet avec pybind11 (cmake --build build).\n"
        f"Détail : {exc}"
    ) from exc


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class BibliothequeApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Système de Gestion de Bibliothèque Personnelle")
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.service: LibraryService | None = None
        self.data_dir_var = tk.StringVar(value=str(PROJECT_ROOT / "data"))
        self.import_dir_var = tk.StringVar(value=str(EXPORT_DIR))
        self.stat_vars = {
            "total_books": tk.StringVar(value="—"),
            "available_books": tk.StringVar(value="—"),
            "checked_out_books": tk.StringVar(value="—"),
            "total_users": tk.StringVar(value="—"),
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_tabs()
        self._build_status()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(150, self._load_data_dir)

    # --- Construction de l'interface -------------------------------------

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Dossier de données :").grid(
            row=0, column=0, padx=(12, 8), pady=12
        )
        self.data_dir_entry = ctk.CTkEntry(header, textvariable=self.data_dir_var)
        self.data_dir_entry.grid(row=0, column=1, sticky="ew", pady=12)
        ctk.CTkButton(
            header, text="Parcourir", width=110, command=self._browse_data_dir
        ).grid(row=0, column=2, padx=(8, 4), pady=12)
        ctk.CTkButton(
            header, text="Charger", width=90, command=self._load_data_dir
        ).grid(row=0, column=3, padx=(4, 12), pady=12)

    def _build_tabs(self) -> None:
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))

        self._build_books_tab(self.tabs.add("Livres"))
        self._build_users_tab(self.tabs.add("Utilisateurs"))
        self._build_loans_tab(self.tabs.add("Emprunts"))
        self._build_stats_tab(self.tabs.add("Statistiques"))
        self._build_data_tab(self.tabs.add("Données"))

    def _build_books_tab(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=0, minsize=400)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(tab)
        controls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            controls, text="Ajouter un livre", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))
        self.title_entry = ctk.CTkEntry(controls, placeholder_text="Titre")
        self.title_entry.pack(fill="x", padx=12, pady=4)
        self.author_entry = ctk.CTkEntry(controls, placeholder_text="Auteur")
        self.author_entry.pack(fill="x", padx=12, pady=4)
        self.isbn_entry = ctk.CTkEntry(controls, placeholder_text="ISBN")
        self.isbn_entry.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(controls, text="Ajouter le livre", command=self._add_book).pack(
            fill="x", padx=12, pady=(6, 12)
        )

        ctk.CTkLabel(
            controls, text="Rechercher", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(4, 6))
        self.search_entry = ctk.CTkEntry(controls, placeholder_text="Titre ou auteur")
        self.search_entry.pack(fill="x", padx=12, pady=4)

        search_buttons = ctk.CTkFrame(controls, fg_color="transparent")
        search_buttons.pack(fill="x", padx=12, pady=4)
        search_buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            search_buttons, text="Par titre", command=self._search_title
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        ctk.CTkButton(
            search_buttons, text="Par auteur", command=self._search_author
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)
        ctk.CTkButton(
            search_buttons, text="Tous les livres", command=self._refresh_books
        ).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=2)
        ctk.CTkButton(
            search_buttons, text="Disponibles", command=self._show_available
        ).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=2)

        ctk.CTkLabel(
            controls, text="Supprimer", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))
        self.delete_isbn_entry = ctk.CTkEntry(controls, placeholder_text="ISBN")
        self.delete_isbn_entry.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(
            controls,
            text="Supprimer le livre",
            fg_color="#b23b3b",
            hover_color="#8f2f2f",
            command=self._delete_book,
        ).pack(fill="x", padx=12, pady=(6, 12))

        list_frame = ctk.CTkFrame(tab)
        list_frame.grid(row=0, column=1, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_frame, text="Livres").grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )
        self.books_text = ctk.CTkTextbox(list_frame, wrap="word")
        self.books_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self._set_text(self.books_text, "Chargez un dossier de données pour commencer.")

    def _build_users_tab(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=0, minsize=400)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(tab)
        controls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(
            controls,
            text="Ajouter un utilisateur",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(12, 6))
        self.user_name_entry = ctk.CTkEntry(controls, placeholder_text="Nom")
        self.user_name_entry.pack(fill="x", padx=12, pady=4)
        self.user_id_entry = ctk.CTkEntry(controls, placeholder_text="ID utilisateur")
        self.user_id_entry.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(
            controls, text="Ajouter l'utilisateur", command=self._add_user
        ).pack(fill="x", padx=12, pady=(6, 12))
        ctk.CTkButton(
            controls, text="Rafraîchir la liste", command=self._refresh_users
        ).pack(fill="x", padx=12, pady=(0, 12))

        list_frame = ctk.CTkFrame(tab)
        list_frame.grid(row=0, column=1, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_frame, text="Utilisateurs").grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )
        self.users_text = ctk.CTkTextbox(list_frame, wrap="word")
        self.users_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self._set_text(self.users_text, "Chargez un dossier de données pour commencer.")

    def _build_loans_tab(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=0, minsize=400)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(tab)
        controls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            controls, text="Emprunter un livre", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))
        self.loan_isbn_entry = ctk.CTkEntry(controls, placeholder_text="ISBN")
        self.loan_isbn_entry.pack(fill="x", padx=12, pady=4)
        self.loan_user_entry = ctk.CTkEntry(controls, placeholder_text="ID utilisateur")
        self.loan_user_entry.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(controls, text="Emprunter", command=self._check_out).pack(
            fill="x", padx=12, pady=(6, 12)
        )

        ctk.CTkLabel(
            controls, text="Retourner un livre", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(4, 6))
        self.return_isbn_entry = ctk.CTkEntry(controls, placeholder_text="ISBN")
        self.return_isbn_entry.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(controls, text="Retourner", command=self._return_book).pack(
            fill="x", padx=12, pady=(6, 12)
        )
        ctk.CTkButton(
            controls, text="Rafraîchir les emprunts", command=self._refresh_loans
        ).pack(fill="x", padx=12, pady=(0, 12))

        list_frame = ctk.CTkFrame(tab)
        list_frame.grid(row=0, column=1, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_frame, text="Emprunts en cours").grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )
        self.loans_text = ctk.CTkTextbox(list_frame, wrap="word")
        self.loans_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self._set_text(self.loans_text, "Chargez un dossier de données pour commencer.")

    def _build_stats_tab(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=1)
        frame = ctk.CTkFrame(tab)
        frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        frame.grid_columnconfigure(1, weight=1)

        rows = [
            ("Total des livres", "total_books"),
            ("Livres disponibles", "available_books"),
            ("Livres empruntés", "checked_out_books"),
            ("Total des utilisateurs", "total_users"),
        ]
        for row, (label, key) in enumerate(rows):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=14)).grid(
                row=row, column=0, sticky="w", padx=16, pady=10
            )
            ctk.CTkLabel(
                frame,
                textvariable=self.stat_vars[key],
                font=ctk.CTkFont(size=20, weight="bold"),
            ).grid(row=row, column=1, sticky="e", padx=16, pady=10)

        ctk.CTkButton(frame, text="Rafraîchir", command=self._refresh_stats).grid(
            row=len(rows), column=0, columnspan=2, pady=(16, 8)
        )

    def _build_data_tab(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=0, minsize=400)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        actions = ctk.CTkFrame(tab)
        actions.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            actions, text="Fichiers", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))
        ctk.CTkButton(actions, text="Sauvegarder les données", command=self._save).pack(
            fill="x", padx=12, pady=4
        )
        ctk.CTkButton(actions, text="Créer une sauvegarde", command=self._backup).pack(
            fill="x", padx=12, pady=4
        )
        ctk.CTkButton(actions, text="Exporter en CSV", command=self._export_csv).pack(
            fill="x", padx=12, pady=4
        )
        ctk.CTkButton(
            actions, text="Recharger depuis le disque", command=self._reload_data
        ).pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            actions, text="Importer depuis un CSV", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))
        import_row = ctk.CTkFrame(actions, fg_color="transparent")
        import_row.pack(fill="x", padx=12, pady=4)
        import_row.grid_columnconfigure(0, weight=1)
        self.import_dir_entry = ctk.CTkEntry(
            import_row, textvariable=self.import_dir_var
        )
        self.import_dir_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            import_row, text="...", width=42, command=self._browse_import_dir
        ).grid(row=0, column=1, padx=(6, 0))
        ctk.CTkButton(actions, text="Importer", command=self._import_csv).pack(
            fill="x", padx=12, pady=(4, 12)
        )

        journal_frame = ctk.CTkFrame(tab)
        journal_frame.grid(row=0, column=1, sticky="nsew")
        journal_frame.grid_columnconfigure(0, weight=1)
        journal_frame.grid_rowconfigure(1, weight=1)
        journal_header = ctk.CTkFrame(journal_frame, fg_color="transparent")
        journal_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        journal_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            journal_header, text="Journal d'activités (20 dernières entrées)"
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            journal_header, text="Rafraîchir", width=100, command=self._refresh_log
        ).grid(row=0, column=1, sticky="e")
        self.log_text = ctk.CTkTextbox(journal_frame, wrap="word")
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self._set_text(self.log_text, "Chargez un dossier de données pour commencer.")

    def _build_status(self) -> None:
        self.status_label = ctk.CTkLabel(self, text="Prêt.", anchor="w")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))

    # --- Utilitaires ------------------------------------------------------

    def _status(self, message: str, error: bool = False) -> None:
        self.status_label.configure(
            text=message.strip() or "Prêt.",
            text_color="#c0392b" if error else "#2e7d32",
        )

    def _unexpected(self, exc: Exception) -> None:
        messagebox.showerror("Erreur inattendue", str(exc))

    @staticmethod
    def _set_text(textbox, text: str) -> None:
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

    def _require_service(self) -> LibraryService | None:
        if self.service is None:
            self._status(
                "Aucune donnée chargée. Choisissez un dossier puis cliquez sur Charger.",
                error=True,
            )
            return None
        return self.service

    def _show_result(self, ok: bool, message: str, success: str) -> None:
        text = (message or "").strip()
        if ok:
            self._status(success)
            if text:
                messagebox.showinfo("Information", text)
        else:
            self._status(text or "L'opération a échoué.", error=True)
            if text:
                messagebox.showerror("Erreur", text)

    # --- Données ----------------------------------------------------------

    def _browse_data_dir(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.data_dir_var.get())
        if directory:
            self.data_dir_var.set(directory)

    def _load_data_dir(self) -> None:
        path = Path(self.data_dir_var.get().strip()).expanduser()
        if not path.is_dir():
            self._status(f"Le répertoire {path} n'existe pas.", error=True)
            messagebox.showerror("Dossier invalide", f"Le répertoire {path} n'existe pas.")
            return

        try:
            self.service = LibraryService(path)
        except LibraryError as exc:
            self._status(str(exc), error=True)
            messagebox.showerror("Chargement impossible", str(exc))
            return
        except Exception as exc:
            self._unexpected(exc)
            return

        self._refresh_all()
        self._status(self.service.last_load_message or "Données chargées.")

    def _reload_data(self) -> None:
        service = self._require_service()
        if service is None:
            return
        if not messagebox.askyesno(
            "Recharger",
            "Recharger les données depuis le disque ? "
            "Les modifications non sauvegardées seront perdues.",
        ):
            return

        try:
            self.service = LibraryService(service.data_dir)
        except Exception as exc:
            self._unexpected(exc)
            return

        self._refresh_all()
        self._status("Données rechargées depuis le disque.")

    def _save(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            ok, message = service.save()
        except Exception as exc:
            self._unexpected(exc)
            return
        self._show_result(ok, message, "Données sauvegardées avec succès.")

    def _backup(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            ok, message = service.create_backup()
        except Exception as exc:
            self._unexpected(exc)
            return
        self._show_result(ok, message, "Sauvegarde de secours créée.")

    def _export_csv(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            ok, message = service.export_csv()
        except Exception as exc:
            self._unexpected(exc)
            return
        self._show_result(ok, message, "Export CSV terminé.")

    def _browse_import_dir(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.import_dir_var.get())
        if directory:
            self.import_dir_var.set(directory)

    def _import_csv(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            ok, message = service.import_csv(self.import_dir_var.get().strip())
        except Exception as exc:
            self._unexpected(exc)
            return
        self._refresh_all()
        self._show_result(ok, message, "Import CSV terminé.")

    # --- Livres -----------------------------------------------------------

    def _add_book(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            service.add_book(
                self.title_entry.get(),
                self.author_entry.get(),
                self.isbn_entry.get(),
            )
        except LibraryError as exc:
            self._status(str(exc), error=True)
            return
        except Exception as exc:
            self._unexpected(exc)
            return

        for entry in (self.title_entry, self.author_entry, self.isbn_entry):
            entry.delete(0, "end")
        self._refresh_books()
        self._refresh_stats()
        self._status("Livre ajouté avec succès.")

    def _delete_book(self) -> None:
        service = self._require_service()
        if service is None:
            return
        isbn = self.delete_isbn_entry.get().strip()
        if not isbn:
            self._status("Entrez l'ISBN du livre à supprimer.", error=True)
            return
        if not messagebox.askyesno(
            "Confirmation", f"Supprimer le livre avec l'ISBN {isbn} ?"
        ):
            return
        try:
            service.remove_book(isbn)
        except LibraryError as exc:
            self._status(str(exc), error=True)
            return
        except Exception as exc:
            self._unexpected(exc)
            return

        self.delete_isbn_entry.delete(0, "end")
        self._refresh_books()
        self._refresh_stats()
        self._status("Livre supprimé avec succès.")

    def _search_title(self) -> None:
        service = self._require_service()
        if service is None:
            return
        term = self.search_entry.get().strip()
        books = service.search_books_by_title(term)
        self._render_books(books, f"Recherche par titre : « {term} »")

    def _search_author(self) -> None:
        service = self._require_service()
        if service is None:
            return
        term = self.search_entry.get().strip()
        books = service.search_books_by_author(term)
        self._render_books(books, f"Recherche par auteur : « {term} »")

    def _show_available(self) -> None:
        service = self._require_service()
        if service is None:
            return
        self._render_books(service.available_books(), "Livres disponibles")

    def _refresh_books(self) -> None:
        if self.service is None:
            return
        self._render_books(self.service.all_books(), "Tous les livres")

    def _render_books(self, books: list, title: str) -> None:
        if self.service is None:
            return
        if not books:
            self._set_text(self.books_text, f"{title}\n\nAucun livre.")
            return
        parts = [f"=== {title} ({len(books)}) ===", ""]
        for index, book in enumerate(books, start=1):
            parts.append(f"{index}. {self.service.describe_book(book)}")
            parts.append("-" * 50)
        self._set_text(self.books_text, "\n".join(parts))

    # --- Utilisateurs / emprunts -----------------------------------------

    def _add_user(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            service.add_user(self.user_name_entry.get(), self.user_id_entry.get())
        except LibraryError as exc:
            self._status(str(exc), error=True)
            return
        except Exception as exc:
            self._unexpected(exc)
            return

        self.user_name_entry.delete(0, "end")
        self.user_id_entry.delete(0, "end")
        self._refresh_users()
        self._refresh_stats()
        self._status("Utilisateur ajouté avec succès.")

    def _refresh_users(self) -> None:
        if self.service is None:
            return
        users = self.service.all_users()
        if not users:
            self._set_text(self.users_text, "Aucun utilisateur enregistré.")
            return
        parts = [f"=== Utilisateurs ({len(users)}) ===", ""]
        for index, user in enumerate(users, start=1):
            parts.append(f"{index}. {user.to_string()}")
            parts.append("-" * 50)
        self._set_text(self.users_text, "\n".join(parts))

    def _check_out(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            service.check_out(self.loan_isbn_entry.get(), self.loan_user_entry.get())
        except LibraryError as exc:
            self._status(str(exc), error=True)
            return
        except Exception as exc:
            self._unexpected(exc)
            return

        self.loan_isbn_entry.delete(0, "end")
        self.loan_user_entry.delete(0, "end")
        self._refresh_all()
        self._status("Livre emprunté avec succès.")

    def _return_book(self) -> None:
        service = self._require_service()
        if service is None:
            return
        try:
            service.return_book(self.return_isbn_entry.get())
        except LibraryError as exc:
            self._status(str(exc), error=True)
            return
        except Exception as exc:
            self._unexpected(exc)
            return

        self.return_isbn_entry.delete(0, "end")
        self._refresh_all()
        self._status("Livre retourné avec succès.")

    def _refresh_loans(self) -> None:
        if self.service is None:
            return
        books = self.service.checked_out_books()
        if not books:
            self._set_text(self.loans_text, "Aucun emprunt en cours.")
            return
        parts = [f"=== Emprunts en cours ({len(books)}) ===", ""]
        for index, book in enumerate(books, start=1):
            parts.append(f"{index}. {self.service.describe_book(book)}")
            parts.append("-" * 50)
        self._set_text(self.loans_text, "\n".join(parts))

    # --- Statistiques / journal ------------------------------------------

    def _refresh_stats(self) -> None:
        if self.service is None:
            return
        stats = self.service.statistics()
        for key, value in stats.items():
            self.stat_vars[key].set(str(value))

    def _refresh_log(self) -> None:
        if self.service is None:
            return
        entries = self.service.activity(20)
        self._set_text(
            self.log_text,
            "\n".join(entries) if entries else "Le journal est vide.",
        )

    def _refresh_all(self) -> None:
        if self.service is None:
            return
        self._refresh_books()
        self._refresh_users()
        self._refresh_loans()
        self._refresh_stats()
        self._refresh_log()

    # --- Fermeture --------------------------------------------------------

    def _on_close(self) -> None:
        if self.service is not None:
            try:
                ok, message = self.service.shutdown()
            except Exception:
                ok, message = False, ""
            if not ok:
                messagebox.showwarning(
                    "Sauvegarde",
                    message.strip() or "La sauvegarde à la fermeture a échoué.",
                )
        self.destroy()


def main() -> None:
    app = BibliothequeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
