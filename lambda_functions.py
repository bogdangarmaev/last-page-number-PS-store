import asyncio
from time import time

import aiohttp


class SearchScopeIsFullOfValidPagesException(Exception):
    """Исключение на случай если в текущей поисковой области не найдена посл. страница"""
    pass


class PsStoreConnection:
    """Соединение с внешним ресурсом PS Store"""

    url = 'https://store.playstation.com/ru-ru/category/44d8bb20-653e-431e-8ad0-c0a365f68d2f/'

    def __init__(self, search_params):
        self.search_params: (int, int, int) = search_params

    @staticmethod
    async def _get_page_len_(page_url: str, session: aiohttp.ClientSession):
        """Получает информацию о странице"""
        async with session.get(page_url) as response:
            if response.status == 200:
                response_data = await response.read()
            else:
                response_data = ''  # если статус_код ответа не равен 200, значит что то пошло не так,
                # записываем пустую строку, в дальнейшем данная страница будет проигнорирована
            return {
                'url': page_url,
                'page_len': len(response_data)
            }

    async def _create_and_gather_tasks_(self):
        """Событийный цикл, управляет получением всех страниц"""
        tasks = []
        async with aiohttp.ClientSession() as session:
            for number_page in range(*self.search_params):
                task = asyncio.create_task(self._get_page_len_(self.url + str(number_page), session))
                tasks.append(task)
            pages = await asyncio.gather(*tasks)
        return pages

    def get_pages(self):
        """Запуск событийного цикла"""
        return asyncio.run(self._create_and_gather_tasks_())


class Utils:
    """Вспомогательные функции для парсинга и генерации параметров"""

    @staticmethod
    def get_search_params(start_range: int, finish_range: int) -> (int, int, int):
        """Сгенерировать шаг на основе старта и финиша"""
        range_width = finish_range - start_range
        step = range_width // 10
        step = step if step != 0 else 1  # шаг для функции range() не может быть равен 0
        return start_range, finish_range, step

    @classmethod
    def get_new_range(cls, pages: [{}, ...], start_range: int, len_of_page_with_content: int) -> (int, int):
        """По полученным страницам находит самую большую заполненную страницу и самую малую незаполненную"""
        finish_range = None
        for page in pages:
            if page['page_len'] == 0:
                continue
            if page['page_len'] > len_of_page_with_content:
                start_range = cls._parse_page_number_from_url_(page['url'])
            else:
                finish_range = cls._parse_page_number_from_url_(page['url'])
                break
        # если не найдена пустая страница возбуждается исключение для изменения параметров поиска
        if finish_range is None:
            raise SearchScopeIsFullOfValidPagesException
        return start_range, finish_range

    @staticmethod
    def _parse_page_number_from_url_(current_url: str) -> int:
        """Получить номер страницы из URL"""
        page_number = current_url.split('/')[-1]
        return int(page_number)


class Parser:
    """Получение последней страницы"""

    initial_first_page = 1  # страница с которой необходимо начать поиск
    search_range = 200  # посл. страница в разрезе которой необходимо проводить поиск, если в указанном срезе не будет
    # найдена посл. страница, переходим к следующему разрезу
    len_of_page_with_content = 89000  # минимальная длина непустой страницы (html - документа)

    def _out_of_scope_wrapper_(func):
        """Декоратор перезапускающий функцию с новыми параметрами, если текущая не нашла последнюю страницу"""
        def inner_func(self):
            while True:
                try:
                    return func(self)
                except SearchScopeIsFullOfValidPagesException:
                    self.initial_first_page += self.search_range
        return inner_func

    @_out_of_scope_wrapper_
    def get_last_page(self):
        """Получить последнюю страницу"""
        initial_last_page_range = self.search_range + self.initial_first_page
        search_params = Utils.get_search_params(self.initial_first_page, initial_last_page_range)
        while True:
            ps_store_connection = PsStoreConnection(search_params)
            pages = ps_store_connection.get_pages()
            start_range, finish_range = Utils.get_new_range(pages, self.initial_first_page, self.len_of_page_with_content)
            if finish_range - start_range == 1:  # если первая и последняя страницы - соседние, значит мы нашли последнюю страницу
                return start_range
            search_params = Utils.get_search_params(start_range, finish_range)


def lambda_handler(event, context):
    start_time = time()
    parser = Parser()
    last_page = parser.get_last_page()
    total_time = time() - start_time
    return {
        'last_page': last_page,
        'work_time': round(total_time, 2)
    }
