from .kernel import Kernel
from .__init__ import __version__

from flask import Flask, request, url_for, render_template, jsonify
import pip
import webbrowser
import json
import os
import sys


app = Flask(__name__)
__dirname = os.path.dirname(os.path.abspath(__file__))
active_dir = "."
kernel = None

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method=="GET":
        packages = pip.get_installed_distributions()
        packages = sorted(packages, key=lambda k: k.key)
        files = [f for f in os.listdir(active_dir) if f.endswith(".py")]
        return render_template("index.html", packages=packages, files=files,
                version=__version__)
    else:
        code = request.form.get('code')
        if code:
            if code=="getvars":
                code = "__get_variables()"
            if request.form.get('complete'):
                result = kernel.complete(code)
            else:
                result = kernel.execute(code)

            return jsonify(result)
        else:
            return "BAD"

@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html", version=__version__)

@app.route("/plots", methods=["GET"])
def plots():
    plot_dir = os.path.join(__dirname, "static", "plots")
    plots = []
    for plot in os.listdir(plot_dir):
        if plot.endswith(".png"):
            plots.append(url_for("static", filename="plots/%s" % plot))
    return jsonify({ "plots": plots })

@app.route("/file/<filename>", methods=["GET"])
def get_file(filename):
    filename = os.path.join(active_dir, filename)
    return open(filename).read()

@app.route("/file", methods=["POST"])
def save_file():
    filename = os.path.join(active_dir, request.form['filename'])
    with open(filename, 'wb') as f:
        f.write(request.form['source'])
    return "OK"

@app.route("/rc", methods=["GET", "POST"])
def rc():
    home = os.path.expanduser("~")
    filename = os.path.join(home, ".rodeorc")
    # give it the good ole college try
    try:
        rc = json.load(open(filename, 'rb'))
    except:
        rc = {}

    if request.method=="GET":
        return jsonify({ "status": "OK", "rc": rc })
    else:
        for field, value in request.form.items():
            rc[field] = value
        with open(filename, "wb") as f:
            f.write(json.dumps(rc))
        return "OK"

def main(directory, port=5000, host=None, browser=True):
    global kernel
    global active_dir
    active_dir = os.path.realpath(directory)

    if not port:
        port = 5000

    # get rid of plots
    for f in os.listdir(os.path.join(__dirname, "static", "plots")):
        f = os.path.join(__dirname, "static", "plots", f)
        if f.endswith(".png"):
            os.remove(f)
    kernel = Kernel()
    art = open(os.path.join(__dirname, "rodeo-ascii.txt"), 'r').read()
    display = """
{ART}
''''''''''''''''''''''''''''''''''''''''''''''''''
  URL: http://localhost:{PORT}/
  DIRECTORY: {DIR}
''''''''''''''''''''''''''''''''''''''''''''''''''
""".format(ART=art, PORT=port, DIR=active_dir)
    sys.stderr.write(display)
    if browser:
        webbrowser.open("http://localhost:%d/" % port, new=2)
    app.run(debug=False, host=host, port=port)

if __name__=="__main__":
    if len(sys.argv)==1:
        directory = "."
    else:
        directory = sys.argv[1]
    main(directory)

