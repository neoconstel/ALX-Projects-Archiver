import requests
import requests.cookies
from bs4 import BeautifulSoup
import os
import json
import time


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


def scrape_alx_syllabus(scrape_output_directory="alx_syllabus", applied_cookies=browser_cookies):

    if not os.path.exists(data_file):
        open(data_file, 'w').close()

    with open(data_file) as save_file:
        try:
            scrape_data = json.load(save_file)
        except:
            scrape_data = {
            "scraped_urls": []
            }

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
                with open(f"{section_dir}/{link_text}.html", 'w') as project_page:
                    project_soup = BeautifulSoup(web_session.get(project_url).text, 'lxml')

                    # replace css online links with offline css files

                    css_dir = f"{section_dir}/css"
                    if not os.path.exists(css_dir):
                        os.makedirs(css_dir)

                    for css_link in project_soup.select("link"):
                        # first ensure the css href is an absolute URL or convert it
                        if not css_link.get("href").startswith("http"):
                            css_link["href"] = f"{domain}{css_link.get('href')}"

                        # fetch the css online content, create a filename with the URL and write css content
                        css = web_session.get(css_link.get("href")).text                        
                        css_filename = css_link.get("href").replace(' ', '_').replace('/', '-')
                        css_path = f"{css_dir}/{css_filename}"
                        with open(css_path, "w") as css_file:
                            css_file.write(css)

                        # edit link href in the html page
                        css_rel_path = f"{os.path.basename(os.path.dirname(css_path))}/{css_filename}"
                        css_link["href"] = css_rel_path

                        print(f" > CSS: {css_filename}")
                        
                    #---------------------

                    # replace token URLs with the true resource URLs
                    for project_link in project_soup.select("a"):
                        # if not project_link.get("href").startswith("http"):  # this line works same as the line below                      
                        if project_link.get("href").startswith("/rltoken"):   # but this is more specific, thus faster
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

    print("\n\nScraping Completed")
    

if __name__ == "__main__":
    scrape_alx_syllabus()