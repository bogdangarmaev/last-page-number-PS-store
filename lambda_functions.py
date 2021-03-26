from time import sleep
import requests
from requests_html import HTMLSession


url = 'https://store.playstation.com/ru-ru/category/44d8bb20-653e-431e-8ad0-c0a365f68d2f/'

def get_text_with_requests_html(url):
    session = HTMLSession()
    r = session.get(url)
    r.html.render()
    sleep(1)
    return r.text


with open('not_found_page_requests_html.html', 'w') as file:
    file.write(get_text_with_requests_html(url + '10000/'))

with open('valid_page2.html_requests_html', 'w') as file:
    file.write(get_text_with_requests_html(url))

with open('invalid_page2_requests_html.html', 'w') as file:
    file.write(get_text_with_requests_html(url + '160/'))


def get_text_with_requests(url):
    response = requests.get(url)
    sleep(1)
    return response.text

with open('valid_page.html', 'w') as file:
    file.write(get_text_with_requests(url))

with open('invalid_page.html', 'w') as file:
    file.write(get_text_with_requests(url + '160/'))

with open('not_found_page.html', 'w') as file:
    file.write(get_text_with_requests(url + '10000/'))
