from flask import Flask, render_template, send_file, redirect, url_for, jsonify
from alx_scrape_app.alx_scrape_view import alx_scrape_view
import os
from flask_cors import CORS
from alx_scrape_app.alx_scrape_view import r, q


app = Flask(__name__)
CORS(app)
app.register_blueprint(alx_scrape_view, url_prefix="")


@app.route("/")
def home():
    return redirect(f"{url_for('.alx_scrape_view.archive_page')}")
    # return render_template("alx_syllabus.html")


@app.route("/alx_syllabus_archiver/status")
def status():
    
    status = r.get("status")
    if status:
        status = status.decode("ascii")
        return jsonify(status=status)
    else:
        return None


@app.route("/download/<file>")
def download(file):
    with open(file, "w+b") as output_file:
        output_file.write(r.get("alx_zip"))

    return send_file(file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
