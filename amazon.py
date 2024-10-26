import scrapy
from scrapy.crawler import CrawlerProcess
import re
from pprint import pprint
import json

class AmazonWishlistSpider(scrapy.Spider):
    BASE_URL = 'https://www.amazon.com'
    name = 'amazonwishlist'
    allowed_domains = ['www.amazon.com']

    def __init__(self, uri, scraped_data, **kwargs):
        self.scraped_data = scraped_data
        self.start_urls = [uri]

        domain = re.sub(r'(http|https)?://', '', uri)
        self.allowed_domains.append(domain)

        super().__init__(**kwargs)

    def parse(self, response):
        page_items = response.css(".g-item-sortable")

        for item in page_items:
            id = item.css('li::attr(data-itemid)').extract_first()
            title = item.css('#itemName_'+id + "::text").extract_first()
            link = item.css('#itemName_'+id + "::attr(href)").extract_first()
            img = item.css('#itemImage_'+id).css('img::attr(src)').extract_first()
            try:
                quantity_needed = int(item.css("#itemRequested_"+id+"::text").extract_first().strip())
            except:
                quantity_needed = None
            try:
                quantity_purchased = int(item.css("#itemPurchased_"+id+"::text").extract_first().strip())
            except:
                quantity_purchased = None
            try:
                comment = item.css("#itemComment_"+id+"::text").extract_first().strip()
            except:
                comment = None

            obj = {
                'id': id,
                'title': title.strip(),
                'link': link,
                'img': img,
                'needed': quantity_needed,
                'purchased': quantity_purchased,
                'comments': comment
            }

            self.scraped_data.append(obj)
            yield obj

        has_next = response.css('.a-size-base.a-link-nav-icon.a-js.g-visible-no-js.wl-see-more').extract_first()
        if has_next:
            lek_uri = response.css('.a-size-base.a-link-nav-icon.a-js.g-visible-no-js.wl-see-more::attr(href)').extract_first()
            next_page = self.BASE_URL + lek_uri
            yield scrapy.Request(next_page)

def get_data(id: str):
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'LOG_LEVEL': 'INFO'
    })
    url = f"https://www.amazon.com/hz/wishlist/ls/{id}"
    scraped_data = []
    process.crawl(AmazonWishlistSpider, url, scraped_data)
    process.start()
    return scraped_data
    

def scrape_all_amazon() -> list:
    res = []
    wishlists = {
        "Waukesha Women's Center": "3AU7L4YQBVOS6",
        "The Guest House of Milwaukee": "183Z20DT40IHB"
    }
    for name, list in wishlists.items():
        data = get_data(list)
        for item in data:
            res.append({
                "shelter": name,
                "item": item['title'],
                "link": f"https://www.amazon.com/dp/{item['id']}",
                "platform": "Amazon",
                "needed": item['needed'],
                "purchased": item['purchased'],
                "comments": item['comments']
            })
    return res
        


if __name__ == "__main__":
    open("test.json", "w").write(
        json.dumps(scrape_all_amazon(), indent=4)
    )