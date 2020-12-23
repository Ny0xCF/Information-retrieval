from saratov24.items import Saratov24Item
import scrapy
from urllib.parse import urljoin


class Saratov24Spider(scrapy.Spider):
    name = "saratov24"
    start_urls = ['https://saratov24.tv/newstags/zhkkh/?page=1']
    visited_urls = []

    def parse_post(self, response):
        item = Saratov24Item()
        item['title'] = response.xpath('//div[@class="article-header"]/h1/text()').extract()
        item['body'] = response.xpath('//div[@class="article-body"]/p[2]/text()').extract()
        item['date'] = response.xpath('//div[@class="article-header"]/span[2]/text()').extract()
        item['url'] = response.url
        yield item

    def parse(self, response):
        if response.url not in self.visited_urls:
            self.visited_urls.append(response.url)
            for post_link in response.xpath('//*[@id="contentTags"]/div/div/a/@href').extract():
                url = urljoin(response.url, post_link)
                yield response.follow(url, callback=self.parse_post)

            next_pages = response.xpath('//li[contains(@class, "page-item") and'
                                        ' not(contains(@class, "active"))]/a/@href').extract()
            next_page = next_pages[-1]

            next_page_url = urljoin(response.url + '/', next_page)
            yield response.follow(next_page_url, callback=self.parse)
