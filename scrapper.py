"""
Crawler implementation
"""

from datetime import datetime
import json
import os
from random import randint
import re
from time import sleep

from bs4 import BeautifulSoup
import requests

from constants import PROJECT_ROOT, ASSETS_PATH, CRAWLER_CONFIG_PATH


class IncorrectURLError(Exception):
    """
    Custom error
    """
    pass


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Custom error
    """
    pass


class IncorrectNumberOfArticlesError(Exception):
    """
    Custom error
    """
    pass


class UnknownConfigError(Exception):
    pass


class BadStatusCode(Exception):
    pass


class Crawler:
    """
    Crawler implementation
    """
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'}
    pages_path = os.path.join(PROJECT_ROOT, 'tmp', 'pages')

    def __init__(self, seed_urls: list, max_articles: int = None, max_articles_per_seed: int = None):
        self.seed_urls = seed_urls
        self.seed_urls_set = set()
        self.max_articles = max_articles
        self.max_articles_per_seed = max_articles_per_seed
        self.urls = []

    @staticmethod
    def _extract_url(article_bs, urls):
        new_links = []
        for link in article_bs.find_all('a'):
            if res := re.findall(r'https://www.zvezdaaltaya.ru/\d{4}/\d{2}/.+', link.get('href')):
                if not re.findall(r'https://www.zvezdaaltaya.ru/\d{4}/\d{2}/\d{2}/', res[0]):
                    if res[0] not in urls:
                        new_links.append(res[0])
        with open(os.path.join(PROJECT_ROOT, 'links.txt', 'a')) as f:
            f.write('\n'.join(new_links) + '\n')
        return new_links

    def find_articles(self):
        """
        Finds articles
        """
        if not os.path.exists(Crawler.pages_path):
            os.makedirs(Crawler.pages_path)
            self.id_generator = iter(range(1, self.max_articles + 1))

        for url in self.seed_urls:
            try:
                page = Crawler.get_page(url, self.headers)
                with open(os.path.join(Crawler.pages_path, f'{next(self.id_generator)}.html'), 'w') as f:
                    f.write(page)
            except BadStatusCode:
                continue
            else:
                soup = BeautifulSoup(page, 'html.parser')
                new_links = crawler._extract_url(soup, self.urls)
                self.urls.extend(new_links)
                self.get_search_urls(soup)
            self.seed_urls.pop(url)
        else:
            if len(self.urls) > max_articles:
                with open(os.path.join(PROJECT_ROOT, 'links.txt'), 'w') as f:
                    f.write('\n'.join(self.urls[:max_articles]))

    def get_search_urls(self, soup):
        """
        Returns seed_urls param
        """
        for link in soup.find_all('a'):
            if res := re.findall(r'https://www.zvezdaaltaya.ru/.+', link.get('href')):
                if res[0] not in self.seed_urls:
                    self.seed_urls.append(res[0])
                    self.seed_urls_set.add(res[0])

    @staticmethod
    def get_page(url, headers):
        response = requests.get(url, headers=Crawler.headers)
        if response.status_code == 200:
            page = response.text
        else:
            raise BadStatusCode
        sleep(randint(3, 10))
        return page


class ArticleParser:
    """
    ArticleParser implementation
    """
    def __init__(self, full_url: str, article_id: int):
        self.full_url = full_url
        self.article_id = article_id
        self.article = ''
        self.title = ''
        self.date = ''
        self.author = ''

    def _fill_article_with_text(self, article_soup):
        for paragraph in article_soup.find_all('p')[:-3]:
            self.article += paragraph.text + ' '

    def _fill_article_with_meta_information(self, article_soup):
        # self.url = article_soup.find('meta', {'property': 'og:url'})['content']
        self.title = re.sub(r' - Звезда Алтая', '', article_soup.find('title').text)
        date_str = article_soup.find('span', {'class': 'mg-blog-date'}).text.strip()
        self.date = self.unify_date_format(date_str)
        self.author = article_soup.find('h4', {'class': 'media-heading'}).find('a').text

    @staticmethod
    def unify_date_format(date_str):
        """
        Unifies date format
        """
        month_dict = {
            'Янв': 1,
            'Фев': 2,
            'Мар': 3,
            'Апр': 4,
            'Май': 5,
            'Июн': 6,
            'Июл': 7,
            'Авг': 8,
            'Сен': 9,
            'Окт': 10,
            'Ноя': 11,
            'Дек': 12
        }

        month, day, year = date_str.split()
        day = int(day[:-1])
        year = (int(year))
        month = month_dict[month]
        return datetime(year, month, day)

    def parse(self):
        """
        Parses each article
        """
        article_page = Crawler.get_page(self.full_url, Crawler.headers)
        with open(os.path.join(ASSETS_PATH,f'{self.article_id}_page.html', 'w')) as f:
            f.write(article_page)
        soup = BeautifulSoup(article_page, 'html.parser')
        self._fill_article_with_meta_information(soup)
        self._fill_article_with_text(soup)
        return self.article

    def save_raw(self):
        with open(os.path.join(ASSETS_PATH,f'{self.article_id}_raw.txt', 'w')) as f:
            f.write(self.article)

    def save_meta(self):
        meta = {
            "url": self.full_url,
            "title": self.title,
            "date": self.date,
            "author": self.author
        }

        with open(os.path.join(ASSETS_PATH, f'{self.article_id}_meta.json')) as f:
            json.dump(meta, f)

    def from_meta_json(self):
        with open(os.path.join(ASSETS_PATH, f'{self.article_id}_meta.json')) as f:
            meta = json.load(f)
        return meta

    def get_raw_text(self):
        raw = open(os.path.join(ASSETS_PATH, f'{self.article_id}_raw.txt')).read()
        return raw

    def save_processed(self, processed_text):
        with open(os.path.join(ASSETS_PATH, f'{self.article_id}_processed.txt', 'w')) as f:
            f.write(processed_text)



def prepare_environment(base_path):
    """
    Creates ASSETS_PATH folder if not created and removes existing folder
    """
    if not os.path.exists(os.path.join(base_path, 'tmp', 'articles')):
        os.makedirs(os.path.join(base_path, 'tmp', 'articles'))


def validate_config(crawler_path):
    """
    Validates given config
    """
    with open(crawler_path) as f:
        config = json.load(f)

    is_config_a_dict = isinstance(config, dict)
    is_base_urls_correct = (
            isinstance(config['base_urls'], list) and
            isinstance(config['base_urls'][0], str)
    )
    is_total_number_of_articles_correct = (
        isinstance(config['total_articles_to_find_and_parse'], int),
        config['total_articles_to_find_and_parse'] > 0
    )
    is_max_number_of_articles_int = (
        isinstance(config['max_number_articles_to_get_from_one_seed'], int),
        config['max_number_articles_to_get_from_one_seed'] > 0
    )

    is_max_number_of_articles_correct = (
            config['max_number_articles_to_get_from_one_seed'] <=
            config['total_articles_to_find_and_parse']
    )

    if all((
            is_config_a_dict,
            is_base_urls_correct,
            is_total_number_of_articles_correct,
            is_max_number_of_articles_int,
            is_max_number_of_articles_correct
    )):
        return config.values()

    elif not is_base_urls_correct:
        raise IncorrectURLError

    elif not is_total_number_of_articles_correct:
        raise IncorrectNumberOfArticlesError

    elif not is_max_number_of_articles_correct:
        raise NumberOfArticlesOutOfRangeError

    else:
        raise UnknownConfigError


if __name__ == '__main__':
    prepare_environment(PROJECT_ROOT)

    try:
        seed_urls, max_articles, max_articles_per_seed = validate_config(CRAWLER_CONFIG_PATH)
    except (
            IncorrectURLError,
            IncorrectNumberOfArticlesError,
            NumberOfArticlesOutOfRangeError,
            UnknownConfigError
    ):
        pass  # todo script immediately finishes execution
    else:
        crawler = Crawler(
            seed_urls=seed_urls,
            max_articles=max_articles,
            max_articles_per_seed=max_articles_per_seed
        )
        crawler.find_articles()
        parser = ArticleParser(article_url=full_url, article_id=i)
        try: parse
        except BadStatusCode:
