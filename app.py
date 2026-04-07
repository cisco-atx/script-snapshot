import os
import sys
from flask import Flask
from .routes import run, input

class ScriptAbstractContext:
    """
    Minimal context implementation used when running the script
    outside of the Netaudit Runner (e.g. standalone mode).

    This mirrors the Runner's ScriptContext interface.
    """

    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "output")

    def log(self, message):
        sys.stdout.write(f"{message}\n")

    def error(self, message):
        sys.stderr.write(f"{message}\n")

    def save_file(self, filename, content):
        path = os.path.join(os.getcwd(), filename)
        with open(path, "wb") as f:
            f.write(content)

    def set_progress(self, percent):
        pass

    def finish(self):
        pass

def create_app():
    app = Flask(__name__)
    app.script_ctx = ScriptAbstractContext()
    app.add_url_rule('/input', 'input', input)
    app.add_url_rule('/run', 'run', run, methods=['POST'])
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)




