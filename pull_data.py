#!/usr/bin/python
# -*- coding: utf-8 -*-
from decimal import Decimal
import datetime
import sys
import codecs
from pprint import pprint

# Goal: Show an overview of discoveries on the NCS. 
# Include all types of discoveries: 
# Producing (e.g. EKOFISK), 
# Shut down (COD), 
# PDO approved (HANZ, FLYNDRE)
# Planning Phase (Johan Castberg)
#
# Grouped by e.g. discovery decade?



discoveries_url_csv = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/discovery&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=2.150.32.28&CultureCode=en'

resources_url_csv = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/discovery_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=2.150.32.28&CultureCode=en'

def set_output_encoding(encoding='utf-8'):
  import sys
  import codecs
  '''When piping to the terminal, python knows the encoding needed, and
     sets it automatically. But when piping to another program (for example,
     | less), python can not check the output encoding. In that case, it 
     is None. What I am doing here is to catch this situation for both 
     stdout and stderr and force the encoding'''
  current = sys.stdout.encoding
  if current is None :
    sys.stdout = codecs.getwriter(encoding)(sys.stdout)
  current = sys.stderr.encoding
  if current is None :
    sys.stderr = codecs.getwriter(encoding)(sys.stderr)

def get_url(url):
  import urllib2
  import hashlib
  import os

  m = hashlib.md5()
  m.update(url)
  md5 = m.hexdigest()
  cache = 'cache/' + md5
  if not os.path.exists('cache'):
    os.makedirs('cache')

  if not os.path.isfile(cache):
    with codecs.open(cache, encoding='utf-8', mode='w') as fd:
      print "Creating cache %s for %s ..." % (cache, url)
      response = urllib2.urlopen(url)
      fd.write(response.read().decode('utf-8-sig'))
      print "Created cache %s for %s" % (cache, url)
  
  with open(cache, 'r') as fd:
    return fd.read().decode('utf-8')

set_output_encoding()

data = [x.strip() for x in get_url(discoveries_url_csv).split('\n')]
values = "dscName,cmpLongName,dscCurrentActivityStatus,dscHcType,wlbName,nmaName,fldName,dscDateFromInclInField,dscDiscoveryYear,dscResInclInDiscoveryName,dscOwnerKind,dscOwnerName,dscNpdidDiscovery,fldNpdidField,wlbNpdidWellbore,dscFactPageUrl,dscFactMapUrl,dscDateUpdated,dscDateUpdatedMax,DatesyncNPD"

if values != data[0]:
  print "Csv format has changed. Aborting..."
  print data[0]
  sys.exit(-1)

data = data[1:]
data = [x for x in data if x.strip() != ""]

(dscName,cmpLongName,dscCurrentActivityStatus,dscHcType,wlbName,nmaName,fldName,dscDateFromInclInField,dscDiscoveryYear,dscResInclInDiscoveryName,dscOwnerKind,dscOwnerName,dscNpdidDiscovery,fldNpdidField,wlbNpdidWellbore,dscFactPageUrl,dscFactMapUrl,dscDateUpdated,dscDateUpdatedMax,DatesyncNPD) = tuple([idx for (idx, x) in enumerate(values.split(","))])

data = [x.split(",") for x in data]

# Goal: Get reserves of fields to come on stream / could come on stream

#DEVELOPMENT LIKELY BUT NOT CLARIFIED
#PDO APPROVED
#PLANNING PHASE

ignore_statuses = """"NEW DISCOVERIES
DEVELOPMENT IS NOT VERY LIKELY
INCLUDED IN OTHER DISCOVERY
PRODUCING
SHUT DOWN""".split("\n")

fields = [line for line in data if line[dscCurrentActivityStatus] not in ignore_statuses]

def get_reserves_by_field_npdid(npdid):
  reserves_url_csv = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/field_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=84.208.160.74&CultureCode=en'
  reserves = [x.strip() for x in get_url(reserves_url_csv).split("\n") if x.strip() != ""]
  values = "fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD"
  if reserves[0] != values:
    print "CSV format changed."
    sys.exit(-1)
  (fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD) = tuple([idx for (idx, x) in enumerate("fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD".split(","))])
  reserves = [x.split(",") for x in reserves[1:]]
  res = [x[fldRecoverableOil] for x in reserves if x[fldNpdidField] == npdid]
  if len(res)>1:
    print "Bad data..."
    sys.exit(-1)
  return res
  
def get_resources_map():
  resources = [x.strip() for x in get_url(resources_url_csv).split("\n")]
  values = "dscName,dscReservesRC,dscRecoverableOil,dscRecoverableGas,dscRecoverableNGL,dscRecoverableCondensate,dscDateOffResEstDisplay,dscNpdidDiscovery,dscReservesDateUpdated,DatesyncNPD"
  if resources[0] != values:
    print "CSV format changed."
    sys.exit(-1)
  (dscName,dscReservesRC,dscRecoverableOil,dscRecoverableGas,dscRecoverableNGL,dscRecoverableCondensate,dscDateOffResEstDisplay,dscNpdidDiscovery,dscReservesDateUpdated,DatesyncNPD) = tuple([idx for (idx, x) in enumerate(values.split(","))])
  resources = resources[1:]
  resources = [x.split(",") for x in resources if x.strip() != ""]
  resource_map = {}
  for res in resources:
    resource_map[res[dscName]] = res[dscRecoverableOil]
  return resource_map
  
res_map = get_resources_map()

found_count = 0
rem = Decimal(0)
ok_fields = []
for f in fields:
  if f[dscName] not in res_map:
    if len(get_reserves_by_field_npdid(f[fldNpdidField])) == 0:
      sys.stderr.write("Warning: missing %s with npdid %s and status %s" % (f[dscName], f[fldNpdidField], f[dscCurrentActivityStatus]))
      sys.stderr.write("\n")
    else:
      rem += Decimal(get_reserves_by_field_npdid(f[fldNpdidField])[0])
      res_map[f[dscName]] = (get_reserves_by_field_npdid(f[fldNpdidField])[0])
      found_count += 1
      ok_fields.append(f)
  else:
    rem += Decimal(res_map[f[dscName]])
    found_count += 1
    ok_fields.append(f)

#print "And found: %d" % (found_count)
print "And remaining in Gb: %.02f" % ((Decimal(6.29) * rem) / Decimal(1000.0))

for f in ok_fields:
  print "%s => %s" % (res_map[f[dscName]], f[dscName])

