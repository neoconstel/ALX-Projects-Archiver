

import requests
import requests.cookies
from bs4 import BeautifulSoup
import os


def split_cookies(full_browser_cookie):
    '''returns a list of tuples, each tuple containing the (name, value) of each cookie'''
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

for cookie_pair in split_cookies(browser_cookies):
    cookie_name = cookie_pair[0]
    cookie_value = cookie_pair[1]

    cookies_jar.set(cookie_name, cookie_value)

# ----------------------------------------------------

web_session = requests.Session()
response = web_session.get(url, cookies=cookies_jar)
if response.status_code != 200:
    print("couldn't get response")
    exit()

for cookie in response.cookies:
    print(f"cookie domain: {cookie.domain}")
    print(f"cookie name: {cookie.name}")
    print(f"cookie value: {cookie.value}")
    print("*" * 70)

print(f"Number of cookies: {len(response.cookies)}")
print(f"\n\ncookies: {response.cookies}")


# soup = BeautifulSoup(response.text, 'lxml')
# for link in soup.find_all("a"):
#     if not link.get("href").startswith("http"):
#         print(f"Link before: {link.get('href')}")
#         link['href'] = f"{domain_from_url(url)}{link.get('href')}"
#         print(f"Link after: {link.get('href')}")

# with open("response.html", 'w') as file:
#     file.write(soup.prettify())


soup = BeautifulSoup(response.text, 'lxml')
project_sections = soup.select(".panel.panel-default")
for section in project_sections:
    section_title = section.select_one("a").text.strip().replace('\n', '')
    section_dir = f"alx_syllabus/{section_title}"
    if not os.path.exists(section_dir):
        os.makedirs(section_dir)

    print(f"\n\n-------{section_title}-------")
    for link in section.select("li a"):
        print(link)

