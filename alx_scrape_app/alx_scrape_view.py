from . import zipper
from .alx_syllabus_scraper import *

from flask import Blueprint, render_template, request, redirect, url_for

import redis
from rq import Queue, Retry

# redis_cache = redis.Redis()  # for development while offline
redis_cache = redis.from_url(os.environ.get("REDIS_URL"))  # for deployment
queue = Queue(connection=redis_cache, default_timeout=3600)

alx_scrape_view = Blueprint("alx_scrape_view", __name__, template_folder="templates", static_folder="static")


def get_alx_syllabus(custom_cookie, scrape_output_directory="alx_syllabus"):

    try:
    
        zip_output_file = f"{os.path.abspath(scrape_output_directory)}.zip"

        if not custom_cookie:
            scrape_alx_syllabus(scrape_output_directory=scrape_output_directory)
        else:
            scrape_alx_syllabus(scrape_output_directory=scrape_output_directory, applied_cookies=custom_cookie)

        # delete any previous zipped output file
        if os.path.exists(zip_output_file):
            os.remove(zip_output_file)

        zipper.zip_contents(scrape_output_directory, zip_output_file)

        zip_path = f"{scrape_output_directory}.zip"

        redis_cache.set("status", 1)
        with open(zip_path, 'r+b') as file:
            redis_cache.set("alx_zip", file.read())

        redis_cache.set("zip_path", zip_path)

    except:
        redis_cache.set("status", -1) # error occured

    
@alx_scrape_view.route("/alx_syllabus_archiver", methods=["GET", "POST"])
def archive_page():
    if request.method == "POST":
        redis_cache.set("status", 0)  # it is only 0 when scraping/zipping is going on. Initially None, and 1 when done.
        redis_cache.delete("alx_zip")
        redis_cache.delete("zip_path")

        # first empty queue
        queue.empty()

        custom_cookie = request.form.get("custom-cookie").strip()
        
        scrape_job = queue.enqueue(get_alx_syllabus, custom_cookie=custom_cookie, retry=Retry(max=3, interval=[10, 30, 60]))
        return redirect(f"{url_for('alx_scrape_view.archive_page')}")

    elif request.method == "GET":
        status = redis_cache.get("status")
        if status:
            status = status.decode()
            if status == "-1":  # error in previous attempt
                # clear the error message for a fresh start
                redis_cache.delete("status")
                queue.empty()


        zip_path = redis_cache.get("zip_path")
        if zip_path:
            zip_path = zip_path.decode()

        return render_template("alx_syllabus.html", status=status, zip_path=zip_path)

    