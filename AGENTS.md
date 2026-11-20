# AGENTS.md

C++17 library manager (`bibliotheque`) with a console app and a customtkinter GUI exposed through pybind11. UI, log messages, and code comments are in French; keep that convention when editing user-facing text.

## Build & run

```bash
# Python deps (once): python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cmake -S . -B build -Dpybind11_DIR="$(python3 -m pybind11 --cmakedir)"
cmake --build build

./build/bibliotheque -d data # console; REQUIRED to load/save data
python gui/app.py            # GUI; defaults to data/ and imports build/bibliotheque_py*.so
```

- No linter/CI. Verify changes by building (`-Wall -Wextra -Wpedantic`) and running the headless smoke scripts: `python tests/test_bindings.py` and `python tests/test_service.py`. GUI needs a display (`xvfb-run -a python gui/app.py` headless).
- pybind11 is optional at configure time: if absent, CMake warns and only builds the console target. `python3-tk` is required for customtkinter.
- Running the console without `-d/--data-dir` starts empty and never persists data (in-memory only).
- Every C++ implementation must be listed explicitly in `SOURCES` in `CMakeLists.txt` (no glob); `bindings.cpp` is listed separately in `pybind11_add_module`.

## Data & path quirks

- Sample data lives in `data/books.txt` and `data/users.txt`. Formats:
  - book: `title|author|isbn|1-or-0|borrowerId`
  - user: `name|userId|isbn1,isbn2,...`
- Fields may not contain `|` or `,`; the UI rejects them. Preserve UTF-8 (accented names/titles are in the sample data).
- `getProjectRoot()` (`filemanager.cpp:11`) walks up one level when cwd is `build/` or contains `CMakeCache.txt`. So `export/` (CSV) and `logs/activity.log` always resolve to the repo root regardless of running from repo root or `build/`.
- CSV export writes `export/books.csv` / `export/users.csv` (UTF-8 BOM); import ignores the header and skips duplicate/invalid rows.
- `build/`, `logs/`, `export/` are gitignored — don't commit generated output.

## Architecture

- `main.cpp` — CLI arg parsing and interactive menu loop; saves on exit/EOF.
- `library.{h,cpp}` — owns books/users via `unique_ptr`, enforces unique ISBN/user ID, reconciles loans (`synchronizeLoans`, books take precedence).
- `book`, `user` — POJOs with `toFileFormat`/`fromFileFormat` serialization.
- `filemanager` — load/save, backups, CSV export/import.
- `activitylogger` — appends to `logs/activity.log`.
- `bindings.cpp` — snake_case pybind11 module `bibliotheque_py`. Methods that print return `(bool, message)` by capturing `std::cout`; methods returning `Book*`/`User*` use `reference_internal`, so the owning `Library` must stay alive.
- `gui/service.py` — Python wrapper: validation (no `|`/`,`), precise French errors, chdir to repo root, session load/save. `gui/app.py` — customtkinter tabs (livres, utilisateurs, emprunts, stats, données).
