#!/usr/bin/env python
import requests
import requests_cache
import helpers
import pandas as pd

def change_column_order(df, col_name, index):
    cols = df.columns.tolist()
    cols.remove(col_name)
    cols.insert(index, col_name)
    return df[cols]

def change_order(df, cols):
    for (idx, col) in enumerate(cols):
        df = change_column_order(df, col, idx)
    return df

frame = helpers.get_table('http://data.ssb.no/api/v0/no/table/04171', 'investments.json')

frame['year'] = frame.kvartal.str.split("K").str.get(0)
frame = frame.groupby(u'year').sum()
frame = frame[frame.index <= "2014"]
frame = frame.drop('kvartal', 1)
frame = frame.drop('investeringsart', 1)

frame.yr = pd.to_numeric(frame.index.values)
frame = frame.groupby((frame.yr - 1985) / 10).sum()
frame['periode'] = ["%d-%d" % (1985 + 10*x, 1985+10*(1+x)-1) for x in frame.index.values]
frame = frame.rename(columns = {u'value': u'letekostnaderMillKr'})

frame = change_order(frame, ['periode', 'letekostnaderMillKr'])

#frame[u'Tid'] = pd.to_datetime(frame[u'kvartal'], format='%YK%m')
#ss = frame.groupby(u'Tid').sum().rolling(window=4).sum()
import ipdb; ipdb.set_trace()



