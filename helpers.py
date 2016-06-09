#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyjstat import pyjstat
import requests
#import requests_cache
from collections import OrderedDict
import codecs
import json

#requests_cache.install_cache('cache')

def get_table(url, payload):
    with codecs.open(payload, 'r', encoding='utf-8') as ff:
        payload = json.loads(ff.read())
        data = requests.post(url, json = payload)
        result = pyjstat.from_json_stat(data.json(object_pairs_hook=OrderedDict))
        frame = result[0]
        return frame
