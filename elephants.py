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

def change_column_order(df, col_name, index):
    cols = df.columns.tolist()
    cols.remove(col_name)
    cols.insert(index, col_name)
    return df[cols]

def change_order(df, cols):
    for (idx, col) in enumerate(cols):
        df = change_column_order(df, col, idx)
    return df

def all_field_discovery():
    # factpages: Discovery -> Table View -> Overview
    url = 'http://factpages.npd.no/ReportServer?/FactPages/TableView/discovery&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=80.212.17.244&CultureCode=en'
    res = requests.get(url).text[1:].split("\n")
    #res = res[0:3]
    frame = pd.read_csv(StringIO("\n".join(res)))
    frame = frame[pd.isnull(frame.dscResInclInDiscoveryName)] # Remove fields which is included in other field
    frame = keep_fields(frame, [u'dscName',
                                u'dscCurrentActivityStatus',
                                u'nmaName',
                                u'fldName',
                                u'dscDiscoveryYear',
                                u'dscNpdidDiscovery',
                                u'fldNpdidField'
    ])
    # As of 2016-05-04, this produces 337 rows
    # frame[pd.notnull(frame.fldNpdidField)] => 108 rows
    # frame[pd.isnull(frame.fldNpdidField)] # => 229 rows
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
    return pd.merge(fields, reserves, on='fldNpdidField')

field_reserve = get_field_reserve()
field_reserve = field_reserve.rename(columns = {
    u'fldName_x': 'name',
    u'dscCurrentActivityStatus' : u'status',
    u'dscDiscoveryYear' : u'discoveryYear',
    u'nmaName' : u'mainArea',
    u'fldRecoverableOil' : 'recoverableOilMillSm3',
    u'fldRecoverableGas' : 'recoverableGasBillSm3',
    u'fldRecoverableOE' : 'recoverableOeMillSm3'})

cols = [u'name',
        u'discoveryYear',
        u'mainArea',
        u'status',
        u'recoverableOilMillSm3',
        u'recoverableGasBillSm3',
        u'recoverableOeMillSm3']

field_reserve = change_order(keep_fields(field_reserve, cols), cols)
field_reserve = field_reserve.sort_values(by='discoveryYear', ascending=True)

field_reserve.to_csv('field_reserve.tsv', sep='\t', index=False)

field_reserve[field_reserve.status == u'PDO APPROVED'].to_csv('pdo_approved.tsv', sep='\t', index=False)
field_reserve[field_reserve.recoverableOeMillSm3 >= 79.0].to_csv('elephants.tsv', sep='\t', index=False)

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

    cumulative_discovery = field_reserve.groupby(by='discoveryYear').sum().cumsum()
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
    mm.to_csv('cumulative_discovery_produced.tsv', sep='\t', index=False)

    remaining_in_ground = mm.copy()
    remaining_in_ground['remainingOilMillSm3'] = remaining_in_ground.recoverableOilMillSm3 - remaining_in_ground.prfPrdOilNetMillSm3
    remaining_in_ground['remainingGasBillSm3'] = remaining_in_ground.recoverableGasBillSm3 - remaining_in_ground.prfPrdGasNetBillSm3
    remaining_in_ground['remainingOeMillSm3'] = remaining_in_ground.recoverableOeMillSm3 - remaining_in_ground.prfPrdOeNetMillSm3
    remaining_in_ground = keep_fields(remaining_in_ground, ['year', 'remainingOilMillSm3', 'remainingGasBillSm3', 'remainingOeMillSm3'])
    remaining_in_ground.to_csv('remaining_in_ground.tsv', sep='\t', index=False)


    def write_diagram(filename, mm, relativevalue):
        mm['tmp'] = mm.recoverableOilMillSm3 - mm.prfPrdOilNetMillSm3
        mm['tmp'] = (100.0 * mm.tmp) / relativevalue(mm)
        maxyear = mm[mm.tmp == relativevalue(mm)].year.values[0]
        d = 'Gjenverande Olje i bakken. %d=100' % (maxyear)
        mm[d] = mm.tmp

        mm['tmp'] = (mm.recoverableGasBillSm3 - mm.prfPrdGasNetBillSm3)
        mm['tmp'] = (100.0 * mm.tmp) / relativevalue(mm)
        maxyear = mm[mm.tmp == relativevalue(mm)].year.values[0]
        d2 = 'Gjenverande Gass i bakken. %d=100' % (maxyear)
        mm[d2] = mm.tmp

        mm['tmp'] = (mm.recoverableOeMillSm3 - mm.prfPrdOeNetMillSm3)
        mm['tmp'] = (100.0 * mm.tmp) / relativevalue(mm)
        maxyear = mm[mm.tmp == relativevalue(mm)].year.values[0]
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
        ymax = ymax+5
        plot.axis((xmin, xmax, 0, ymax))
        fig = matplotlib.pyplot.gcf()
        ax = fig.axes[0]

        dd = d
        txt = "Olje %4d=%.f" % (mm.index[-1].year, mm[dd].values[-1])
        ax.annotate(txt, (mdates.date2num(mm.index.values[-1]), mm[dd].values[-1]), xytext=(-10, -20), textcoords='offset points', ha='right', va='baseline', arrowprops={"arrowstyle" : '-|>', "mutation_scale":500**.5})

        dd = d2
        txt = "Gass %4d=%.f" % (mm.index[-1].year, mm[dd].values[-1])
        ax.annotate(txt, (mdates.date2num(mm.index.values[-1]), mm[dd].values[-1]), xytext=(-10, -20), textcoords='offset points', ha='right', va='baseline', arrowprops={"arrowstyle" : '-|>', "mutation_scale":500**.5})

        dd = d3
        txt = "Petroleum %4d=%.f" % (mm.index[-1].year, mm[dd].values[-1])
        ax.annotate(txt, (mdates.date2num(mm.index.values[-1]), mm[dd].values[-1]), xytext=(-10, -20), textcoords='offset points', ha='right', va='baseline', arrowprops={"arrowstyle" : '-|>', "mutation_scale":500**.5})
        pylab.savefig(filename, bbox_inches='tight')
    #import pylab; pylab.show()

    write_diagram('remaining_in_ground.png', mm.copy(), lambda x: x.tmp.max())
    since = mm.copy(); since = since[since.year >= 1996]
    write_diagram('remaining_in_ground_since_1996.png', since, lambda x: x.tmp.values[0])
    since = mm.copy(); since = since[since.year >= 2006]
    write_diagram('remaining_in_ground_since_2006.png', since, lambda x: x.tmp.values[0])
    since = mm.copy(); since = since[since.year >= 1985]
    write_diagram('remaining_in_ground_since_1985.png', since, lambda x: x.tmp.values[0])

petroleum_production()

