import scrapy
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer
from scrapy.utils.log import configure_logging
import re
from pprint import pprint
import json

class AmazonWishlistSpider(scrapy.Spider):
    BASE_URL = 'https://www.amazon.com'
    name = 'amazonwishlist'
    allowed_domains = ['www.amazon.com']

    def __init__(self, uri, shelter_name, scraped_data, **kwargs):
        self.scraped_data = scraped_data
        self.shelter_name = shelter_name
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
                "shelter": self.shelter_name,
                "item": title.strip() if title else None,
                "link": f"https://www.amazon.com{link.split('/?')[0]}",
                "platform": "Amazon",
                "needed": quantity_needed,
                "purchased": quantity_purchased,
                "comments": comment
            }

            self.scraped_data.append(obj)
            yield obj

        has_next = response.css("a[aria-labelledby='showMoreUrlId']").extract_first()
        if has_next:
            lek_uri = response.css("a[aria-labelledby='showMoreUrlId']::attr(href)").extract_first()
            next_page = self.BASE_URL + lek_uri
            yield scrapy.Request(next_page)

@defer.inlineCallbacks
def scrape_all_amazon():
    configure_logging({'LOG_LEVEL': 'INFO'})
    runner = CrawlerRunner(settings={
        'FEED_FORMAT': 'json',
    })
    
    scraped_data = []
    wishlists = {
        "Waukesha Women's Center": "3AU7L4YQBVOS6",
        "The Guest House of Milwaukee": "183Z20DT40IHB",
        "Cathedral Center": "1IAE55NXCXK5X",
        "Sojourner Truth House": "A8SDOAMS3UNO"
    }

    for name, list_id in wishlists.items():
        url = f"https://www.amazon.com/hz/wishlist/ls/{list_id}"
        yield runner.crawl(AmazonWishlistSpider, url, name, scraped_data)
    
    # Return the results before stopping the reactor
    return scraped_data

def main():
    # Create a deferred to store our final results
    final_results = defer.Deferred()
    
    def write_results(results):
        with open("test.json", "w") as f:
            json.dump(results, f, indent=4)
        return results

    def stop_reactor(results):
        reactor.stop()
        return results

    def handle_error(failure):
        print(f"An error occurred: {failure.value}")
        reactor.stop()

    # Chain our operations
    d = scrape_all_amazon()
    d.addCallback(write_results)
    d.addCallback(stop_reactor)
    d.addErrback(handle_error)
    
    # Start the reactor
    reactor.run()

if __name__ == "__main__":
    main()