# coding:utf-8
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import uuid
import re
from bs4 import BeautifulSoup
import urllib2
import requests
import json


class TmallScrap:
    url = 'https://list.tmall.com/search_product.htm?q=%B1%CA%BC%C7%B1%BE&type=p&vmarket=&spm=875.7931836%2FB.a2227oh.d100&from=mallfp..pc_1_searchbutton'
    cookie = ''

    def __init__(self):
        driver = webdriver.Chrome()
        driver.get("https://login.taobao.com/member/login.jhtml")
        time.sleep(5)
        # 用户名 密码
        elem_user = driver.find_element_by_name("TPL_username")
        elem_user.send_keys("your user name")
        elem_pwd = driver.find_element_by_name("TPL_password")
        elem_pwd.send_keys("your password")
        submit_btn = driver.find_element_by_id("J_SubmitStatic")

        time.sleep(3)
        submit_btn.send_keys(Keys.ENTER)

        cookies = driver.get_cookies()
        self.cookie = "; ".join([item["name"] + "=" + item["value"] for item in cookies])

    def get_soup(self, _url, _cookie, _refer=None):
        url = _url
        headers = {
            "user-agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36",
            "cookie": self.cookie,
            "referer": _refer}

        response = requests.get(url, headers=headers)
        contents = response.content

        soup = BeautifulSoup(contents, 'html.parser')
        return soup

    def save_image(self, _url, save_path, _filename):
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        img_data = requests.get(_url).content
        path = save_path + "/" + _filename + '.jpg'
        with open(path, 'wb') as handler:
            handler.write(img_data)

    def get_basicinfo(self, soup):
        product_list = []
        product_title = soup.find("div", {"id": "J_ItemList"})
        # print product_title

        # take care 广告
        # product_title = [x for x in product_title if x.get('class', []) == ['product', 'item-1111', '']]
        product_item = product_title.find_all("div", {"class": "product "})
        for index, item in enumerate(product_item):
            product_img =[]
            shop_name = item.find("div", class_='productShop').find("a", class_='productShop-name').text
            shop_price = item.find("p", class_='productPrice').find("em").text
            shop_title = item.find("div", class_='productTitle').find_all("a")
            product_name = ''
            for item_title in shop_title:
                product_name += item_title.text.strip()
            shop_status = item.find("p", class_='productStatus') and item.find("p", class_='productStatus').text
            product_status = shop_status and shop_status.strip() or "No Shop Status"
            shop_http = 'http:' + item.find("div", class_='productImg-wrap').find("a")['href']
            try:
                url_img = 'http:' + item.find("div", class_='productImg-wrap').find("a").find("img")['src']
            except:
                url_img = 'http:' + item.find("div", class_='productImg-wrap').find("a").find("img")['data-ks-lazyload']
            save_path = 'img'
            file_name = str(uuid.uuid4())
            product_img.append(file_name)
            self.save_image(url_img,save_path,file_name)
            prosoup = self.get_soup(shop_http, self.cookie, shop_http)
            ulimgs = prosoup.find('ul', {"id": "J_UlThumb"})
            imglist = ulimgs.find_all('li')
            for index2, img in enumerate(imglist):
                detailsrc = 'http:' + img.find('a').find('img')['src']
                detail_file_path = 'img'
                detail_file_name = str(uuid.uuid4())
                self.save_image(detailsrc, detail_file_path, detail_file_name)
                product_img.append(detail_file_name)
            sss = prosoup.find("div", {"id": "J_DetailMeta"})
            map_list = []
            m = re.search(r"\"(skuList)\":\[(.*?)\]", str(sss))
            pro_json = json.loads('{' + (m.group(0)) + '}')
            pro_list = pro_json['skuList']
            y = re.findall(r"\"(skuId)\":\"(\d+)\",\"(stock)\":(\d+)", str(sss))
            for item_y in y:
                map_json = {item_y[0]: item_y[1],
                            item_y[2]: item_y[3]
                            }
                map_list.append(map_json)
            list_n = []
            for i in map_list:
                for y in pro_list:
                    if i['skuId'] == y[u'skuId']:
                        map_json = {
                            'skuId': i['skuId'],
                            'product name': y[u'names'],
                            'stock': i['stock']
                        }
                        list_n.append(map_json)
            detail = {
                "Shop Name": shop_name.strip(),
                "Product Price": shop_price.strip(),
                "Product Name": product_name,
                "product Image List": product_img,
                "Product Status": product_status,
                "Http": shop_http,
                "Product List": list_n
            }
            product_list.append(detail)
        return product_list

    def out(self, _list):
        for item in _list:
            print "Shop Name:", item['Shop Name']
            print "Product Price:", item['Product Price']
            print "Product Name:", item['Product Name']
            for p in item['product Image List']:
                print p+'.img'
            print "Product Status:", item['Product Status']
            print "Http:", item['Http']
            for i in item['Product List']:
                print 'Product Name:', i['product name'], '  SkuId:', i['skuId'], '  Stock Value:', i['stock']
            print '\n'


if __name__ == '__main__':
    p = TmallScrap()
    soup = p.get_soup(p.url, p.cookie)
    t_list = p.get_basicinfo(soup)
    p.out(t_list)
