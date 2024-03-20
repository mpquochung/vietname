# encoding: utf-8
"""
Extract content from html file using xpath syntax
"""
import asyncio
import base64
import os
import random
import time
from itertools import cycle

import requests
from bs4 import BeautifulSoup
from lxml import html, etree
from lxml.html import fromstring
from pyppeteer import launch

from common.file_utils import read_json_file, write_json_file

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:46.0) "
                  "Gecko/20100101 Firefox/46.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0"
}
PROXY_JSON_PATH = 'vs/common/data/proxy_list.json'


def xtract_from_url_with_proxy(url, xpath):
    proxies, proxies_json = get_proxies_free_proxy()
    random.shuffle(proxies)
    proxy_pool = cycle(proxies)
    SLEEP = 5
    cnt = len(proxies)
    while cnt > 0:
        proxy = next(proxy_pool)
        try:
            page = requests.get(url, proxies={"http": 'http://%s' % proxy, "https": 'https://%s' % proxy}, timeout=10)
            print("status code", page.status_code)
            if page.status_code == 403 or page.status_code == 429:
                cnt -= 1
                print("Proxy %s is forbinder" % proxy)
                proxies_json[proxy] = 4
                write_json_file(PROXY_JSON_PATH, proxies_json)
                time.sleep(SLEEP)
                continue
            cnt = 0
        except Exception as ex:
            print('Fail with request %s, retry in %ss, %s  times left' % (url, SLEEP, cnt))
            cnt -= 1
            # update proxy bị lỗi
            proxies_json[proxy] = proxies_json[proxy] + 1
            write_json_file(PROXY_JSON_PATH, proxies_json)
            time.sleep(SLEEP)

    tree = html.fromstring(page.text)
    return tree.xpath(xpath)


def remove_html_tag(html_node):
    try:
        a_tag_str = etree.tostring(html_node, encoding='UTF-8')
        soup = BeautifulSoup(a_tag_str)
        text = soup.get_text()
    except Exception as ex:
        print(ex)
        return ''
    return text


def get_proxies_free_proxy():
    """
    lấy proxy được lưu ở local trước, nếu có thì dùng, nếu không có thì lấy online
    """
    # 1. lấy proxy được lưu trước,
    proxy_list = []
    if os.path.exists(PROXY_JSON_PATH):
        proxy_dict = read_json_file(PROXY_JSON_PATH)
        proxy_list = [proxy for proxy, failure_times in proxy_dict.items() if failure_times < 4]

    if len(proxy_list) > 0:
        return proxy_list, proxy_dict

    url = 'http://free-proxy.cz/en/proxylist/country/all/https/speed/all'
    proxies = set()
    table = xtract_from_url(url, '//*[@id="proxy_list"]')
    rows = xtract(table[0], '..//tbody/tr')
    if rows:
        for tr in rows:
            td = xtract(tr, './/td')
            if len(td) == 11:
                td_ip_tag_str = remove_html_tag(td[0])
                port = remove_html_tag(td[1])
                try:
                    ip = base64.b64decode(td_ip_tag_str).decode('UTF-8')
                except:
                    ip = td_ip_tag_str
                if ip and port:
                    proxy = ':'.join([ip, port])
                    proxies.add(proxy)
    # lưu proxies vào file read_json_file
    proxies_json = {item: 0 for item in proxies}
    write_json_file(PROXY_JSON_PATH, proxies_json)
    return proxies, proxies_json


async def get_proxies_free_proxy_new():
    """
    lấy proxy được lưu ở local trước, nếu có thì dùng, nếu không có thì lấy online
    """
    # 1. lấy proxy được lưu trước,
    proxy_list = []
    if os.path.exists(PROXY_JSON_PATH):
        try:
            proxy_dict = read_json_file(PROXY_JSON_PATH)
            proxy_list = [proxy for proxy, failure_times in proxy_dict.items() if failure_times < 4]
        except:
            proxy_list = []

    if len(proxy_list) > 0:
        return proxy_list, proxy_dict

    url = 'https://spys.one/en/https-ssl-proxy/'
    proxies = set()
    table = await xtract_from_url_headless_browser(url, '/html/body/table[2]/tbody/tr[4]/td/table')
    rows = xtract(table[0], '..//tr')
    if rows:
        for tr in rows:
            td = xtract(tr, './/td')
            if len(td) == 10:
                td_ip_tag_str = remove_html_tag(td[0])
                proxies.add(td_ip_tag_str)
    # lưu proxies vào file read_json_file
    proxies_json = {item: 0 for item in proxies}
    write_json_file(PROXY_JSON_PATH, proxies_json)
    return proxies, proxies_json


def get_proxies():
    url = 'https://www.us-proxy.org/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = []
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.append(proxy)
    return proxies


def inner_html(node):
    """
    get original html from a node
    """
    return (node.text or '') + ''.join(
        [html.tostring(child) for child in node.iterchildren()])


def xtract_from_url(url, xpath):
    """
    Extract all elements from url
    :param url:
    :param xpath:
    :return: list of values
    """
    SLEEP = 10
    cnt = 6
    while cnt > 0:
        try:
            page = requests.get(url, headers=HEADERS)
            cnt = 0
        except Exception as ex:
            print(ex)
            print('Fail with request %s, retry in %ss, %s  times left' % (url, SLEEP, cnt))
            cnt -= 1
            time.sleep(SLEEP)

    tree = html.fromstring(page.text)
    return tree.xpath(xpath)


async def xtract_from_url_headless_browser(url, xpath):
    """
    Extract all elements from url
    :param url:
    :param xpath:
    :return: list of values
    """
    global html_page_string
    SLEEP = 10
    cnt = 6
    browser = await launch({'headless': True})
    page = await browser.newPage()

    while cnt > 0:
        try:
            await page.setExtraHTTPHeaders(headers=HEADERS)
            await page.goto(url=url)
            html_page_string = await page.evaluate("() => document.documentElement.outerHTML")
            cnt = 0
        except Exception as ex:
            print(ex)
            print('Fail with request %s, retry in %ss, %s  times left' % (url, SLEEP, cnt))
            cnt -= 1
            time.sleep(SLEEP)
    await page.close()
    await browser.close()
    tree = html.fromstring(html_page_string)
    return tree.xpath(xpath)


def xtract(node, xpath):
    """
    Extract from a node
    :param node:
    :param xpath:
    :return: list of values
    """
    return node.xpath(xpath)


def xtract_first_from_url(url, xpath):
    """
    Extract first element from url
    :param url:
    :param xpath:
    :return: first value
    """
    nodes = xtract_from_url(url, xpath)
    if len(nodes) == 0:
        return None
    return nodes[0]


def xtract_first(node, xpath):
    """
    Extract first element from a node
    """
    nodes = node.xpath(xpath)[0]
    if len(nodes) == 0:
        return None
    return nodes[0]


def xtract_html(node, xpath):
    """
    Extract whole html content fron a node
    :param node:
    :param xpath:
    """
    return inner_html(node.xpath(xpath)[0])


def xtract_fields(url, field_xpaths):
    """
    Extract multiple fields from url
    :param url:
    :param field_xpaths: dictionary of field and xpath, for example:
        {
        'date': '//table[@summary=""]/tbody/tr/td[1]/span/a/text()',
        'content': '//table[@summary=""]/tbody/tr/td[2]/span/text()'
        }
    :return:
    """
    page = requests.get(url, headers=HEADERS)
    tree = html.fromstring(page.text)
    return xtract_fields_from_node(tree, field_xpaths)


def xtract_fields_from_node(node, field_xpaths):
    results = {}
    for k, v in field_xpaths.items():
        results[k] = node.xpath(v)

    return results


def xtract_cleaned_fields_from_url(url, field_xpaths):
    """
    Return only first extracted element
    """
    page = requests.get(url, headers=HEADERS)
    tree = html.fromstring(page.text)
    return xtract_cleaned_fields(tree, field_xpaths)


def xtract_cleaned_fields(node, field_xpaths):
    results = {}
    for k, v in field_xpaths.items():
        values = node.xpath(v)
        if values is None or len(values) == 0:
            results[k] = None
        else:
            results[k] = values[0].strip()

    return results


def xtract_table(url, field_xpaths):
    values = {}
    page = requests.get(url, headers=HEADERS)
    # print page.text
    tree = html.fromstring(page.text)
    length = 0
    for k, v in field_xpaths.items():
        values[k] = tree.xpath(v)
        # print k, values[k]
        newLength = len(values[k])
        if length != 0 and newLength != length:
            print('WARNING: Column size is different between values:', length, newLength)
            return []
        length = newLength
    """
        Convert map to list to transform table:
        {
            "k1" : ["v11", "v12"],
            "k2" : ["v21", "v22"]
        }
        =>
        [
            {
                "k1": "v11",
                "k2" : "v21"
            },
            {
                "k1": "v12",
                "k2" : "v22"
            }
        ]
    """
    results = []
    for i in range(0, length):
        item = {}
        for k, v in values.items():
            item[k] = v[i]
        results.append(item)
    return results


def example1():
    print(xtract_from_url('http://www.swisscom.ch', '/html/head/title/text()'))
    print(xtract_from_url('http://www.swisscom.ch', '/html/head/meta[@name="description"]/@content'))

    field_xpaths = {
        'title': '/html/head/title/text()',
        'description': '/html/head/meta[@name="description"]/@content'
    }
    print(xtract_fields('https://www.post.ch', field_xpaths))
    print(xtract_fields('http://de.burger-king.ch', field_xpaths))


def example2():
    field_xpaths = {
        'date': '//table[@summary=""]/tbody/tr/td[1]/span/a/text()',
        'content': '//table[@summary=""]/tbody/tr/td[2]/span/text()'
    }
    print(
        xtract_table('http://www.wallisellen.ch/de/polver/verwaltung/abfallver/abfalldaten/welcome.php', field_xpaths))


def example3():
    print(xtract_from_url('https://www.tripadvisor.com/Restaurants-g188045-Switzerland.html#LOCATION_LIST',
                          '//div[@class="geo_name"]/a/@href'))


def main():
    example1()
    example2()
    example3()


async def example_new():
    proxies, proxies_json = await get_proxies_free_proxy_new()
    print(proxies)
    print(proxies_json)


if __name__ == '__main__':
    # main()
    asyncio.get_event_loop().run_until_complete(example_new())
