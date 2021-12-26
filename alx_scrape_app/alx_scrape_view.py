from . import zipper
from .alx_syllabus_scraper import *

from flask import Blueprint, render_template, request, redirect, url_for

import redis
from rq import Queue

r = redis.Redis()
q = Queue(connection=r, default_timeout=3600)

alx_scrape_view = Blueprint("alx_scrape_view", __name__, template_folder="templates", static_folder="static")


def get_alx_syllabus(scrape_output_directory="alx_syllabus"):
    
    zip_output_file = f"{os.path.abspath(scrape_output_directory)}.zip"

    scrape_alx_syllabus(scrape_output_directory=scrape_output_directory)

    # delete any previous zipped output file
    if os.path.exists(zip_output_file):
        os.remove(zip_output_file)

    zipper.zip_contents(scrape_output_directory, zip_output_file)

    zip_path = f"{scrape_output_directory}.zip"

    r.set("status", 1)
    with open(zip_path, 'r+b') as file:
        r.set("alx_zip", file.read())

    r.set("zip_path", zip_path)

    
@alx_scrape_view.route("/alx_syllabus_archiver", methods=["GET", "POST"])
def archive_page():
    if request.method == "POST":
        r.set("status", 0)  # it is only 0 when scraping/zipping is going on. Initially None, and 1 when done.
        r.delete("alx_zip")
        r.delete("zip_path")

        scrape_job = q.enqueue(get_alx_syllabus)
        return redirect(f"{url_for('alx_scrape_view.archive_page')}")

    elif request.method == "GET":
        status = r.get("status")
        if status:
            status = status.decode()

        zip_path = r.get("zip_path")
        if zip_path:
            zip_path = zip_path.decode()

        return render_template("alx_syllabus.html", status=status, zip_path=zip_path)

    