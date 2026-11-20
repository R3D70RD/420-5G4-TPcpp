# AGENTS.md

C++17 console app (`bibliotheque`) — a personal library manager. UI, log messages, and code comments are in French; keep that convention when editing user-facing text.

## Build & run

```bash
cmake -S . -B build
cmake --build build          # binary: build/bibliotheque
./build/bibliotheque -d data # REQUIRED to load/save data
```

- There is no test suite, linter, or CI. Verify changes by building (the build uses `-Wall -Wextra -Wpedantic`) and exercising the interactive menu with `-d data`.
- Running without `-d/--data-dir` starts empty and never persists data (only in-memory).
- Every `.cpp` must be listed explicitly in the `SOURCES` list in `CMakeLists.txt`; there is no glob.

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
