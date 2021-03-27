import asyncio
import aiohttp

url = 'https://store.playstation.com/ru-ru/category/44d8bb20-653e-431e-8ad0-c0a365f68d2f/'
initial_first_page = 1
search_range = 200  # search scope, if there are no last page it's try to find in next scope
len_of_page_with_content = 89000  # min count of symbols in html doc with dynamic content


class SearchScopeIsFullOfValidPagesException(Exception):
    """If there are no last page"""
    pass


async def get_page(url, session):
    async with session.get(url) as response:
        if response.status == 200:
            response_data = await response.read()
        else:
            response_data = ''
        return {
            'url': url,
            'page_len': len(response_data)
            }


async def get_pages(search_params):
    """Event loop"""
    tasks = []
    async with aiohttp.ClientSession() as session:
        for number_page in range(*search_params):
            task = asyncio.create_task(get_page(url+str(number_page), session))
            tasks.append(task)
        pages = await asyncio.gather(*tasks)
    return pages


def get_search_params(start_range, finish_range):
    """Generate search params"""
    range_width = finish_range - start_range
    step = range_width // 10
    step = step if step != 0 else 1
    return start_range, finish_range, step


def get_new_range(pages):
    """Return last page with content and first page without content"""
    start_range = initial_first_page
    finish_range = None
    for page in pages:
        if page['page_len'] == 0:
            continue
        if page['page_len'] > len_of_page_with_content:
            start_range = parse_page_number_from_url(page['url'])
        else:
            finish_range = parse_page_number_from_url(page['url'])
            break
    if finish_range is None:  # if there are no pages without dynamic content
        raise SearchScopeIsFullOfValidPagesException
    return start_range, finish_range


def parse_page_number_from_url(current_url):
    page_number = current_url.split('/')[-1]
    return int(page_number)


def out_of_scope_wrapper(func):
    """If func don't get valid result, it's change search scope"""
    def inner_func(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except SearchScopeIsFullOfValidPagesException:
                global initial_first_page
                initial_first_page += search_range
    return inner_func


@out_of_scope_wrapper
def main():
    """Main func return last page"""
    search_params = get_search_params(initial_first_page, search_range + initial_first_page)
    while True:
        pages = asyncio.run(get_pages(search_params))
        start_range, finish_range = get_new_range(pages)
        if finish_range - start_range == 1:  # if this ranges
            return start_range
        search_params = get_search_params(start_range, finish_range)


def lambda_handler(event, context):
    last_page = main()
    return{
        'last_page': last_page
    }
