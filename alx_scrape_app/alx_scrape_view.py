from . import zipper
from .alx_syllabus_scraper import *

from flask import Blueprint, render_template, request, redirect, url_for

alx_scrape_view = Blueprint("alx_scrape_view", __name__, static_folder="static", template_folder="templates")

zip_path = None


@alx_scrape_view.route("/alx_syllabus_archiver", methods=["GET", "POST"])
def get_alx_syllabus():
    global zip_path
    if request.method == "POST":
        scrape_output_directory = "alx_syllabus"
        zip_output_file = f"{os.path.abspath(scrape_output_directory)}.zip"

        scrape_alx_syllabus(scrape_output_directory=scrape_output_directory)

        # delete any previous zipped output file TODO: only if SHA256 sum differs
        if os.path.exists(zip_output_file):
            os.remove(zip_output_file)

        zipper.zip_contents(scrape_output_directory, zip_output_file)

        # return render_template("alx_syllabus.html", zip_path=f"{scrape_output_directory}.zip")
        zip_path = f"{scrape_output_directory}.zip"
        return redirect(f"{url_for('alx_scrape_view.get_alx_syllabus')}")
    
    elif request.method == "GET":
        # return render_template("alx_syllabus.html", zip_path=None)
        return render_template("alx_syllabus.html", zip_path=zip_path)
    