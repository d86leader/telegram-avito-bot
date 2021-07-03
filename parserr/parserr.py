#!/usr/bin/env python3
import json
import re
import requests
import time
from bs4 import BeautifulSoup # type: ignore
from requests import RequestException

from typing import Optional, List


class Advertizement:
    title: str
    price: Optional[str]
    url: str
    image: Optional[str] # link to image

    _prefix_re = re.compile("(https?://)?(m\.)?avito.ru")

    def __init__(self, title, url, image=None, price=None) -> None:
        self.title = title
        site_prefix ="https://avito.ru"
        self.url = (site_prefix if not self._prefix_re.match(url) else "") + url
        self.image = image
        self.price = price

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "price": self.price,
            "url": self.url,
            "image": self.image,
        }

    @staticmethod
    def from_dict(d: dict) -> 'Advertizement':
        return Advertizement(
            d["title"],
            d["url"],
            d.get("image", None),
            d.get("price", None),
        )

    def lax_eq(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.url == other.url

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        def optional_eq(a, b) -> bool:
            return a is None or b is None or a == b

        return ( self.title == other.title
            and  self.url == other.url
            and  optional_eq(self.image, other.image)
            and  optional_eq(self.price, other.price)
        )

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.title, self.url, self.image, self.price))

    def __repr__(self) -> str:
        return (
            f"Advertizement( \"{self.title}\", \"{self.url}\""
            + (f", image=\"{self.image}\"" if self.image else "")
            + (f", price=\"{self.price}\"" if self.price else "")
            + " )"
        )

    def __str__(self) -> str:
        return repr(self)


def get_proxy():
    proxy = requests.get(
        'https://gimmeproxy.com/api/getProxy?country=RU&get=true&supportsHttps=true&protocol=http')
    proxy_json = json.loads(proxy.content)
    if proxy.status_code != 200 and 'ip' not in proxy_json:
        raise RequestException
    else:
        return 'http://' + proxy_json['ip'] + ':' + proxy_json['port']


def get_html(url):
    import random
    USER_AGENTS = [
        'Mozilla/5.0 (Linux; Android 7.0; SM-G930VC Build/NRD90M; wv)',
        'Chrome/70.0.3538.77 Safari/537.36',
        'Opera/9.68 (X11; Linux i686; en-US) Presto/2.9.344 Version/11.00',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows 95; Trident/5.1)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_6) AppleWebKit/5342 (KHTML, like Gecko) Chrome/37.0.896.0 Mobile Safari/5342',
        'Mozilla/5.0 (Windows; U; Windows NT 6.2) AppleWebKit/533.49.2 (KHTML, like Gecko) Version/5.0 Safari/533.49.2',
        'Mozilla/5.0 (Windows NT 5.0; sl-SI; rv:1.9.2.20) Gecko/20110831 Firefox/37.0'
    ]
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }
    proxy = {
        # 'https': get_proxy()
    }
    response = requests.get(url, headers=headers)
    return response.content


def parse_ads_classful(soup: BeautifulSoup) -> List[Advertizement]:
    """
    Parse ads with specific class name. Doesn't work sometimes
    """
    ad_link_re = re.compile("^iva-item-sliderLink")

    ads = soup.find_all("a", {"class": ad_link_re})

    ads_list = []
    for ad in ads:
        try:
            title = ad.attrs.get("title")
            url = ad.attrs["href"]
        except NameError:
            continue

        imgs = ad.find_all("img")
        if len(imgs) > 0:
            img = imgs[0].attrs["src"]
        else:
            img = None

        ads_list.append(Advertizement(
            title=title.replace(u'\xa0', u' '),
            url=url,
            image=img,
        ))

    return ads_list

def parse_ads_marker(soup: BeautifulSoup) -> List[Advertizement]:
    """
    Parse ads only knowing that they have specific data marker
    """

    ads = soup.find_all("a", {"data-marker": "item/link"})
    ads_list = []
    for ad in ads:
        try:
            url = ad.attrs["href"]
        except NameError:
            continue
        children = list(ad.children)
        if len(children) == 1:
            body = children[0]
            if not isinstance(body, str):
                title = body
                # only thus we append new
                ads_list.append(Advertizement(title, url))
    return ads_list

def parse_ads(soup: BeautifulSoup) -> List[Advertizement]:
    p1 = parse_ads_classful(soup)
    if len(p1) != 0:
        return p1
    return parse_ads_marker(soup)


def get_ads_list(avito_search_url: str) -> List[Advertizement]:
    """
    :param avito_search_url: url like https://m.avito.ru/kazan/avtomobili/inomarki?pmax=200000&pmin=50000
    :return: ads list
    """
    html = get_html(avito_search_url)
    soup = BeautifulSoup(html, 'lxml')
    return parse_ads(soup)


def get_new_ads(new: List[Advertizement], old_: dict) -> List[Advertizement]:
    result = []
    old = [Advertizement.from_dict(x) for x in old_]
    for new_ad in new:
        for old_ad in old:
            if old_ad.lax_eq(new_ad):
                break
        else:
            result.append(new_ad)
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} url\n\tParse the current ads and print them")
        sys.exit(1)
    url = sys.argv[1]
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')

    p1 = parse_ads_classful(soup)
    if len(p1) == 0:
        print("No ads with classful method")
    else:
        for ad in p1:
            print(f"{ad}")

    p2 = parse_ads_marker(soup)
    if len(p2) == 0:
        print("No ads with marker method")
    else:
        for ad in p2:
            print(f"{ad}")
