from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
NOTE_FILE = BASE_DIR / "pymentor_file_lab" / "note.txt"
RELATIVE_FILE = Path("pymentor_file_lab") / "note.txt"

print("cwd:", Path.cwd())
print("Относительный путь:", RELATIVE_FILE.resolve())
print("От модуля:", NOTE_FILE.resolve())

with NOTE_FILE.open("r", encoding="utf-8") as file:
    print("Содержимое:", repr(file.read()))