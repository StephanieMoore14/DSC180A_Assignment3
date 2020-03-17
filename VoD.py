from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats
import pandas as pd
import numpy as np
import datetime
import urllib
import json
import os

import pathlib


from etl import get_data
cs = pd.read_csv('data/census_data/sd_pop.csv')

def to_DT(df):
    df['date_time'] = pd.to_datetime(df['date_time'])
    return df

def is_time_between(check_time):
    y = str(check_time.year) 
    m = str(check_time.month)
    d = str(check_time.day)

    date = y + '-' + m + '-' + d
    begin_time = pd.to_datetime(date + ' 17:39:00', format= '%Y-%m-%d %H:%M:%S')
    end_time = pd.to_datetime(date + ' 20:59:00', format= '%Y-%m-%d %H:%M:%S')
    
    begin_hr = begin_time.hour
    check_hr = check_time.hour
    end_hr = end_time.hour
    
    begin_m = begin_time.minute
    check_m = check_time.minute
    end_m = end_time.minute
    
    begin_s = begin_time.second
    check_s = check_time.second
    end_s = end_time.second
    
    check1 = (check_hr >= begin_hr) & (check_m >= begin_m) & (check_s >= begin_s)
    check2 = (check_hr <= end_hr) & (check_m <= end_m) & (check_s <= end_s)
    
    return check1 and check2

'''
For Veil of Darkness Analysis
'''

def filter_stop_reason(df):
    return df[(df['stop_cause'] == 'Moving Violation') | (df['stop_cause'] == 'Equipment Violation') | (df['stop_cause'] == 'Traffic Violation') | (df['stop_cause'] == 'Reasonable Suspicion')]     

def get_veil(yr):
    
    file = pathlib.Path('data/cleaned/{}_clean.csv'.format(yr))
    if file.exists ():
        df = pd.read_csv(file)
        
    else: # file is test file
        df = pd.read_csv('data/test/cleaned/{}_clean.csv'.format(yr))
    
    inter = filter_stop_reason(df)
    inter = to_DT(inter)
    inter['in_veil'] = inter['date_time'].apply(lambda x: is_time_between(x))
    df = inter[inter['in_veil'] == True]
    path = 'data/intertw'
    if not os.path.exists(path):
        os.makedirs(path)
            
    df.to_csv(path + '/{}_intertw.csv'.format(yr))
    return df

def get_dates(yr):
    s = int(yr)
    start = datetime.datetime(s, 1, 1, 0, 0, 0)
    end = datetime.datetime(s, 12, 31, 0, 0, 0)

    delta = end - start
    dates = []
    for i in range(delta.days + 1):
        dates.append((start + datetime.timedelta(days=i)).strftime('%Y-%m-%d'))
    return dates

def get_sunset(yr):
    request_list = []
    dates = get_dates(yr)
    for date in dates:
        url = 'https://api.sunrise-sunset.org/json?lat=36.7201600&lng=-4.4203400&date={}'.format(date)
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        dct = data['results']
        dct['date'] = date
        request_list.append(dct)
    # build sunset df
    
    s = pd.DataFrame(request_list)
    s['date'] = pd.to_datetime(s['date'])
    time_cols = [x for x in s.columns][:-1]
    late_cols = ['sunset', 'civil_twilight_end', 'nautical_twilight_end', 'astronomical_twilight_end']
    for c in time_cols:
        s[c] = pd.to_datetime(s[c]).apply(lambda x: x.time()) 
        
    # save to data/sunset
    path = 'data/sunset'
    if not os.path.exists(path):
        os.makedirs(path)

    s.to_csv(path + '/{}_sunset.csv'.format(yr))
    return s
        
        
def is_dark(row, yr):    
    # after civil twilight - civil twilight begins
    date = pd.to_datetime(row.date_time).date()
    time = pd.to_datetime(row.date_time).time()
            
    fp = 'data/sunset/{}_sunset.csv'.format(yr)
    s = pd.read_csv(fp)
    s['date'] = s['date'].apply(lambda x: pd.to_datetime(x).date())
    sunrise_row = s[s['date'] == date]

    end = pd.to_datetime(sunrise_row.civil_twilight_end.values[0]).time()
    start = pd.to_datetime(sunrise_row.civil_twilight_begin.values[0]).time()    
    if time > end: # its dark
        return 1
    elif time < start:
        return 1
    else:
        return 0

# For mapping Divsions 
    
# from sd stop cards
div = {'N': [110,120,130], 'NE':[230,240], 'E':[310,320], 'SE':[430,440], 'C':[510,520,530], 
       'W':[610,620,630],'S':[710,720], 'MS': [810,820,830,840]}

# areas above and below the I-8
above_8 = ['N', 'E', 'NW', 'W', 'NE']

# stars with: 4, 5, 7, 8
below_8 = ['SE' , 'C', 'S', 'MS']
    
def get_div(service_area):
    val = int(str(service_area)[0]) - 1
    ls = ['N', 'NE', 'E', 'SE', 'C', 'W', 'S', 'MS']
    return ls[val]

def get_neighborhood(v):    
    if v in above_8:
        return 1
    elif v in below_8:
        return 0
    else:
        return 'Not Applicable'
    
# Investigation of Shortcomings 

# Seasonal Differences
def map_season(date):
    month = int(str(date).split('-')[1])
    if 3 <= month < 6:
        return 'Spring'
    elif 6 <= month < 8:
        return 'Summer'
    elif 8 <= month < 12:
        return 'Fall'
    else:
        return 'Winter'
    
def build_intertw(yr):
    veil = pd.read_csv('data/intertw/{}_intertw.csv'.format(yr))
    veil = to_DT(veil)
    veil['is_dark'] = veil.apply(lambda x: is_dark(x, yr), axis=1)

    # Monday is 0 and Sunday is 6.
    veil['date_stop'] = pd.to_datetime(veil['date_stop'])
    veil['day'] = veil['date_stop'].apply(lambda x: x.weekday())
    veil['div'] = veil['service_area'].apply(lambda x: get_div(x))
    veil['above_8'] = veil['div'].apply(lambda x: get_neighborhood(x))
    veil['Season']= veil['date_stop'].apply(lambda x: map_season(x))
    veil['Minority'] = veil['driver_race'].apply(lambda x: 0 if x == 'W' else 1)
    veil['under_25'] = veil['percieved_driver_age'].apply(lambda x: 1 if x < 25 else 0)
    
    # save IT to data/model
    path = 'data/model'
    if not os.path.exists(path):
        os.makedirs(path)

    veil.to_csv(path + '/{}_veil.csv'.format(yr))
    return veil
    
# adjust intertwilight period for bunching --> narrow by 30 minutes on each side
def adjust_dark(row, yr, minutes):
    # after civil twilight - civil twilight begins
    day = row.date_stop
    time = row.date_time.time()
    time = pd.to_timedelta(str(time))
    s = pd.read_csv('data/sunset/{}_sunset.csv'.format(yr))
    sunrise_row = s[s['date'] == day]
    
    adjust = datetime.timedelta(0, minutes)
    sunrise_time1 = pd.to_timedelta(str(sunrise_row.civil_twilight_end.values[0]))
    sunrise_time2 = pd.to_timedelta(str(sunrise_row.civil_twilight_begin.values[0]))
        
    if time > sunrise_time1 + adjust: # its dark
        return 1
    elif time < sunrise_time2  - adjust:
        return 1
    else:
        return 0
    
def add_adjusted_dark(df, minutes):
    new = to_DT(df)
    yr = str(new.date_stop[0])[:4]
    new['is_dark'] = new.apply(lambda x: adjust_dark(x, yr, minutes), axis=1)
    return df
    

def make_pivot(df, vals, idx, rM, rNM):
    filtered_df = df[(df['driver_race'] == rM) | (df['driver_race'] == rNM)]
    new =  filtered_df.pivot_table(values=vals,index=idx, aggfunc=np.mean)    
    return new

def stop_pivot(df, vals, rM, rNM):
    cs = pd.read_csv('data/census_data/sd_pop.csv')
    # get min
    dfs = []
    a1 = []
    a2 = []
    for r in rM:
        pop_min = cs[r].sum()
        pop_maj = cs[rNM].sum()
        
        df_dark = df[df['is_dark'] == 1]
        df_ndark = df[df['is_dark'] == 0]
        
        v1 = df_dark[df_dark['driver_race'] == r].shape[0] / pop_min
        v2 = df_dark[df_dark['driver_race'] == rNM].shape[0] / pop_maj
        d1 = pd.DataFrame([[v1, v2]])
        
        v3 = df_ndark[df_ndark['driver_race'] == r].shape[0] / pop_min
        v4 = df_ndark[df_ndark['driver_race'] == rNM].shape[0] / pop_maj
        d2 = pd.DataFrame([[v3, v4]])

        dfs.append(d1)
        dfs.append(d2)
        a1 += [r] *2 
        a2 += ['dark', 'not_dark']
        
    df =  pd.DataFrame(pd.concat(dfs))
    col1 = df[0].values
    col2 = df[1].values
    
    arrays = [a1, a2]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=['Minority', 'is_dark'])
    new = pd.DataFrame(list(zip(col1, col2)) , columns = ['Stop Rate Minority', 'Stop Rate Not Minority'], index=index)
    return new

def search_pivot(df, vals, rM, rNM, col='searched'):
    # get min
    dfs = []
    a1 = []
    a2 = []
    for r in rM:
        df_dark = df[df['is_dark'] == 1]
        df_ndark = df[df['is_dark'] == 0]
        
        v1 = df_dark[(df_dark['searched'] == 1) & (df_dark['driver_race'] == r)].shape[0] / df_dark.shape[0]
        v2 = df_dark[(df_dark['searched'] == 1) & (df_dark['driver_race'] == rNM)].shape[0] / df_dark.shape[0]
        d1 = pd.DataFrame([[v1, v2]])
        
        v3 = df_ndark[(df_ndark['searched'] == 1) & (df_ndark['driver_race'] == r)].shape[0] / df_ndark.shape[0]
        v4 = df_ndark[(df_ndark['searched'] == 1) & (df_ndark['driver_race'] == rNM)].shape[0] / df_ndark.shape[0]
        d2 = pd.DataFrame([[v3, v4]])

        dfs.append(d1)
        dfs.append(d2)
        a1 += [r] *2 
        a2 += ['dark', 'not_dark']
        
    df =  pd.DataFrame(pd.concat(dfs))
    col1 = df[0].values
    col2 = df[1].values
    
    arrays = [a1, a2]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=['Minority', 'is_dark'])
    new = pd.DataFrame(list(zip(col1, col2)) , columns = ['Search Rate Minority', 'Search Rate Not Minority'], index=index)
    return new

def stop_agg(d, col, rM, rNM):
    # get min
    total = []
    values = d[col].unique()
    cs = pd.read_csv('data/census_data/sd_pop.csv')

    for val in values:
        dfs = []
        a1 = []
        a2 = []
        df = d[d[col] == val]
        for r in rM:
            pop_min = cs[r].sum()
            pop_maj = cs[rNM].sum()
            
            df_dark = df[df['is_dark'] == 1]
            df_ndark = df[df['is_dark'] == 0]

            v1 = df_dark[df_dark['driver_race'] == r].shape[0] / pop_min
            v2 = df_dark[df_dark['driver_race'] == 'W'].shape[0] / pop_maj
            d1 = pd.DataFrame([[v1, v2]])

            v3 = df_ndark[df_ndark['driver_race'] == r].shape[0] / pop_min
            v4 = df_ndark[df_ndark['driver_race'] == 'W'].shape[0] / pop_maj
            d2 = pd.DataFrame([[v3, v4]])

            dfs.append(d1)
            dfs.append(d2)
            a1 += [r] *2 
            a2 += ['dark', 'not_dark']
        
        df =  pd.DataFrame(pd.concat(dfs))
        col1 = df[0].values
        col2 = df[1].values

        arrays = [a1, a2]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples, names=['Minority', 'is_dark'])
        new = pd.DataFrame(list(zip(col1, col2)) , columns = ['Stop Rate Minority', 'Stop Rate Non-Majority'], index=index)
        total.append(new)
    final = pd.concat(total, keys=values)
    idx = list(final.index.names)
    idx[0] = col
    final.index.names = idx
    return final


def search_agg(d, col, rM):
    # get min
    total = []
    values = d[col].unique()
    
    for val in values:
        dfs = []
        a1 = []
        a2 = []
        df = d[d[col] == val]
        for r in rM:
            df_dark = df[df['is_dark'] == 1]
            df_ndark = df[df['is_dark'] == 0]

            v1 = df_dark[(df_dark['searched'] == 1) & (df_dark['driver_race'] == r)].shape[0] / df_dark.shape[0]
            v2 = df_dark[(df_dark['searched'] == 1) & (df_dark['driver_race'] == 'W')].shape[0] / df_dark.shape[0]
            d1 = pd.DataFrame([[v1, v2]])

            v3 = df_ndark[(df_ndark['searched'] == 1) & (df_ndark['driver_race'] == r)].shape[0] / df_ndark.shape[0]
            v4 = df_ndark[(df_ndark['searched'] == 1) & (df_ndark['driver_race'] == 'W')].shape[0] / df_ndark.shape[0]
            d2 = pd.DataFrame([[v3, v4]])

            dfs.append(d1)
            dfs.append(d2)
            a1 += [r] *2 
            a2 += ['dark', 'not_dark']
        
        df =  pd.DataFrame(pd.concat(dfs))
        col1 = df[0].values
        col2 = df[1].values

        arrays = [a1, a2]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples, names=['Minority', 'is_dark'])
        new = pd.DataFrame(list(zip(col1, col2)) , columns = ['Search Rate Minority', 'Search Rate W'], index=index)
        total.append(new)
    final = pd.concat(total, keys=values)
    idx = list(final.index.names)
    idx[0] = col
    final.index.names = idx
    return final

def search_by_minority(df, rM, rNM, col='searched'):
    tbls = []
    for r in rM:        
        t = make_pivot(df, col, ['Minority'], r, rNM)[col]
        if col != 'searched':
            n = 'W vs. {} {} Rate'.format(r, col)
        else:
            n = 'W vs. {} Search Rate'.format(r)
        
        t.name = n
        tbls.append(t)
    return pd.DataFrame(tbls).T

def compare_dark(df, rM, rNM):
    # get min
    dfs = []
    for r in rM:
        df_dark = df[df['is_dark'] == 1]
        df_ndark = df[df['is_dark'] == 0]
        
        test1 = ttest(df_dark, r, rNM)
        statistic1 = test1[0]
        pval1 = test1[1]
        d1 = pd.DataFrame([[statistic1, pval1]])
        
        test2 = ttest(df_ndark, r, rNM)
        statistic2 = test2[0]
        pval2 = test2[1]
        d2 = pd.DataFrame([[statistic2, pval2]])

        dfs.append(d1)
        dfs.append(d2)
        
    df =  pd.DataFrame(pd.concat(dfs))
    col1 = df[0].values
    col2 = df[1].values
    
    arrays = [['B', 'B', 'H', 'H'],['dark', 'not_dark', 'dark', 'not_dark']]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=['Minority', 'is_dark'])
    new = pd.DataFrame(list(zip(col1, col2)) , columns = ['statistic', 'pvalue'], index=index)
    return new

def add_region(ser):
    new = pd.Series(ser.index.get_level_values(0)).apply(lambda x: 1 if x in above_8 else 0).values
    return new

def filter_y(df):
    df = df[df['under_25'] == 1]
    return df

def run_summary(df, rM, rNM):
    t = df.replace([np.inf, -np.inf], np.nan)
    t = t.dropna(subset=['percieved_driver_age', 'driver_race', 'Minority', 'searched'])
    
    t = t[(t['driver_race'] == rM) | (t['driver_race'] == rNM)]
    X = np.array(t[['Minority','percieved_driver_age']])

    y = np.array(t.searched)
    X = sm.add_constant(X)
    ols = sm.OLS(y, X)
    ols_result = ols.fit()
    ols_result.params
    
    print(ols_result.summary())
    
def plot_minority(df, rM, rNM):
    t = df[(df['driver_race'] == rM) | (df['driver_race'] == rNM)]
    t.groupby('Minority').percieved_driver_age.plot(kind='hist', legend=True);