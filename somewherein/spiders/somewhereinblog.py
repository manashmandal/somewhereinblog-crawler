import scrapy
from scrapy.exceptions import CloseSpider
from pprint import pprint
import dateparser
import json
from datetime import timedelta


class SomewhereinblogSpider(scrapy.Spider):
    name = "somewhereinblog"
    # allowed_domains = ["somwehreinblog.net"]
    # start_urls = ["https://somwehreinblog.net/"]

    def __init__(self, start_date="2019/11/01", end_date="2017/01/03", *args, **kwargs):
        print("kwargs", kwargs)
        self.date_format = "%Y/%m/%d"
        self.start_date = dateparser.parse(start_date)
        self.end_date = dateparser.parse(end_date)
        self.current_date = self.start_date
        self.base_url = "https://www.somewhereinblog.net/blog/archive/{date}/{page}"
        self.site_url = "https://www.somewhereinblog.net"
        self.current_url = self.base_url.format(
            date=self.current_date.strftime(self.date_format), page=0
        )
        self.selectors = {
            "all_posts": '//*[@id="posts"]//div/h2/a/@href',
            "blog_content": "//div[@class='single-full-post']/div[@class='blog-content']//text()",
            "published_at": "//div[@class='single-full-post']/div[@class='author']/text()",
            "title": "//div[@class='single-full-post']/h2//text()",
            "raw_title": "//div[@class='single-full-post']/h2",
            "post_images": "//div[@class='blog-content']//img[@class='post_image']/@src",
        }
        self.page_size = 15

    def parse_post_title(self, response):
        return {
            "title": response.xpath(self.selectors["title"]).extract_first(),
            "raw_title": response.xpath(self.selectors["raw_title"]).extract_first(),
        }

    def parse_post_image_urls(self, response):
        *_, nick, post_id = response.url.split("/")
        return [
            imgurl
            for imgurl in response.xpath(self.selectors["post_images"]).extract()
            if nick in imgurl
        ]

    def parse_post_content(self, response):
        return "".join(response.xpath(self.selectors["blog_content"]).extract())

    def iterate_posts(self, response):
        for url in self.get_all_posts(response):
            yield scrapy.Request(url, callback=self.parse_post)

    def parse_published_at(self, response):
        published_at_raw = response.xpath(
            self.selectors["published_at"]
        ).extract_first()
        day, _, month, year = published_at_raw.split()[:-2]
        parsable_date = " ".join([day, month, year])
        published_at = dateparser.parse(parsable_date)
        return dict(published_at_raw=published_at_raw, published_at=published_at)

    def parse_post_meta(self, response):
        *_, nick, post_id = response.url.split("/")
        return dict(nick=nick, post_id=post_id)

    def get_all_posts(self, response):
        return [
            self.site_url + a
            for a in response.xpath(self.selectors["all_posts"]).extract()
        ]

    def next_date(self):
        self.current_date += timedelta(days=1)
        self.current_url = self.base_url.format(
            date=self.current_date.strftime(self.date_format), page=0
        )

    def current_date_next_page(self, response):
        for url in self.get_all_posts(response):
            yield scrapy.Request(url, callback=self.parse_post)
        print("CURRENT DATE NEXT PAGE ", response.url)
        *_, year, month, day, current_page = response.url.split("/")
        current_page = int(current_page)
        posts_count = len(response.xpath(self.selectors["all_posts"]).extract())
        if posts_count == 0:
            return
        else:
            next_page = current_page + self.page_size
            date = f"{year}/{month}/{day}"
            next_url = self.base_url.format(date=date, page=next_page)
            yield scrapy.Request(
                next_url, callback=self.current_date_next_page, dont_filter=True
            )

        # if (current_page == 0 and response)

    def check(self):
        if self.current_date > self.end_date:
            raise CloseSpider(f"{self.current_date} > {self.end_date}")

    def start_requests(self):
        yield scrapy.Request(self.current_url, callback=self.parse)

    def parse_post(self, response):
        item = dict(
            content=self.parse_post_content(response),
            post_url=response.url,
            post_image_urls=self.parse_post_image_urls(response),
            **self.parse_post_title(response),
            **self.parse_published_at(response),
            **self.parse_post_meta(response),
        )

        yield item

    def parse(self, response):
        yield scrapy.Request(
            self.current_url, callback=self.current_date_next_page, dont_filter=True
        )
        self.next_date()
        yield scrapy.Request(self.current_url, callback=self.parse, dont_filter=True)
