from flask import Flask, render_template, send_file, redirect, url_for, jsonify
from alx_scrape_app.alx_scrape_view import alx_scrape_view
import os
import redis
from rq import Queue

app = Flask(__name__)
app.register_blueprint(alx_scrape_view, url_prefix="")

try:
    r = redis.from_url(os.environ.get("REDIS_URL"))
except:
    r = redis.Redis()
q = Queue(connection=r, default_timeout=180)


@app.route("/")
def home():
    return redirect(f"{url_for('.alx_scrape_view.get_alx_syllabus')}")
    # return render_template("alx_syllabus.html")


@app.route("/fetch_status")
def fetch_status():
    status = r.get("fetch_status")
    return jsonify(status=status)


@app.route("/download/<file>")
def download(file):
    return send_file(file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
