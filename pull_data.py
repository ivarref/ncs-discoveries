#!/usr/bin/python
# -*- coding: utf-8 -*-
from decimal import Decimal
import datetime
import sys
import codecs
import os
from pprint import pprint

# Notes about the generated data:
# Original units is kept, i.e. Mill Sm3 is used for oil, and Bill Sm3 is used for gas.

# Goal:
# Output
# field    discovery_year    produced_oil produced_gas ... etc .. recoverable_oil  recoverable_gas ..etc.. status (producing, shutdown, etc.)

# Discovery -> Table view -> Overview
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

def break_on_duplicates():
  entries = []
  def stop_on_duplicates(elem):
    if elem in entries:
      import sys
      import traceback
      traceback.print_stack()
      print "ERROR. Got duplicate " + str(elem)
      sys.exit(-1)
    entries.append(elem)

  return stop_on_duplicates

def get_url(url, filename):
  import urllib2
  import os

  if not os.path.exists('cache'):
    os.makedirs('cache')

  if not os.path.isfile(filename):
    with codecs.open(filename, encoding='utf-8', mode='w') as fd:
      print "Creating cache %s for %s ..." % (filename, url)
      response = urllib2.urlopen(url)
      fd.write(response.read().decode('utf-8-sig'))
      print "Created cache %s for %s" % (filename, url)
  
  with open(filename, 'r') as fd:
    return fd.read().decode('utf-8')

set_output_encoding()

data = [x.strip() for x in get_url(discoveries_url_csv, 'cache/discoveries.csv').split('\n')]
values = "dscName,cmpLongName,dscCurrentActivityStatus,dscHcType,wlbName,nmaName,fldName,dscDateFromInclInField,dscDiscoveryYear,dscResInclInDiscoveryName,dscOwnerKind,dscOwnerName,dscNpdidDiscovery,fldNpdidField,wlbNpdidWellbore,dscFactPageUrl,dscFactMapUrl,dscDateUpdated,dscDateUpdatedMax,DatesyncNPD"

if values != data[0]:
  print "Csv format has changed. Aborting..."
  print data[0]
  sys.exit(-1)

data = [x.split(",") for x in data[1:] if x.strip() != ""]

(dscName,cmpLongName,dscCurrentActivityStatus,dscHcType,wlbName,nmaName,fldName,dscDateFromInclInField,dscDiscoveryYear,dscResInclInDiscoveryName,dscOwnerKind,dscOwnerName,dscNpdidDiscovery,fldNpdidField,wlbNpdidWellbore,dscFactPageUrl,dscFactMapUrl,dscDateUpdated,dscDateUpdatedMax,DatesyncNPD) = tuple([idx for (idx, x) in enumerate(values.split(","))])


no_duplicates = []
seen_npdids = []

ignore_statuses = """"NEW DISCOVERIES
DEVELOPMENT IS NOT VERY LIKELY
INCLUDED IN OTHER DISCOVERY
""".split("\n")
#PDO APPROVED
#PLANNING PHASE
#DEVELOPMENT LIKELY BUT NOT CLARIFIED
#PRODUCING
#SHUT DOWN

data = [line for line in data if line[dscCurrentActivityStatus] not in ignore_statuses]

for line in data:
  npdid = line[fldNpdidField]
  if npdid == '':
    no_duplicates.append(line)
  elif npdid not in seen_npdids:
    no_duplicates.append(line)
    seen_npdids.append(npdid)
  elif npdid in seen_npdids:
    print "[WARN] Skip duplicate npdid '%s', line '%s'" % (npdid, str(line))

fields = no_duplicates

def verify_and_assign(values, data):
  if data[0] != values:
    print "Failure. Expected %s, but got %s.\nCSV format must have changed!" % (values, data)
    sys.exit(-1)
  return tuple([idx for (idx, x) in enumerate(values.split(","))])

def get_resources_map():
  resources = [x.strip() for x in get_url(resources_url_csv, 'cache/resources.csv').split("\n")]
  values = "dscName,dscReservesRC,dscRecoverableOil,dscRecoverableGas,dscRecoverableNGL,dscRecoverableCondensate,dscDateOffResEstDisplay,dscNpdidDiscovery,dscReservesDateUpdated,DatesyncNPD"
  if resources[0] != values:
    print "CSV format changed."
    sys.exit(-1)
  (dscName,dscReservesRC,dscRecoverableOil,dscRecoverableGas,dscRecoverableNGL,dscRecoverableCondensate,dscDateOffResEstDisplay,dscNpdidDiscovery,dscReservesDateUpdated,DatesyncNPD) = tuple([idx for (idx, x) in enumerate(values.split(","))])
  resources = [x.split(",") for x in resources[1:] if x.strip() != ""]
  resource_map = {}
  for res in resources:
    oil = Decimal(res[dscRecoverableOil])
    gas = Decimal(res[dscRecoverableGas])
    ngl = Decimal(res[dscRecoverableNGL])
    con = Decimal(res[dscRecoverableCondensate])
    oe = oil + gas + ngl + con
    resource_map[res[dscName]] = (oil, gas, oe)
  return resource_map

def npdid_to_reserves():
  reserves_url_csv = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/field_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=84.208.160.74&CultureCode=en'
  reserves = [x.strip() for x in get_url(reserves_url_csv, 'cache/reserves.csv').split("\n") if x.strip() != ""]
  values = "fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD"
  if reserves[0] != values:
    print "CSV format changed."
    sys.exit(-1)
  (fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD) = tuple([idx for (idx, x) in enumerate("fldName,fldRecoverableOil,fldRecoverableGas,fldRecoverableNGL,fldRecoverableCondensate,fldRecoverableOE,fldRemainingOil,fldRemainingGas,fldRemainingNGL,fldRemainingCondensate,fldRemainingOE,fldDateOffResEstDisplay,fldNpdidField,DatesyncNPD".split(","))])
  reserves = [x.split(",") for x in reserves[1:] if x.strip() != ""]
  reserves_map = {}
  for reserve in reserves:
    oil = Decimal(reserve[fldRecoverableOil])
    gas = Decimal(reserve[fldRecoverableGas])
    ngl = Decimal(reserve[fldRecoverableNGL])
    con = Decimal(reserve[fldRecoverableCondensate])
    oe = oil + gas + ngl + con
    reserves_map[reserve[fldNpdidField]] = (oil, gas, oe)
  return reserves_map

rs_map = get_resources_map()
npdid_to_rs = npdid_to_reserves()


result = []

for field in fields:
  npdid = field[fldNpdidField]
  name = field[dscName]
  (oil, gas, oe) = (None, None, None)
  if name in rs_map:
    (oil, gas, oe) = rs_map[name]
  elif npdid in npdid_to_rs:
    (oil, gas, oe) = npdid_to_rs[npdid]
  else:
    print "[WARN] Did not find reserve data for field '%s'" % (name)
  if oil is not None:
    year = field[dscDiscoveryYear]
    status = field[dscCurrentActivityStatus]
    result.append( (int(year), npdid, name, status, oil, gas, oe) )
  
result.sort(key=lambda tup: tup[0])

def npdid_to_production():
  url = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/field_production_monthly&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=84.208.153.159&CultureCode=en'
  production = [x.strip() for x in get_url(url, 'cache/production.csv').split("\n") if x.strip() != ""]
  (prfInformationCarrier,prfYear,prfMonth,prfPrdOilNetMillSm3,prfPrdGasNetBillSm3,prfPrdNGLNetMillSm3,prfPrdCondensateNetMillSm3,prfPrdOeNetMillSm3,prfPrdProducedWaterInFieldMillSm3,prfNpdidInformationCarrier) = verify_and_assign("prfInformationCarrier,prfYear,prfMonth,prfPrdOilNetMillSm3,prfPrdGasNetBillSm3,prfPrdNGLNetMillSm3,prfPrdCondensateNetMillSm3,prfPrdOeNetMillSm3,prfPrdProducedWaterInFieldMillSm3,prfNpdidInformationCarrier", production)
  production = production[1:]
  res = {}
  for line in production:
    line = line.split(",")
    npdid = line[prfNpdidInformationCarrier]
    if npdid not in res:
      res[npdid] = { 'oil' : Decimal(0), 'gas' : Decimal(0), 'oe' : Decimal(0) }
    res[npdid]['oil'] += Decimal(line[prfPrdOilNetMillSm3])
    res[npdid]['gas'] += Decimal(line[prfPrdGasNetBillSm3])
    # TODO add OE
  def lookup(npdid):
    if npdid in res:
      return res[npdid]
    else:
      return { 'oil' : Decimal(0), 'gas' : Decimal(0), 'oe' : Decimal(0) }
  return lookup

# field -> Table view -> Status
def shutdown_date():
  dat = [x.strip() for x in get_url("http://factpages.npd.no/ReportServer?/FactPages/TableView/field_activity_status_hst&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=84.208.153.159&CultureCode=en", "cache/field_tableview_status.csv").split('\n') if x.strip() != '']
  (fldName,fldStatusFromDate,fldStatusToDate,fldStatus,fldNpdidField,fldStatusDateUpdated,datesyncNPD) = verify_and_assign("fldName,fldStatusFromDate,fldStatusToDate,fldStatus,fldNpdidField,fldStatusDateUpdated,datesyncNPD", dat)
  res = {}
  dat = [x.split(",") for x in dat[1:]]
  npdid_to_date = {}

  for line in dat:
    npdid = line[fldNpdidField]
    fromdate = line[fldStatusFromDate].split(".")
    fromdate.reverse()
    fromdate = "-".join(fromdate)
    if npdid not in npdid_to_date:
      npdid_to_date[npdid] = fromdate
    else:
      npdid_to_date[npdid] = max(fromdate, npdid_to_date[npdid])

  for line in dat:
    npdid = line[fldNpdidField]
    status = line[fldStatus]
    fromdate = line[fldStatusFromDate].split(".")
    fromdate.reverse()
    fromdate = "-".join(fromdate)
    if fromdate == npdid_to_date[npdid] and status == 'SHUT DOWN':
      print line[fldName]
    
  def lookup_shutdown(npdid):
    if npdid in res:
      return res[npdid]
    else:
      return None
  return lookup_shutdown


npdid_to_prod = npdid_to_production()

#print shutdown_date()('43437')
#print "woooho"

if not os.path.exists('data'):
  os.makedirs('data')
with codecs.open('data/data.tsv', encoding='utf-8', mode='w') as fd:
  fd.write('field discovery_year status recoverable_oil recoverable_gas recoverable_oe produced_oil produced_gas\n'.replace(' ', '\t'))
  for (year, npdid, name, status, oil, gas, oe) in result:
    produced = npdid_to_prod(npdid)
    produced_oil = "%.2f" % (produced['oil'])
    produced_gas = "%.2f" % (produced['gas'])
    fd.write("\t".join([name, str(year), status, str(oil), str(gas), str(oe), produced_oil, produced_gas] ))
    fd.write("\n")

with codecs.open('data/produced.csv', encoding='utf-8', mode='w') as fd:
  data = [x.strip() for x in get_url('http://factpages.npd.no/ReportServer?/FactPages/TableView/field_production_totalt_NCS_year__DisplayAllRows&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=84.208.153.159&CultureCode=en', 'cache/yearly_produced_total.csv').split('\n') if x.strip() != '']
  (prfYear,prfPrdOilNetMillSm,prfPrdGasNetBillSm,prfPrdCondensateNetMillSm3,prfPrdNGLNetMillSm3,prfPrdOeNetMillSm3,prfPrdProducedWaterInFieldMillSm3) = verify_and_assign("prfYear,prfPrdOilNetMillSm,prfPrdGasNetBillSm,prfPrdCondensateNetMillSm3,prfPrdNGLNetMillSm3,prfPrdOeNetMillSm3,prfPrdProducedWaterInFieldMillSm3", data)
  fd.write("\n".join(data))

