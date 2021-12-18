import zipper
from alx_syllabus_scraper import *

if __name__ == '__main__':
    scape_output_directory = "alx_syllabus"
    zip_output_file = f"{scape_output_directory}.zip"

    scrape_alx_syllabus(scrape_output_directory=scape_output_directory)
    zipper.zip_contents(scape_output_directory, zip_output_file)