#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import requests_cache
import pandas as pd
from StringIO import StringIO
from lxml import etree

requests_cache.install_cache('cached')

url = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/discovery&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=80.212.17.244&CultureCode=en'
res = requests.get(url).text[1:].split("\n")
frame = pd.read_csv(StringIO("\n".join(res)))

statuses = []

for npdid in set(frame.dscNpdidDiscovery.values):
    url = 'http://factpages.npd.no/ReportServer?/FactPages/PageView/discovery&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&NpdId=%d&ChapterExpand=All&IpAddress=80.213.254.210&CultureCode=en' % (npdid)
    resp = requests.get(url)
    tree = etree.parse(StringIO(resp.text), etree.HTMLParser())
    root = tree.getroot()
    div = root.xpath('.//div[text()="Current activity status"]')[0]
    status = div.getparent().getparent().getchildren()[-1].getchildren()[0].text
    statuses.append(status)
    print "%d => %s" % (npdid, status)

print str(set(statuses))

