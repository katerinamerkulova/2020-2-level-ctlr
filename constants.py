"""
Useful constant variables
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

ASSETS_PATH = os.path.join(PROJECT_ROOT, 'tmp', 'articles')
CRAWLER_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'crawler_config.json')

ARTIFACTS_ROOT = os.path.join(PROJECT_ROOT, 'tmp')
PAGES_ROOT = os.path.join(ARTIFACTS_ROOT, 'pages')

TO_PARSE_URLS = os.path.join(ARTIFACTS_ROOT, 'to_parse_urls.txt')
SEEN_URLS = os.path.join(ARTIFACTS_ROOT, 'seen_urls.txt')
ARTICLE_URLS = os.path.join(ARTIFACTS_ROOT, 'article_urls.txt')
