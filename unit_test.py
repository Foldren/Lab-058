import unittest
import os
from os.path import getsize, join
import yaml
import main


class UrlCheckingTestCase(unittest.TestCase):
    def test_netloc_validation(self):
        self.assertFalse(main.is_valid("htt ps://docs-python.ru/search/"), 'wrong netloc validation')

    def test_scheme_validation(self):
        self.assertFalse(main.is_valid("test:||docs-python.ru/search"), 'wrong scheme validation')


class CrawlTestCase(unittest.TestCase):

    def test_not_valid_url(self):
        self.assertFalse(main.crawl("htt ps://docs-python.ru/search/"), 'wrong url validation')

    def test_urls_count(self):
        main.crawl("https://docs-python.ru/search/")
        with open('params.yaml') as f:
            read_data = yaml.safe_load(f)
        max_urls = read_data.get('max-urls')
        self.assertLessEqual(main.visited_urls, max_urls, 'wrong urls counting')


class ImagesGettingTestCase(unittest.TestCase):

    def test_not_valid_image_url(self):
        self.assertFalse(main.get_all_images("https://docs-python.ru/123.gif?c=3.2.5"), 'wrong image url validation')


class ImagesDownloadingTestCase(unittest.TestCase):

    def setUp(self):
        self.pathname = "downloads"
        self.url = "https://newtechaudit.ru/"
        self.min_size = 10000
        main.download(self.url, self.pathname, self.min_size)

    def tearDown(self):
        pass

    def test_directory_not_created(self):
        self.assertTrue(os.path.isdir(self.pathname), 'directory not created')

    def test_images_not_downloaded(self):
        self.assertNotEqual(len(os.listdir(self.pathname)), 0, 'images not downloaded')

    def test_images_too_small(self):
        for root, dirs, files in os.walk(self.pathname):
            for name in files:
                self.assertGreater(int(getsize(join(root, name))), self.min_size, 'images smaller than minimal length downloaded')


if __name__ == '__main__':
    unittest.main()
