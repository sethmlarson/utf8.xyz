import nox


@nox.session
def build(session):
    session.install("pip-tools", "black", "urllib3")
    session.run("black", "app.py", "build-db.py")
    session.run(
        "pip-compile", "--no-header", "requirements.in", "-o", "requirements.txt"
    )
    session.run("python", "build-db.py")
    session.run("docker", "build", ".", "--tag=sethmlarson/utf8-xyz")
