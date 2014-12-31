#!/usr/bin/python
# -*- coding: utf-8 -*-
from decimal import Decimal
import datetime
import sys
import codecs
from pprint import pprint

# Goal:
# Output
# field    discovery_year    produced_oil produced_gas ... etc .. recoverable_oil  recoverable_gas ..etc.. status (producing, shutdown, etc.)

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

data = [x.split(",") for x in data[1:] if x.strip() != ""]

(dscName,cmpLongName,dscCurrentActivityStatus,dscHcType,wlbName,nmaName,fldName,dscDateFromInclInField,dscDiscoveryYear,dscResInclInDiscoveryName,dscOwnerKind,dscOwnerName,dscNpdidDiscovery,fldNpdidField,wlbNpdidWellbore,dscFactPageUrl,dscFactMapUrl,dscDateUpdated,dscDateUpdatedMax,DatesyncNPD) = tuple([idx for (idx, x) in enumerate(values.split(","))])

#PDO APPROVED
#PLANNING PHASE
#DEVELOPMENT LIKELY BUT NOT CLARIFIED
#PRODUCING
#SHUT DOWN

ignore_statuses = """"NEW DISCOVERIES
DEVELOPMENT IS NOT VERY LIKELY
INCLUDED IN OTHER DISCOVERY
""".split("\n")

fields = [line for line in data if line[dscCurrentActivityStatus] not in ignore_statuses]

def get_resources_map():
  resources = [x.strip() for x in get_url(resources_url_csv).split("\n")]
  values = "dscName,dscReservesRC,dscRecoverableOil,dscRecoverableGas,dscRecoverableNGL,dscRecoverableCondensate,dscDateOffResEstDisplay,dscNpdidDiscovery,dscReservesDateUpdated,DatesyncNPD"
  if resources[0] != values:
    print "CSV format changed."
    sys.exit(-1)
  (dscName,dscReservesRC,dscRecoverableOil,dscRecoverableGas,dscRecoverableNGL,dscRecoverableCondensate,dscDateOffResEstDisplay,dscNpdidDiscovery,dscReservesDateUpdated,DatesyncNPD) = tuple([idx for (idx, x) in enumerate(values.split(","))])
  resources = [x.split(",") for x in resources[1:] if x.strip() != ""]
  resource_map = {}
  for res in resources:
    resource_map[res[dscName]] = (Decimal(res[dscRecoverableOil]), Decimal(res[dscRecoverableGas]))
  return resource_map

def npdid_to_reserves():
  reserves_url_csv = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/field_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=84.208.160.74&CultureCode=en'
  reserves = [x.strip() for x in get_url(reserves_url_csv).split("\n") if x.strip() != ""]
  values = "fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD"
  if reserves[0] != values:
    print "CSV format changed."
    sys.exit(-1)
  (fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD) = tuple([idx for (idx, x) in enumerate("fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD".split(","))])
  reserves = [x.split(",") for x in reserves[1:] if x.strip() != ""]
  reserves_map = {}
  for reserve in reserves:
    reserves_map[reserve[fldNpdidField]] = (Decimal(reserve[fldRecoverableOil]), Decimal(reserve[fldRecoverableGas]))
  return reserves_map

rs_map = get_resources_map()
npdid_to_rs = npdid_to_reserves()

result = []

for field in fields:
  npdid = field[fldNpdidField]
  name = field[dscName]
  (oil, gas) = (None, None)
  if name in rs_map:
    (oil, gas) = rs_map[name]
  elif npdid in npdid_to_rs:
    (oil, gas) = npdid_to_rs[npdid]
  else:
    print "[WARN] did not reserve data for field '%s'" % (name)
  if oil is not None:
    year = field[dscDiscoveryYear]
    status = field[dscCurrentActivityStatus]
    result.append( (int(year), name, status, oil, gas) )
  
result.sort(key=lambda tup: tup[0])

def reserves_sum(res):
  oil_total = Decimal(0)
  gas_total = Decimal(0)
  for (year, name, status, oil, gas) in res:
    oil_total += oil
    gas_total += gas
  return (oil_total, gas_total)

laterthan2000 = []
for (year, name, status, oil, gas) in result:
  if status in ['PRODUCING', 'SHUT DOWN'] or year < 2000:
    continue
  laterthan2000.append((year, name, status,oil,gas))

#print reserves_sum(laterthan2000)
#print reserves_sum(result)

with codecs.open('data/data.tsv', encoding='utf-8', mode='w') as fd:
  fd.write('field discovery_year recoverable_oil recoverable_gas\n'.replace(' ', '\t'))
  for (year, name, status, oil, gas) in result:
    fd.write("\t".join([name, str(year), str(oil), str(gas)]))
    fd.write("\n")


