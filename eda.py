from src.generate_pop import gen_sd_pop
from functools import reduce
import pandas as pd
import numpy as np


cs = pd.read_csv('data/census_data/sd_pop.csv')

def to_DT(df):
    df['date_time'] = pd.to_datetime(df['date_time'])
    return df

################################################################################################

# Traffic Stop Analysis #

################################################################################################

# Stop Rates

def filter_service_area(df):
    d = df.copy()
    d['service_area'] = d['service_area'].apply(lambda x: int(x) if ((x != 'Unknown') | (str(x) != 'nan')) else np.nan)
    return d

def get_sd_pop():
    df = gen_sd_pop()
    return df

def get_stop_rates(df):
    c = cs
    d = {}
    l = ['W', 'B', 'H', 'A']
    total_pop_2010 = c['Total'].sum()
    for r in l:
        d[r] = df[df.driver_race == r].shape[0] / total_pop_2010
    d =  pd.DataFrame(d.values(), index = d.keys(), columns=['Stop Rates']).sort_values(by='Stop Rates', ascending=False)
    d['Proportion of Population'] = c[l].sum() / c['Total'].sum()
    d.index.name = 'Race'
    return d

def stop_rates_by_serv(df):
    c = cs
    df_list = []
    l = ['W', 'B', 'H', 'A']
    
    gb = c.groupby('serv')
    
    new = df[(df['service_area'] != 'Unknown') & (~df['service_area'].isna())]
    new['service_area'] = new['service_area'].apply(lambda x: int(x))
    
    for race in l:
        d = {}
        # list of total pop by service area, race
        ser = gb[race].sum() 
        
        # list of total stops by service area
        stops_race = new[new['driver_race'] == race]
        stops = stops_race.groupby('service_area')['stop_id'].count()

        area_race_stops = pd.merge(pd.DataFrame(ser).reset_index(), pd.DataFrame(stops).reset_index(), left_on='serv', right_on='service_area').drop(columns='service_area').rename(columns={'serv':'service_area', race: '{}_population'.format(race), 'stop_id': 'num_stops'})

        # get stop rate
        area_race_stops['{}_stop_rate'.format(race)] = area_race_stops['num_stops'] / area_race_stops['{}_population'.format(race)]
        curr = area_race_stops[['service_area', '{}_stop_rate'.format(race)]]
        df_list.append(curr)
    
    final = reduce(lambda x, y: pd.merge(x, y, on = 'service_area'), df_list).set_index('service_area')    
    return final

# Post Stop Outcomes

def add_searched(df):
    # add 'searched col'
    df['searched'] = df['outcome'].apply(lambda x: 1 if x == 'Search was conducted' else 0)
    return df

def add_race_txt(df):
    race_code_dict = {
     'A': 'ASIAN',
     'M': 'MIDDLE EASTERN OR SOUTH ASIAN',
     'B': 'BLACK',
     'C': 'CHINESE',
     'D': 'CAMBODIAN',
     'F': 'FILIPINO',
     'G': 'GUAMANIAN',
     'H': 'HISPANIC/LATINO/A',
     'I': 'INDIAN',
     'J': 'JAPANESE',
     'K': 'KOREAN',
     'L': 'LAOTIAN',
     'O': 'OTHER',
     'P': 'PACIFIC ISLANDER',
     'S': 'SAMOAN',
     'U': 'HAWAIIAN',
     'V': 'VIETNAMESE',
     'W': 'WHITE',
     'Z': 'ASIAN INDIAN',
     'N': 'NATIVE AMERICAN'
    }
    # check if race is the index
    idx = df.index.name
    if (idx == 'race') | (idx == 'driver_race'): 
        #race is index
        val = pd.Series(df.index, index=df.index).apply(lambda x: race_code_dict[x] if x in race_code_dict.keys() else 'Not Applicable')
        df['race_mapped'] = val
    
    else: 
        # race is just a column
        if 'subject_race' in df.columns:
            col = 'subject_race'
        elif 'race' in df.columns:
            col = 'race'
        else: 
            col = 'driver_race'
        new = df[col].apply(lambda x: race_code_dict[x].upper() if x in race_code_dict.keys() else 'Not Applicable')
        df['race_mapped'] = new
    return df

def search_rate(col):
        # drop nulls
        c = col.where(col == 1, 0)
        return sum(c) / col.shape[0]
    

def search_rate_by_race(df):      
    new = df[(df['driver_race'] == 'W') | (df['driver_race'] == 'B') | (df['driver_race'] == 'H') | (df['driver_race'] == 'A')]
    f = pd.DataFrame(new.groupby(['driver_race'])['searched'].apply(search_rate)).rename(columns={'searched':'search_rate'})
    
    d = f[f['search_rate'] != float(0)].sort_values(by='search_rate', ascending=False)
    return d

def ttest(df, rM, rNM, col='searched'):
    # Testing the average difference in stop rates between two groups:
    filtered_df = df[(df['driver_race'] == rM) | (df['driver_race'] == rNM)]
    t = filtered_df.dropna(subset=[col])
    
    minority = t.loc[t.Minority == 1, col]
    not_minority = t.loc[t.Minority == 0, col]
    
    return stats.ttest_ind(minority, not_minority)

def hit_rate1(df):
    hit = ['Arrested']
    df['success_hit'] = df['outcome'].apply(lambda x: 1 if x in hit else 0)
    new = df[(df['driver_race'] == 'W') | (df['driver_race'] == 'B') | (df['driver_race'] == 'H') | (df['driver_race'] == 'A')]
    d = new.groupby('driver_race')['success_hit'].apply(lambda x: x.sum() / x.shape[0])
    d = pd.DataFrame(d)
    d = d.rename(columns={'success_hit': 'hit_rate: Arrested'})
    
    return d.sort_values(by='hit_rate: Arrested', ascending=False)

# useful for pre-2018 data
def hit_rate2(df):
    hit = ['Arrested', 'Property was seized', 'Contraband Found']
    df['success_hit'] = df['outcome'].apply(lambda x: 1 if x in hit else 0)
    new = df[(df['driver_race'] == 'W') | (df['driver_race'] == 'B') | (df['driver_race'] == 'H') | (df['driver_race'] == 'A')]
    d = new.groupby('driver_race')['success_hit'].apply(lambda x: x.sum() / x.shape[0])
    d = pd.DataFrame(d)
    d = d.rename(columns={'success_hit': 'hit_rate: Arrested, Property Seized, Contraband Found'})
    
    return d.sort_values(by='hit_rate: Arrested, Property Seized, Contraband Found', ascending=False)