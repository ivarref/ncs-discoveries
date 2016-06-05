#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import requests_cache
import pandas as pd
import numpy as np
pd.set_option('display.width', 1000)
from StringIO import StringIO
requests_cache.install_cache('cached')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
import pylab
import datetime
#matplotlib.style.use('ggplot')

def keep_fields(frm, to_keep):
    seen_fields = []
    for field in frm.columns:
        if field in to_keep:
            seen_fields.append(field)
            continue
        else:
            frm = frm.drop(field, 1)
    for field in to_keep:
        if field not in seen_fields:
            print "Missing field %s" % (field)
            raise ValueError("Missing field %s" % (field))
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
                                                 u'fldRecoverableOil' : 'recoverableOilMillSm3',
                                                 u'fldRecoverableGas' : 'recoverableGasBillSm3',
                                                 u'fldRecoverableOE' : 'recoverableOeMillSm3'})
fields = [#u'dscName',
    u'nmaName',
    u'name',
    u'dscDiscoveryYear',
    #u'dscNpdidDiscovery',
    #u'fldNpdidField',
    #u'fldName_y',
    u'recoverableOilMillSm3',
    u'recoverableGasBillSm3',
    u'recoverableOeMillSm3',
]

field_reserve = keep_fields(field_reserve, fields)

discovery_resource = get_discovery_resource()
discovery_resource = discovery_resource.rename(columns = { u'dscName' : 'name',
                                                           u'dscRecoverableOil' : 'recoverableOilMillSm3',
                                                           u'dscRecoverableGas' : 'recoverableGasBillSm3',
                                                           u'dscRecoverableOe' : 'recoverableOeMillSm3'})
discovery_resource = keep_fields(discovery_resource, fields)

def change_column_order(df, col_name, index):
    cols = df.columns.tolist()
    cols.remove(col_name)
    cols.insert(index, col_name)
    return df[cols]

def change_order(df, cols):
    for (idx, col) in enumerate(cols):
        df = change_column_order(df, col, idx)
    return df

field_discovery = pd.concat([field_reserve, discovery_resource])
field_discovery = field_discovery.rename(columns = { u'dscDiscoveryYear' : 'discoveryYear',
                         u'nmaName' : 'mainArea'})

cols = [u'name',
        u'mainArea',
        u'discoveryYear',
        u'recoverableOilMillSm3',
        u'recoverableGasBillSm3',
        u'recoverableOeMillSm3',
        ]
field_discovery = change_order(field_discovery, cols)

elephants =  field_discovery[field_discovery.recoverableOeMillSm3 >= 79.0]
elephants = elephants.sort_values(by='discoveryYear', ascending=False)
elephants.to_csv('elephants.tsv', sep='\t', index=False)

field_discovery = field_discovery.sort_values(by='discoveryYear', ascending=False)
field_discovery.to_csv('field_discovery.tsv', sep='\t', index=False)

def petroleum_production():
    url = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/field_production_totalt_NCS_year__DisplayAllRows&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=80.212.17.244&CultureCode=en'
    res = requests.get(url).text[1:].split("\n")
    production = pd.read_csv(StringIO("\n".join(res)))
    columns = [u'prfYear',
               u'prfPrdOilNetMillSm3',
               u'prfPrdGasNetBillSm3',
               u'prfPrdOeNetMillSm3',
               #u'prfPrdCondensateNetMillSm3', #u'prfPrdNGLNetMillSm3', #u'prfPrdProducedWaterInFieldMillSm3'
    ]
    production = keep_fields(production, columns)
    production = production.sort_values(by='prfYear', ascending=True)
    production = production.groupby(by='prfYear').sum().cumsum()
    production['year'] = production.index

    cumulative_discovery = field_discovery.groupby(by='discoveryYear').sum().cumsum()
    cumulative_discovery['year'] = cumulative_discovery.index

    missing_production_years = [year for year in cumulative_discovery.index.values if year not in production.index.values]
    zero_pad = pd.DataFrame(np.zeros((len(missing_production_years), len(production.columns))), columns=production.columns)
    zero_pad.index = missing_production_years
    zero_pad.year = zero_pad.index
    production = zero_pad.append(production)

    missing_disc_years = [year for year in production.index.values if year not in cumulative_discovery.index.values]
    for year in missing_disc_years:
        copy = cumulative_discovery[cumulative_discovery.year == year-1].copy()
        copy.year = year
        copy.index = [year]
        cumulative_discovery = cumulative_discovery.append(copy)
    cumulative_discovery = cumulative_discovery.sort_values(by='year')
    mm = pd.merge(cumulative_discovery, production, on='year')
    cols = [u'year',
            u'prfPrdOilNetMillSm3',
            u'prfPrdGasNetBillSm3',
            u'prfPrdOeNetMillSm3',
            u'recoverableOilMillSm3',
            u'recoverableGasBillSm3',
            u'recoverableOeMillSm3']
    mm = change_order(mm, cols)
    mm.to_csv('cumulative_discovery_produced.tsv', sep='\t')

    #mm = mm[mm.year >= 1996]

    mm['tmp'] = mm.recoverableOilMillSm3 - mm.prfPrdOilNetMillSm3
    mm['tmp'] = (100.0 * mm.tmp) / mm.tmp.max()
    maxyear = mm[mm.tmp == mm.tmp.max()].year.values[0]
    d = 'Gjenverande Olje i bakken. %d=100' % (maxyear)
    mm[d] = mm.tmp

    mm['tmp'] = (mm.recoverableGasBillSm3 - mm.prfPrdGasNetBillSm3)
    mm['tmp'] = (100.0 * mm.tmp) / mm.tmp.max()
    maxyear = mm[mm.tmp == mm.tmp.max()].year.values[0]
    d2 = 'Gjenverande Gass i bakken. %d=100' % (maxyear)
    mm[d2] = mm.tmp

    mm['tmp'] = (mm.recoverableOeMillSm3 - mm.prfPrdOeNetMillSm3)
    mm['tmp'] = (100.0 * mm.tmp) / mm.tmp.max()
    maxyear = mm[mm.tmp == mm.tmp.max()].year.values[0]
    d3 = 'Gjenverande Petroleum i bakken. %d=100' % (maxyear)
    mm[d3] = mm.tmp

    columns = [u'year', d2, d, d3]
    mm = keep_fields(mm, columns)
    for (idx, col) in enumerate([d2, d3, d]):
        mm = change_column_order(mm, col, idx)

    mm.index = mm.year
    mm[u'År'] = pd.to_datetime(mm[u'year'], format='%Y')
    mm.index = mm[u'År']
    mm.index = mm.index.astype(datetime.datetime)
    mm = mm.drop(u'year', 1)
    plot = mm.plot()
    (xmin, xmax, ymin, ymax) = plot.axis()
    ymax = 105
    plot.axis((xmin, xmax, 0, ymax))
    fig = matplotlib.pyplot.gcf()
    ax = fig.axes[0]

    dd = d
    txt = "Olje %4d=%.f" % (mm.index[-1].year, mm[dd].values[-1])
    ax.annotate(txt, (mdates.date2num(mm.index.values[-1]), mm[dd].values[-1]), xytext=(-10, -20), textcoords='offset points', ha='right', va='baseline', arrowprops={"arrowstyle" : '-|>', "mutation_scale":500**.5})

    dd = d2
    txt = "Gass %4d=%.f" % (mm.index[-1].year, mm[dd].values[-1])
    ax.annotate(txt, (mdates.date2num(mm.index.values[-1]), mm[dd].values[-1]), xytext=(-10, 20), textcoords='offset points', ha='right', va='baseline', arrowprops={"arrowstyle" : '-|>', "mutation_scale":500**.5})

    dd = d3
    txt = "Petroleum %4d=%.f" % (mm.index[-1].year, mm[dd].values[-1])
    ax.annotate(txt, (mdates.date2num(mm.index.values[-1]), mm[dd].values[-1]), xytext=(-10, -20), textcoords='offset points', ha='right', va='baseline', arrowprops={"arrowstyle" : '-|>', "mutation_scale":500**.5})

    pylab.savefig('remaining_in_ground.png', bbox_inches='tight')
    #import pylab; pylab.show()


petroleum_production()

