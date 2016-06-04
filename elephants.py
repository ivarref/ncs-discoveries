#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import requests_cache
import pandas as pd
pd.set_option('display.width', 1000)
from StringIO import StringIO
requests_cache.install_cache('cached')


def keep_fields(frm, to_keep):
    seen_fields = []
    for field in frm.columns:
        if field in to_keep:
            continue
        else:
            frm = frm.drop(field, 1)
    return frm

def all_field_discovery():
    # factpages: Discovery -> Table View -> Overview
    url = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/discovery&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=80.212.17.244&CultureCode=en'
    res = requests.get(url).text[1:].split("\n")
    #res = res[0:3]
    frame = pd.read_csv(StringIO("\n".join(res)))
    frame = frame[pd.isnull(frame.dscResInclInDiscoveryName)] # Remove fields which is included in other field
    frame = keep_fields(frame, [u'dscName',
                                #u'dscCurrentActivityStatus',
                                u'nmaName',
                                u'fldName',
                                u'dscDiscoveryYear',
                                u'dscNpdidDiscovery',
                                u'fldNpdidField'
    ])
    # As of 2016-05-04, this produces 337 rows
    # frame[pd.notnull(frame.fldNpdidField)] => 108 rows
    # frame[pd.isnull(frame.fldNpdidField)] # => 229 rows
    #import ipdb; ipdb.set_trace()
    return frame

def get_field_reserve():
    frame = all_field_discovery()
    #frame = frame.drop_duplicates('fldNpdidField')
    fields = frame[pd.notnull(frame.fldNpdidField)]
    fields = fields.drop_duplicates('fldNpdidField')

    # Field -> Table view -> Reserves
    field_reserves_url = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/field_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=80.212.17.244&CultureCode=en'
    res = requests.get(field_reserves_url).text[1:].split('\n') # So this is 109 rows
    #res = res[0:3]
    reserves = pd.read_csv(StringIO("\n".join(res)))
    #fldName  fldRecoverableOil  fldRecoverableGas  fldRecoverableNGL  fldRecoverableCondensate  fldRecoverableOE  fldRemainingOil  fldRemainingGas  fldRemainingNGL  fldRemainingCondensate  fldRemainingOE fldDateOffResEstDisplay  fldNpdidField DatesyncNPD
    reserves = keep_fields(reserves, [u'fldName',
                                      u'fldRecoverableOil',
                                      u'fldRecoverableGas',
                                      u'fldRecoverableOE',
                                      u'fldNpdidField'])
    field_reserve = pd.merge(fields, reserves, on='fldNpdidField')
    return field_reserve

def get_discovery_resource():
    # Discovery -> Table view -> Resources
    resources_url = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/discovery_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=80.212.17.244&CultureCode=en'
    res = requests.get(resources_url).text[1:].split('\n')
    #res = [res[0], res[-3], res[-4]]
    resources = pd.read_csv(StringIO("\n".join(res)))
    # [u'dscName', u'dscReservesRC', u'dscRecoverableOil', u'dscRecoverableGas', u'dscRecoverableNGL', u'dscRecoverableCondensate', u'dscRecoverableOe', u'dscDateOffResEstDisplay', u'dscNpdidDiscovery', u'dscReservesDateUpdated', u'DatesyncNPD']
    resources = keep_fields(resources, [u'dscName',
                                        u'dscRecoverableOil',
                                        u'dscRecoverableGas',
                                        u'dscRecoverableOe',
                                        u'dscNpdidDiscovery'])
    grouped = resources.groupby(by='dscNpdidDiscovery', as_index=False).sum()
    return pd.merge(all_field_discovery(), grouped, on='dscNpdidDiscovery') # => 90 discoveries with resource estimates
    # 139 non-fields without resource estimates
    # I've manually verified that this is correct for Pingvin, Desmond, Atlantis, Zulu Øst, etc.
    # nonfields = frame[pd.isnull(frame.fldNpdidField)]
    # no_resource_estimates = [npdid for npdid in nonfields.dscNpdidDiscovery.values if npdid not in m.dscNpdidDiscovery.values]
    # print "Number of discoveries with no resources estimates: %d" % (len(no_resource_estimates))
    # for npdid in no_resource_estimates:
        #print "Missing resource estimate for discovery: %s" % (nonfields[nonfields.dscNpdidDiscovery == npdid].dscName.values[0])

field_reserve = get_field_reserve()
field_reserve = field_reserve.rename(columns = { u'fldName_x': 'name',
                                                 u'fldRecoverableOil' : 'recoverableOil',
                                                 u'fldRecoverableGas' : 'recoverableGas',
                                                 u'fldRecoverableOE' : 'recoverableOe'})
fields = [#u'dscName',
    u'nmaName',
    u'name',
    u'dscDiscoveryYear',
    #u'dscNpdidDiscovery',
    #u'fldNpdidField',
    #u'fldName_y',
    u'recoverableOil',
    u'recoverableGas',
    u'recoverableOe',
]

field_reserve = keep_fields(field_reserve, fields)

discovery_resource = get_discovery_resource()
discovery_resource = discovery_resource.rename(columns = { u'dscName' : 'name',
                                                           u'dscRecoverableOil' : 'recoverableOil',
                                                           u'dscRecoverableGas' : 'recoverableGas',
                                                           u'dscRecoverableOe' : 'recoverableOe'})
discovery_resource = keep_fields(discovery_resource, fields)

def change_column_order(df, col_name, index):
    cols = df.columns.tolist()
    cols.remove(col_name)
    cols.insert(index, col_name)
    return df[cols]

m = pd.concat([field_reserve, discovery_resource])
m = m.rename(columns = { u'dscDiscoveryYear' : 'discoveryYear',
                         u'nmaName' : 'mainArea'})
cols = [u'name',
        u'mainArea',
        u'discoveryYear',
        u'recoverableOil',
        u'recoverableGas',
        u'recoverableOe',
        ]

for (idx, col) in enumerate(cols):
    m = change_column_order(m, col, idx)

elephants =  m[m.recoverableOe >= 79.0]
print elephants.sort_values(by='discoveryYear', ascending=False)

#import ipdb; ipdb.set_trace()

