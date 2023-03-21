import re
import sqlite3
import csv
import os
import io
import urllib3

currency = []
arrows = []


def normalize(x):
    return re.sub("[^a-zA-Z0-9]+", " ", x).lower()


try:
    os.remove("utf8.db")
except Exception:
    pass

http = urllib3.PoolManager()
db = sqlite3.connect("utf8.db")
db.execute(
    """
CREATE TABLE chars (
    name STRING PRIMARY KEY,
    ordinal INTEGER UNIQUE,
    category STRING DEFAULT ''
);
"""
)

unicodedata = http.request(
    "GET",
    f"https://www.unicode.org/Public/draft/UCD/ucd/UnicodeData.txt",
    preload_content=False,
)
unicodedata.auto_close = False
reader = csv.reader(io.TextIOWrapper(unicodedata, encoding="utf-8"), delimiter=";")
for row in reader:
    ordinal = int(row[0], 16)
    name = row[1].lower().replace(" ", "-")
    if "<" in name:  # Skip control characters
        continue
    category = None
    group = row[2]

    if group == "Sc":
        category = "currency"
    if "arrow" in name:
        category = "arrows"
    db.execute(
        """
        INSERT INTO chars (
            name, ordinal, category
        ) VALUES (
            ?, ?, ?
        )
    """,
        (name, ordinal, category),
    )

db.commit()
db.close()
