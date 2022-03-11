import requests
import requests.cookies
from bs4 import BeautifulSoup
import os
import json
import time
import re
from datetime import datetime as dt


def split_cookies(full_browser_cookie):
    '''returns a list of tuples, each tuple containing the (name, value) of 
    each cookie'''
    cookie_list = [(pair.split("=")[0], pair.split("=")[1])
                   for pair in full_browser_cookie.split("; ")]
    return cookie_list


def domain_from_url(url):
    if url.count('/') == 2:
        return url
    else:
        return url[:8 + url[8:].index('/')]


url = "https://alx-intranet.hbtn.io/projects/current"
browser_cookies = os.environ.get("ALX_COOKIES")
cookies_jar = requests.cookies.RequestsCookieJar()
domain = domain_from_url(url)

scrape_interval = 2  # Interval (in seconds) between requests sent.
data_file = "scrape_data.dat"



def scrape_alx_syllabus(scrape_output_directory="alx_syllabus", applied_cookies=browser_cookies, include_css=True, include_js=False):

    if not os.path.exists(data_file):
        open(data_file, 'w').close()

    with open(data_file) as save_file:
        try:
            scrape_data = json.load(save_file)
        except:
            scrape_data = {
            "scraped_urls": [],
            "contents": {


                },
            "cookies_hash": hash(applied_cookies)
            }

    # if cookies are different from the previously used cookies, clear the
    # contents data -- as they could have conflicting timestamps and end up
    # sorting the appearance of the projects wrongly
    if hash(applied_cookies) != scrape_data["cookies_hash"]:
        scrape_data["contents"] = {}

    
    for cookie_pair in split_cookies(applied_cookies):
        cookie_name = cookie_pair[0]
        cookie_value = cookie_pair[1]

        cookies_jar.set(cookie_name, cookie_value)

    # ----------------------------------------------------

    web_session = requests.Session()
    response = web_session.get(url, cookies=cookies_jar)
    if response.status_code != 200:
        print("couldn't get response")
        exit()

    # --------cookie diagnosis--------
    for cookie in response.cookies:
        print(f"cookie domain: {cookie.domain}")
        print(f"cookie name: {cookie.name}")
        print(f"cookie value: {cookie.value}")
        print("*" * 70)

    print(f"Number of cookies: {len(response.cookies)}")
    print(f"\n\ncookies: {response.cookies}")
    print('-' * 70)
    # --------end cookie diagnosis------

    soup = BeautifulSoup(response.text, 'lxml')
    project_sections = soup.select(".panel.panel-default")
    for section in project_sections:
        section_title = section.select_one("a").text.strip().replace('\n', '')
        section_dir = f"{scrape_output_directory}/{section_title}"
        if not os.path.exists(section_dir):
            os.makedirs(section_dir)

        print(f"\n\n-------{section_title}-------")
        for link in section.select("li a"):
            link_text = link.text.replace(' ', '_').replace('/', '-')
            project_url = link.get("href")
            if not project_url.startswith("http"):
                project_url = f"{domain}{project_url}"

            if not project_url in scrape_data["scraped_urls"]:
                # proceed with scraping of project_url
                project_page_path = f"{section_dir}/{link_text}.html"
                with open(project_page_path, 'w') as project_page:
                    project_soup = BeautifulSoup(web_session.get(project_url).text, 'lxml')


                    # Get project starting date and project title -- this would be used in sorting the order of the projects and creating a contents file
                    date_regex = re.compile("\d\d-\d\d-\d\d\d\d")
                    starting_date_match = re.search(date_regex, project_soup.select(".list-group-item")[2].text)
                    if starting_date_match:
                        starting_date = starting_date_match.group()
                        # convert to epoch
                        starting_date = dt.strptime(starting_date, "%m-%d-%Y").timestamp()

                        project_title = project_soup.select_one("h1").text

                        offline_contents_url = f'<a href="{section_title}/{link_text}.html">{project_title}</a>'
                        scrape_data["contents"][starting_date] = offline_contents_url


                    # replace css online links with offline css files

                    if include_css:
                        css_dir = f"{section_dir}/css"
                        if not os.path.exists(css_dir):
                            os.makedirs(css_dir)

                        for css_link in project_soup.select("link"):
                            # first ensure the css href is an absolute URL or convert it
                            href = css_link.get("href")
                            if href:
                                if not href.startswith("http"):
                                    css_link["href"] = f"{domain}{css_link.get('href')}"
                                    href = css_link.get("href")

                                # fetch the css online content, create a filename with the URL and write css content
                                css = web_session.get(href).text                        
                                css_filename = href.replace(' ', '_').replace('/', '-')
                                css_path = f"{css_dir}/{css_filename}"
                                with open(css_path, "w") as css_file:
                                    css_file.write(css)

                                # edit link href in the html page
                                css_rel_path = f"{os.path.basename(os.path.dirname(css_path))}/{css_filename}"
                                css_link["href"] = css_rel_path

                                print(f" > CSS: {css_filename}")
                        
                    #---------------------

                    # replace script online src with offline js files

                    if include_js:
                        scripts_dir = f"{section_dir}/scripts"
                        if not os.path.exists(scripts_dir):
                            os.makedirs(scripts_dir)

                        for script in project_soup.select("script"):
                            # first ensure the script src is an absolute URL or convert it
                            src = script.get("src")
                            if src:
                                if not src.startswith("http"):
                                    script["src"] = f"{domain}{src}"
                                    src = script.get("src")

                                # fetch the script online content, create a filename with the URL and write js content
                                js = web_session.get(src).text                        
                                js_filename = src.replace(' ', '_').replace('/', '-')
                                js_path = f"{scripts_dir}/{js_filename}"
                                with open(js_path, "w") as js_file:
                                    js_file.write(js)

                                # edit script src in the html page
                                js_rel_path = f"{os.path.basename(os.path.dirname(js_path))}/{js_filename}"
                                script["src"] = js_rel_path

                                print(f" > JS: {js_filename}")

                    else: # don't include js, so erase all web srcs to avoid
                        # trying to connect to the internet while opening the 
                        # offline html
                        for script in project_soup.select("script"):
                            src = script.get("src")
                            if src:
                                script["src"] = ""

                    # --------------------------------

                    # replace token URLs with the true resource URLs
                    for project_link in project_soup.select("a"):
                        # if not project_link.get("href").startswith("http"):  # this line works same as the line below                      
                        if project_link.get("href") and project_link.get("href").startswith("/rltoken"):   # but this is more specific, thus faster
                            try:                     
                                real_project_resource_url = web_session.get(f"{domain}{project_link.get('href')}", timeout=20).url
                                project_link["href"] = real_project_resource_url
                            except:
                                # in case it can't fetch the resource link. I encountered this problem for
                                # twitter links, and that's because as a Nigerian my country's president has
                                # banned our network from accessing anything twitter.
                                # so in this case just take the absolute token url
                                project_link["href"] = f"{domain}{project_link.get('href')}"
                            else:
                                print(f"    > Resource URL: {project_link.get('href')}")

                    project_page.write(project_soup.prettify())

                    # add to storage
                    scrape_data["scraped_urls"].append(project_url)
                    with open(data_file, 'w') as save_file:
                        json.dump(scrape_data, save_file)

                    # delay a bit to avoid over-stressing the website with requests
                    time.sleep(scrape_interval)

            print(f"\n\n{link}")

    # CONTENTS file creation (for chronological order of projects and offline location)
    contents_path = f"{scrape_output_directory}/contents.html"
    with open(contents_path, "w") as contents_file:
        chronological_epoch = sorted(scrape_data["contents"].keys())

        contents_file.write(f"<br>\n")
        contents_file.write("<h1>Chronological order of Projects</h1>")
        contents_file.write(f"<br>\n")
        contents_file.write("<h3>(Projects in the same day are not ordered)</h3>")
        for epoch in chronological_epoch:
            contents_file.write(f"<br>\n")
            contents_file.write(scrape_data["contents"][epoch])       

    print("\n\nScraping Completed")
    

if __name__ == "__main__":
    scrape_alx_syllabus()