import requests
import os
import yaml
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse

# Инициализировать набор ссылок (уникальные ссылки)
int_url = set() #задаем массивы
ext_url = set()
# Количество посещенных URL-адресов
visited_urls = 0


def is_valid(url):
    """
    Проверяем, является ли url действительным URL
    """
    parsed = urlparse(url) #разбиваем на 6 частей ссылку
    return bool(parsed.netloc) and bool(parsed.scheme) #проверка протокола и домена


# Возвращаем все URL-адреса
def get_website_links(url):
    urls = set()
    # извлекаем доменное имя из URL
    domain_name = urlparse(url).netloc
    # скачиваем HTML-контент вэб-страницы
    soup = bs(requests.get(url).content, "html.parser") #скачиваем html разметку
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href пустой тег
            continue
        # присоединить URL, если он относительный (не абсолютная ссылка)
        href = urljoin(url, href)
        parsed_href = urlparse(href) #парсим и разделяем ссылку чтобы убрать лишние параметры
        # удалить параметры URL GET, фрагменты URL и т. д.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # недействительный URL
            continue
        if href in int_url:
            # уже в наборе дочерних
            continue
        if domain_name not in href:
            # внешняя ссылка
            if href not in ext_url:
                print(f"[!] External link: {href}")
                ext_url.add(href)
            continue
        print(f"[*] Internal link: {href}")
        urls.add(href)
        int_url.add(href)
    return urls


# Просматриваем веб-страницу и извлекаем все ссылки.
def crawl(url, max_urls=50):
    # max_urls (int): количество макс. URL для сканирования
    if not is_valid(url):
        return
    global visited_urls
    visited_urls += 1
    links = get_website_links(url) #берем дочерние ссылки с сайта
    for link in links:
        if visited_urls > max_urls:
            break
        crawl(link, max_urls=max_urls)


def get_all_images(url):
    """
    Возвращает все URL‑адреса изображений по одному `url`
    """
    soup = bs(requests.get(url).content, "html.parser") #получаем Dom объект
    urls = []
    for img in tqdm(soup.find_all("img"), "Image received"): #вывод прогресс бара, поиск по тегам img
        img_url = img.attrs.get("src")
        if not img_url:
            # если img не содержит атрибута src, просто пропускаем
            continue
        # сделаем URL абсолютным, присоединив имя домена к только что извлеченному URL
        img_url = urljoin(url, img_url)
        # удалим URL‑адреса типа '/hsts-pixel.gif?c=3.2.5'
        try:
            pos = img_url.index("?") #ищем параметры, если есть то убираем
            img_url = img_url[:pos]
        except ValueError:
            pass
        # наконец, если URL действителен
        if is_valid(img_url):
            urls.append(img_url)
    return urls


def download(url, pathname, minSize=20000):
    """
    Загружает файл по URL‑адресу и помещает его в папку `pathname`
    """
    # если путь не существует, создать dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    # загружаем тело ответа по частям, а не сразу
    response = requests.get(url, stream=True)
    # получить общий размер файла
    file_size = int(response.headers.get("Content-Length", 0))
    #print(file_size)
    if file_size <= minSize:
        return
    # получаем имя файла
    filename = os.path.join(pathname, url.split("/")[-1])
    # индикатор выполнения, изменение единицы измерения на байты вместо итераций (по умолчанию tqdm)
    progress = tqdm(response.iter_content(1024), f"Download {filename}", total=file_size, unit="kB", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f: #открываем или создаем файл создаем объект f
        for data in progress.iterable:
            # записываем прочитанные данные в файл
            f.write(data)
            # обновление индикатора выполнения вручную
            progress.update(len(data))


if __name__ == '__main__':
    with open('params.yaml') as f:
        read_data = yaml.safe_load(f)

    # url1 = 'http://www.finepix-x100.com/gallery/images'
    url = read_data.get('url')
    path = read_data.get('path')
    size = read_data.get('min-size')
    max_urls = read_data.get('max-urls')

    crawl(url, max_urls) #вывод ссылок и итогового количества
    print("[+] Total External links:", len(ext_url))
    print("[+] Total Internal links:", len(int_url))
    print("[+] Total:", len(ext_url) + len(int_url))
    imgs = get_all_images(url) #получаем массив ссылок на изображения с главной страницы

    for urls in int_url: #получаем ссылки на изображения с дочерних страниц и устанавливаем
        imgs = get_all_images(urls)
        for img in imgs:
            # скачать для каждого img
            download(img, path, size)
