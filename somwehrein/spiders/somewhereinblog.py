import scrapy
from scrapy.exceptions import CloseSpider
from pprint import pprint
import dateparser
import json


class SomewhereinblogSpider(scrapy.Spider):
    name = "somewhereinblog"
    # allowed_domains = ["somwehreinblog.net"]
    # start_urls = ["https://somwehreinblog.net/"]

    def __init__(self, start_page=99 * 1000, end_page=100 * 1000, *args, **kwargs):
        print("kwargs", kwargs)
        self.start_page = int(kwargs.get("start_page", start_page))
        self.end_page = int(kwargs.get("end_page", end_page))
        self.current_page_no = self.start_page
        self.base_url = "https://www.somewhereinblog.net/live/{page}"
        self.site_url = "https://www.somewhereinblog.net"
        self.current_url = self.base_url.format(page=self.current_page_no)
        self.selectors = {
            "all_posts": '//*[@id="posts"]//div/h2/a/@href',
            "blog_content": "//div[@class='single-full-post']/div[@class='blog-content']//text()",
            "published_at": "//div[@class='single-full-post']/div[@class='author']/text()",
            "title": "//div[@class='single-full-post']/h2/text()",
        }

    def parse_post_title(self, response):
        return response.xpath(self.selectors["title"]).extract_first()

    def parse_post_content(self, response):
        return "".join(response.xpath(self.selectors["blog_content"]).extract())

    def parse_published_at(self, response):
        published_at_raw = response.xpath(
            self.selectors["published_at"]
        ).extract_first()
        published_at = dateparser.parse(" ".join(published_at_raw.split()[:-2]))
        return dict(published_at_raw=published_at_raw, published_at=str(published_at))

    def parse_post_meta(self, response):
        *_, nick, post_id = response.url.split("/")
        return dict(nick=nick, post_id=post_id)

    def get_all_posts(self, response):
        return [
            self.site_url + a
            for a in response.xpath(self.selectors["all_posts"]).extract()
        ]

    def next_page(self):
        self.current_page_no += 1
        self.current_url = self.site_url.format(page=self.current_page_no)

    def check(self):
        if self.current_page_no > self.end_page:
            raise CloseSpider(f"{self.current_page_no} > {self.end_page}")

    def start_requests(self):
        yield scrapy.Request(self.current_url, callback=self.parse)

    def parse_post(self, response):
        # print(response.url)

        data = dict(
            title=self.parse_post_title(response),
            content=self.parse_post_content(response),
            post_url=response.url,
            **self.parse_published_at(response),
            **self.parse_post_meta(response),
        )

        with open(f"./crawled_items/{data['post_id']}.json", "w") as writefile:
            json.dump(data, writefile, ensure_ascii=False)

        # print("DATA", data)

    def parse(self, response):
        # print(response.url)
        for url in self.get_all_posts(response):
            print(url)
            yield scrapy.Request(url, callback=self.parse_post)
        self.next_page()
        self.check()
        # yield scrapy.Request(self.current_url, callback=self.parse)
