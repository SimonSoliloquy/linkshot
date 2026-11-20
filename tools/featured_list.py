#!/usr/bin/env python3
"""Write featured.json: every article listed on https://en.wikipedia.org/wiki/Wikipedia:Featured_articles.

Random games start from one of these. Rerun now and then to pick up newly promoted articles.
usage: python3 tools/featured_list.py
"""
import json, os, urllib.parse, urllib.request

API = 'https://en.wikipedia.org/w/api.php'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'featured.json')


def get(params):
    url = API + '?' + urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})
    req = urllib.request.Request(url, headers={'User-Agent': 'LinkshotFeaturedList/1.0 (https://simonsoliloquy.com/linkshot/) python-urllib'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


links = get({'action': 'parse', 'page': 'Wikipedia:Featured articles', 'prop': 'links'})['parse']['links']
titles = sorted({l['title'] for l in links if l.get('ns') == 0 and l.get('exists')})
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(titles, f, ensure_ascii=False, separators=(',', ':'))
print(len(titles), 'featured articles ->', os.path.normpath(OUT))
