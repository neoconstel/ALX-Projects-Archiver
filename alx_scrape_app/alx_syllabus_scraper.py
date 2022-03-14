import requests
import requests.cookies
from bs4 import BeautifulSoup
import os
import json
import time
import re
from datetime import datetime as dt


def cookies_to_cookiesjar(full_browser_cookie):
    '''takes the complete string of browser cookies and returns a valid cookiejar 
    object which can be used to authenticate a requests session object'''

    def split_cookies(full_browser_cookie):
        '''returns a list of tuples, each tuple containing the (name, value) of 
        each cookie'''
        cookie_list = [(pair.split("=")[0], pair.split("=")[1])
                    for pair in full_browser_cookie.split("; ")]
        return cookie_list

    cookie_pairs = split_cookies(full_browser_cookie)
    cookies_jar = requests.cookies.RequestsCookieJar()

    for cookie_pair in cookie_pairs:
        cookie_name = cookie_pair[0]
        cookie_value = cookie_pair[1]

        cookies_jar.set(cookie_name, cookie_value)

    return cookies_jar


def domain_from_url(url):
    if url.count('/') == 2:
        return url
    else:
        return url[:8 + url[8:].index('/')]


def re_symbolize_link(link):
    return link.replace(' ', '_').replace('/', '-').replace('#','--')


url = "https://alx-intranet.hbtn.io/projects/current"
browser_cookies = os.environ.get("ALX_COOKIES")
cookies_jar = cookies_to_cookiesjar(browser_cookies)
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
            "contents": [],
            "cookies_hash": hash(applied_cookies)
            }

    # if cookies are different from the previously used cookies, clear the
    # contents data -- as they could have conflicting timestamps and end up
    # sorting the appearance of the projects wrongly. Then replace stored
    # cookie hash
    if hash(applied_cookies) != scrape_data["cookies_hash"]:
        scrape_data["contents"] = []
        scrape_data["cookies_hash"] = hash(applied_cookies)


    # ----------------------------------------------------

    web_session = requests.Session()
    response = web_session.get(url, cookies=cookies_jar)
    concepts_response = web_session.get("https://alx-intranet.hbtn.io/concepts", cookies=cookies_jar)
    if response.status_code != 200 or concepts_response.status_code != 200:
        print("couldn't get response")
        exit()
    

    # --------cookie diagnosis--------
    # for cookie in response.cookies:
    #     print(f"cookie domain: {cookie.domain}")
    #     print(f"cookie name: {cookie.name}")
    #     print(f"cookie value: {cookie.value}")
    #     print("*" * 70)

    # print(f"Number of cookies: {len(response.cookies)}")
    # # print(f"\n\ncookies: {response.cookies}")
    # print('-' * 70)
    # --------end cookie diagnosis------

    # '''
    all_projects_soup = BeautifulSoup(response.text, 'lxml')
    all_concepts_soup = BeautifulSoup(concepts_response.text, 'lxml')
    concept_sections = [sect for sect in all_concepts_soup.select(".list-group-item")]
    

    project_sections = [sect for sect in all_projects_soup.select(".panel.panel-default")]
    # new integration: merge concepts list into projects list and handle them together
    all_sections = concept_sections + project_sections

    static_dir = f"{scrape_output_directory}/static_files"

    for section in all_sections:
        section_title = section.select_one("a").text.strip().replace('\n', '').replace('/', '-')
        if section in project_sections:
            section_dir = f"{scrape_output_directory}/projects/{section_title}"
        elif section in concept_sections:
            section_dir = f"{scrape_output_directory}/concepts/{section_title}"

        if not os.path.exists(section_dir):
            os.makedirs(section_dir)

        print(f"\n\n-------{section_title}-------")
        for link in section.select("li a"):
            link_text = re_symbolize_link(link.text)
            project_url = link.get("href")
            if not project_url.startswith("http"):
                project_url = f"{domain}{project_url}"


            project_page_path = f"{section_dir}/{link_text}.html"
            project_soup = BeautifulSoup(web_session.get(project_url).text, 'lxml')
            # Get project starting date and project title -- this would be used in sorting the order of the projects and creating a contents file
            date_regex = re.compile("\d\d-\d\d-\d\d\d\d")

            starting_date_match = None
            try:
                starting_date_match = re.search(date_regex, project_soup.select(".list-group-item")[2].text)
            except:
                pass
            
            if starting_date_match:
                starting_date = starting_date_match.group()
                # convert to epoch
                starting_date = dt.strptime(starting_date, "%m-%d-%Y").timestamp()

                project_title = project_soup.select_one("h1").text

                offline_contents_url = f'<a href="projects/{section_title}/{link_text}.html">{project_title}</a>'
                scrape_data["contents"].append([starting_date, offline_contents_url])

                # update storage
                with open(data_file, 'w') as save_file:
                    json.dump(scrape_data, save_file)

            if not project_url in scrape_data["scraped_urls"]:
                # proceed with scraping of project_url                
                with open(project_page_path, 'w') as project_page:

                    # replace css online links with offline css files

                    if include_css:
                        css_dir = f"{static_dir}/css"
                        if not os.path.exists(css_dir):
                            os.makedirs(css_dir)

                        for css_link in project_soup.select("link"):
                            # first ensure the css href is an absolute URL or convert it
                            href = css_link.get("href")
                            if href:
                                if not href.startswith("http"):
                                    css_link["href"] = f"{domain}{css_link.get('href')}"
                                    href = css_link.get("href")

                                                      
                                css_filename = re_symbolize_link(href)
                                css_path = f"{css_dir}/{css_filename}"

                                if not href in scrape_data["scraped_urls"]:
                                    # fetch the css online content, create a filename with the URL and write css content
                                    css = web_session.get(href).text 
                                    with open(css_path, "w") as css_file:
                                        css_file.write(css)
                                    scrape_data["scraped_urls"].append(href)

                                    # update data file
                                    with open(data_file, 'w') as save_file:
                                        json.dump(scrape_data, save_file)

                                    # print(f"CSS path: {css_path}")
                                    print(f" > CSS: {css_filename}")

                                # edit link href in the html page
                                css_path_in_html = f"../../static_files/{os.path.basename(os.path.dirname(css_path))}/{css_filename}"
                                css_link["href"] = css_path_in_html

                                
                        
                    #---------------------

                    # replace script online src with offline js files

                    if include_js:
                        scripts_dir = f"{static_dir}/scripts"
                        if not os.path.exists(scripts_dir):
                            os.makedirs(scripts_dir)

                        for script in project_soup.select("script"):
                            # first ensure the script src is an absolute URL or convert it
                            src = script.get("src")
                            if src:
                                if not src.startswith("http"):
                                    script["src"] = f"{domain}{src}"
                                    src = script.get("src")

                                                       
                                js_filename = re_symbolize_link(src)
                                js_path = f"{scripts_dir}/{js_filename}"
                                if not src in scrape_data["scraped_urls"]:
                                    # fetch the script online content, create a filename with the URL and write js content
                                    js = web_session.get(src).text 
                                    with open(js_path, "w") as js_file:
                                        js_file.write(js)
                                    scrape_data["scraped_urls"].append(src)

                                    # update data file
                                    with open(data_file, 'w') as save_file:
                                        json.dump(scrape_data, save_file)

                                    print(f" > JS: {js_filename}")

                                # edit script src in the html page
                                js_path_in_html = f"../../static_files/{os.path.basename(os.path.dirname(js_path))}/{js_filename}"
                                script["src"] = js_path_in_html


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
                    

                        if project_link.get("href") and project_link.get("href").startswith("/rltoken"):
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

                        # do same for concepts URLs -- but replace with offline concepts path
                        elif project_link.get("href") and re.search(re.compile("/concepts/(\d+)"), project_link.get("href")):

                            concept_num = re.search(re.compile("/concepts/(\d+)"), project_link.get("href")).group(1)
                            
                            print(f"\nFetching Concept {concept_num}\n")
                          
                            concept_sect = list(   filter(lambda sect: sect.select_one("a").get("href").endswith(f"/concepts/{concept_num}"), concept_sections)   )[0]
                            concept_link_text = concept_sect.select_one("a").text.strip().replace('\n', '')
                            real_project_resource_url = f"../../concepts/{concept_link_text.replace('/', '-')}/{re_symbolize_link(concept_link_text)}.html"

                            project_link["href"] = real_project_resource_url
                            

                    project_page.write(project_soup.prettify())

                    # add to storage
                    scrape_data["scraped_urls"].append(project_url)
                    with open(data_file, 'w') as save_file:
                        json.dump(scrape_data, save_file)

                    # delay a bit to avoid over-stressing the website with requests
                    time.sleep(scrape_interval)

            print(f"\n\n{link}")
    # '''

    with open(data_file) as save_file:
        try:
            scrape_data = json.load(save_file)
        except:
            pass

    # CONTENTS file creation (for chronological order of projects and offline location)
    contents_path = f"{scrape_output_directory}/contents.html"
    with open(contents_path, "w") as contents_file:
        #form of contents data: [ [epoch,epoch_url], [epoch,epoch_url], [epoch,epoch_url] ]
        chronological_pairs = sorted(scrape_data["contents"], key=lambda x:x[0])

        contents_file.write(f"<br>\n")
        contents_file.write("<h1>Chronological order of Projects</h1>")
        contents_file.write(f"<br>\n")
        contents_file.write("<h3>(Projects of the same day are grouped together by the dashed lines)</h3>")

        previous_epoch = ""
        for epoch, epoch_url in chronological_pairs:
            if previous_epoch and epoch != previous_epoch:
                contents_file.write(f"<br>\n")
                contents_file.write("-" * 72)
            previous_epoch = epoch

            contents_file.write(f"<br>\n")
            contents_file.write(epoch_url)       

    print("\n\nScraping Completed")
    

if __name__ == "__main__":
    scrape_alx_syllabus()