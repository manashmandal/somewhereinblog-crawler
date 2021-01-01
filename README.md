# [Somewherein Blog](https://somewhereinblog.net) Crawler

## Environment Setup

```sh
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run Spider

Make sure mongo is either installed on your pc or have access to one. Then just edit the access in `settings.py` file.

```sh
scrapy crawl somewhereinblog -a start_date="2017-01-01"
```

## Deployment in Docker [Coming soon....]
