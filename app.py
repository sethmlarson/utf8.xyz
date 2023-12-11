import re
import sqlite3
from flask import (
    Flask,
    Request,
    Response,
    render_template,
    g,
    request,
    abort,
    redirect,
    url_for,
)

app = Flask(__name__)
categories = ["arrows", "currency"]
aliases = {
    "zwj": ("zero-width-joiner", "Zero-width joiner"),
    "zwnbs": ("zero-width-no-break-space", "Zero-width non-breaking space"),
    "nbs": ("zero-width-no-break-space", "Zero width non-breaking space"),
    "zwnj": ("zero-width-non-joiner", "Zero-width non-joiner"),
    "zws": ("zero-width-space", "Zero-width space"),
    "nd": ("en-dash", "–"),
    "md": ("em-dash", "—"),
}


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("utf8.db")
    return db


def normalize(x):
    return re.sub("[^a-zA-Z0-9]+", "-", x).lower()


def title(x):
    return re.sub("[^a-zA-Z0-9]+", " ", x).title()


def ord_to_hex(x):
    x = hex(x)[2:].upper()
    if len(x) <= 4:
        return x.zfill(4)
    return x.zfill(8)


def encode_to_hex_bytes(char, encoding):
    return "".join(f"\\x{hex(x)[2:]}" for x in char.encode(encoding))


def is_cli_tool(request: Request) -> bool:
    """Is the User Agent from a CLI tool?"""
    cli_user_agents = ["curl", "HTTPie"]
    return any(x in request.user_agent.string for x in cli_user_agents)


@app.after_request
def cache_control_header(response: Response):
    response.headers["vary"] = "user-agent"
    response.headers["cache-control"] = "public,max-age=300,immutable"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect(url_for("category_or_char", char=request.form.get("char")))
    return render_template("index.html", aliases=aliases)


@app.errorhandler(Exception)
def on_error(e):
    status_code = getattr(e, "code", 500)
    if is_cli_tool(request):
        return f"HTTP {status_code} - That's an error :(\n", status_code
    return render_template("error.html", status_code=status_code), status_code


def render_list_of_chars(title, db, sql, params):
    db.execute(sql, params)
    chars = db.fetchall()
    if not chars:
        return abort(404)

    chars = [
        (name, chr(ordinal)) for name, ordinal in sorted(chars, key=lambda x: x[0])
    ]

    if is_cli_tool(request):
        lines = [title, "=" * len(title)]
        lines.extend([f" - {text} ({name})" for name, text in chars])
        lines.append("")
        return "\n".join(lines)

    return render_template("category.html", category=title, chars=chars)


@app.route("/<string:char>")
def category_or_char(char):
    # Resolve aliases
    if char in aliases:
        return redirect(url_for("category_or_char", char=aliases[char][0]), code=307)

    db = get_db().cursor()

    if char in categories:
        return render_list_of_chars(
            char.title(),
            db,
            "SELECT name, ordinal FROM chars WHERE category = ?;",
            (char,),
        )

    # Redirect single characters to their names
    if len(char) == 1:
        db.execute("SELECT name, ordinal FROM chars WHERE ordinal = ?;", (ord(char),))
        try:
            name, char_ord = db.fetchone()
        except Exception:
            pass
        else:
            return redirect(url_for("category_or_char", char=name))

    db.execute("SELECT name, ordinal FROM chars WHERE name = ?;", (char,))
    try:
        name, char_ord = db.fetchone()
    except Exception:
        return render_list_of_chars(
            "%r" % char,
            db,
            "SELECT name, ordinal FROM chars WHERE name LIKE ? LIMIT 100;",
            (f"%{normalize(char)}%",),
        )

    if is_cli_tool(request):
        return chr(char_ord)

    code_point_hex = ord_to_hex(char_ord)
    char_chr = chr(char_ord)

    def backslashed(x):
        return x.replace("\\", "\\\\").replace('"', '\\"')

    return render_template(
        "char.html",
        char_text=char_chr,
        char_html=f"&#{char_ord};",
        char_python=f"\\{'U' if len(code_point_hex) > 4 else 'u'}{code_point_hex}",
        char_python2=f"\\N{{{name.replace('-', ' ')}}}",
        char_long_name=title(name),
        char_code_point=f"U+{code_point_hex}",
        char_utf8=encode_to_hex_bytes(char_chr, "utf-8"),
        char_utf16=encode_to_hex_bytes(char_chr, "utf-16"),
        backslashed=backslashed,
    )
