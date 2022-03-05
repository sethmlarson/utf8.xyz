import nox


@nox.session
def build(session):
    session.install("pip-tools", "black", "urllib3")
    session.run("black", "app.py", "build-db.py")
    session.run(
        "pip-compile", "-U", "--no-header", "requirements.in", "-o", "requirements.txt"
    )
    session.run("python", "build-db.py")
    session.run("docker", "build", ".", "--tag=sethmlarson/utf8-xyz")


@nox.session
def run(session):
    build(session)
    session.run("docker", "run", "--rm", "-it", "-p", "8080:8080", "sethmlarson/utf8-xyz")
