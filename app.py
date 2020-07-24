import re
import sqlite3
from flask import Flask, Response, render_template, g, request, abort

app = Flask(__name__)
categories = ["arrows", "currency"]


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("utf8.db")
    return db


def normalize(x):
    return re.sub("[^a-zA-Z0-9]+", " ", x).lower()


def ord_to_hex(x):
    x = hex(x)[2:].upper()
    if len(x) <= 4:
        return x.zfill(4)
    return x.zfill(8)


@app.after_request
def cache_control_header(response: Response):
    response.headers["vary"] = "user-agent"
    response.headers["cache-control"] = "public,max-age=300,immutable"
    return response


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.errorhandler(Exception)
def on_error(e):
    status_code = getattr(e, "status", 500)
    if "curl" in request.headers.get("user-agent", ""):
        return f"HTTP {status_code} - That's an error :(\n"
    return render_template("error.html", status_code=status_code)


def render_list_of_chars(title, db, sql, params):
    db.execute(sql, params)
    chars = db.fetchall()
    if not chars:
        return abort(404)

    chars = [
        (name, chr(ordinal)) for name, ordinal in sorted(chars, key=lambda x: x[0])
    ]

    if "curl" in request.headers.get("user-agent", ""):
        lines = [title, "=" * len(title)]
        lines.extend([f" - {text} ({name})" for name, text in chars])
        lines.append("")
        return "\n".join(lines)

    return render_template("category.html", category=title, chars=chars)


@app.route("/<string:char>")
def category_or_char(char):
    db = get_db().cursor()

    if char in categories:
        return render_list_of_chars(
            char.title(),
            db,
            "SELECT name, ordinal FROM chars WHERE category = ?;",
            (char,),
        )

    db.execute("SELECT long_name, ordinal FROM chars WHERE name = ?;", (char,))
    try:
        long_name, char_ord = db.fetchone()
    except Exception:
        return render_list_of_chars(
            "%r" % char,
            db,
            "SELECT name, ordinal FROM chars WHERE long_name LIKE ? LIMIT 100;",
            (f"%{normalize(char)}%",),
        )

    # Short-circuit for curl
    if "curl" in request.headers.get("user-agent", ""):
        return chr(char_ord)

    return render_template(
        "char.html",
        char_text=chr(char_ord),
        char_long_name=long_name.title(),
        char_ordinal=ord_to_hex(char_ord),
    )
