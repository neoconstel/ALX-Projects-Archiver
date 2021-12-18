import zipper
from alx_syllabus_scraper import *

if __name__ == '__main__':
    scrape_output_directory = "alx_syllabus"
    zip_output_file = f"{os.path.abspath(scrape_output_directory)}.zip"

    scrape_alx_syllabus(scrape_output_directory=scrape_output_directory)

    # delete any previous zipped output file TODO: only if SHA256 sum differs
    if os.path.exists(zip_output_file):
        os.remove(zip_output_file)

    zipper.zip_contents(scrape_output_directory, zip_output_file)