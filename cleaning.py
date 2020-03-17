import geopandas as gpd
import pandas as pd
import numpy as np
import regex as re

# PRE- 2018 Format:
# ----------------------------------------------------------------------------------

def change_bool(string):
    '''
    Changes string values to boolean
    '''
    if (string == 'Y') | (string =='y'):
        return 1
    if (string == 'N') | (string == 'n'):
        return 0
    return np.nan

def map_bool(cols, df):
    '''
    Maps string values in given columns to boolean
    '''
    for col in cols:
        if col not in list(df.columns):
            continue
        df[col] = df[col].apply(lambda x: change_bool(x))
    return df

# ----------------------------------------------------------------------------------

# POST- 2018 Format:

# -------------------------------------------------------------------------------------
def change_sex(x):
    '''
    Changes male and female vales of gender to numeric
    '''
    if (x == 1.0) | (x == 1):
        return 'M'
    elif (x == 2.0) | (x == 2):
        return 'F'
    else:
        return np.nan

def map_sex(col):
    '''
    Maps change_sex function to given gender column
    '''
    return col.apply(lambda x: change_sex(x))

def map_race(df):
    '''
    Uses te existing race code map from:
    'http://seshat.datasd.org/pd/vehicle_stops_race_codes.csv'
    and observation to match the pre- 2018 race codes with the post- 2018
    '''

    race_dict = {
     'Asian' : 'A',
     'OTHER ASIAN': 'A',
     'Middle Eastern or South Asian': 'M',
     'BLACK': 'B',
     'Black/African American': 'B',
     'CHINESE': 'C',
     'CAMBODIAN': 'D',
     'FILIPINO': 'F',
     'GUAMANIAN': 'G',
     'HISPANIC': 'H',
     'Hispanic/Latino/a': 'H',
     'HISPANIC/LATINO/A': 'H',
     'INDIAN': 'I',
     'JAPANESE': 'J',
     'KOREAN': 'K',
     'LAOTIAN': 'L',
     'OTHER': 'O',
     'Other': 'O',
     'PACIFIC ISLANDER': 'P',
     'Pacific Islander': 'P',
     'SAMOAN': 'S',
     'HAWAIIAN': 'U',
     'VIETNAMESE': 'V',
     'WHITE': 'W',
     'White': 'W',
     'ASIAN INDIAN': 'Z',
     'Native American': 'N'
    }
    df['Race Code'] = df['race'].map(race_dict)
    return df

def map_service_area(df):
    '''
    Add an additional service area columns to the pre-existing data
    with just police beats to allow for multi- year analysis of 2018 
    with pre- 2018
    '''
    stop_beats = 'http://seshat.datasd.org/sde/pd/pd_beats_datasd.geojson'
    beats = gpd.read_file(stop_beats)
    
    # get unique beats
    unique_beats = beats[['beat', 'serv']].drop_duplicates('beat')
    beat_dict = dict(zip(unique_beats.beat, unique_beats.serv))
    
    df['service_area'] = df['beat'].map(beat_dict)
    return df

def rename_cols(df, yr):
    '''
    Renames columns to have same format pre and post 2018
    '''
    if int(yr) < 2018:
        df = df.rename(columns={'subject_age': 'percieved_driver_age', 'subject_sex': 'driver_sex', 
                                'subject_race': 'driver_race'})
        return df
    else:
        df = df.rename(columns={'perceived_age': 'percieved_driver_age', 'gend': 'driver_sex', 
                                'Race Code': 'driver_race', 'reason_for_stop': 'stop_cause'})
        return df
    
def map_searched(df):
    df['searched'] = df['action'].apply(lambda a: 1 if  ((a == 'Search of property was conducted') | (a == 'Property was seized') | (a == 'Search of person was conducted')) else 0)
    
    return df

# ------------------------------------------------------------------------------

# Both Formats:

# ------------------------------------------------------------------------------

def clean_bool(df, yr):
    '''
    Changes the necessary object columns to boolean
    '''
    if int(yr) < 2018:
        c = ['sd_resident', 'searched', 'contraband_found', 'property_seized', 'arrested']
        return map_bool(c, df)
    else:
        df['gend'] = map_sex(df['gend'])
        return df

def clean_age(df, age_col = 'percieved_driver_age'):
    '''
    Filters out 'bad ages' most likely human error
    '''
    cts = df[age_col].value_counts() 
    bad_age = cts[cts <= 10].index
    df = df[~df[age_col].isin(bad_age)]
    df[age_col] = df[age_col].apply(lambda x: np.nan if ((str(x) == 'nan') | (str(x) == 'No Age')) else int(x))
    return df

def fix_time(t):
    if (type(t) == np.float) | ('.' in str(t)) | (t == 'None'):
        return np.nan
    
    if str(t)[0] == ' ':
        t = '0' + str(t)[1:]
    
    if '-' in str(t):
        t = str(t).replace('-', '0')
    
    if '_' in str(t):
        t = str(t).replace('_', '0')    
    
    if ' ' in str(t):
        t = str(t).replace(' ', '0')
    
    if ':' in str(t):
        if len(t) <= 8:
            if len(t) == 7:
                t = '0' + t
            if len(t) == 5: # add trailing 00s
                t = t + ':00'
            if len(t) == 4:
                t = '0' + t + ':00'
    return t

def clean_time(df):
    '''
    Changes format of time to easily determine inter-twilight period 
    for Veil of Darkness
    '''
    def check_time(row):
        time = row.time_stop
        t = fix_time(time)
        
        if len(str(t)) != 8:
            return np.nan

        hr = str(t)[:2]
        m = str(t)[3:5]
        s = str(t)[-2:]
        
        if (hr > '23') |(m > '59') | (s > '59'):
            return np.nan
        
        return pd.to_datetime(str(row.date_stop) + ' ' + str(t))
    
    df['date_time'] = pd.to_datetime(df.apply(lambda x: check_time(x), axis=1))
    
    return df.dropna(subset=['date_time']) # < 500 rows

def filter_service_area(df):
    df = df[df['service_area'] != 'Unknown']
    df = df.dropna(subset=['service_area'])
    df['service_area'] = df['service_area'].astype(int)
    df =  df[df['service_area'] <= 840]
    return df
    
# ----------------------------------------------------------------------------------

# Outcome Engineering:

# ----------------------------------------------------------------------------------

'''
The following 3 functions create a feature called "outcome" for pre and post
2018. For the purpose of this study, the outcomes assigned are either:
"Not Applicable", "Warning (verbal or written)", "Search was conducted",
"Property was seized", or "Arrest". These are chosen because they make up 
the large majority of outcomes and they are consistent across pre- and post- 2018 data.
'''

def check_outcome(row, year):
    if int(year) < 2018:
        # check 'arrested', 'searched', 'property_seized'
        if row.arrested == 1.0:
            return 'Arrested'
        elif row.contraband_found == 1.0:
            return 'Contraband Found'
        elif row.property_seized == 1.0:
            return 'Property was seized'
        elif row.searched == 1.0:
            return 'Search was conducted'
        return 'Not Applicable'
        
    else:
        a = row.action
        r = row.result
        
        # check worst outcome first
        if (r == 'Custodial Arrest without warrant') | (r == 'Custodial Arrest pursuant to outstanding warrant'):
            return 'Arrested'
        
        elif a == 'Property was seized':
             return a
        
        elif (r == 'Citation for infraction') | (r == 'In-field cite and release'):
            return 'Citation'
        
        elif (a == 'Field interview card completed'):
            return a
        
        elif r == 'Warning (verbal or written)':
            return r
                
        else:
            return 'Not Applicable'
    
def outcome_map(df, yr):
    df_copy = df.copy()
    df_copy['outcome'] = df_copy.apply(lambda x: check_outcome(x, yr), axis=1)
    
    if int(yr) < 2018:
        # keep searched column for post- stop outcome analysis
        return df_copy.drop(columns=['arrested', 'property_seized', 'obtained_consent', 'contraband_found'])
        
    return df_copy.drop(columns=['action', 'result'])    
    
def get_post_year(df, yr, special_2018=False): 
    if special_2018: # need 2018 from 2017 data
        Bool = df['date_stop'].apply(lambda x: x[:4] == '2018')
        return df[Bool]
        
    Bool = df['date_stop'].apply(lambda x: x[:4] == str(yr))
    return df[Bool]
# ----------------------------------------------------------------------------------

# Final Formatting of Data

'''
The following 2 functions apply all the helper functions to clean the data
'''
def pre_2018_format(df, yr, special_2018=False):
    if special_2018:
        yr = 2017
    df = clean_bool(df, yr)
    df = filter_service_area(df)
    df = rename_cols(df, yr)
    df = clean_age(df)
    df = clean_time(df)
    df = outcome_map(df, yr)
    if special_2018:
        yr = 2018
    df = get_post_year(df, yr, special_2018)
    
    return df

def post_2018_format(df, yr):
    df = clean_bool(df, yr)
    df = map_searched(df)
    df = map_race(df)
    df = map_service_area(df)
    df = filter_service_area(df)
    df = rename_cols(df, yr)
    df = clean_age(df)
    df = clean_time(df)
    df = outcome_map(df, yr)  
    df = get_post_year(df, yr)
    return df

def format_df(df, yr, special_2018=False):
    '''
    Formats the data given the year and puts the columns in the same order 
    (easier to read when looking at two df)
    '''
    
    if (int(yr) < 2018) | (special_2018):
        cols = ['stop_id', 'stop_cause', 'date_stop', 'time_stop', 'date_time', 'searched', 'outcome', 'service_area', 'driver_race', 
                'driver_sex', 'percieved_driver_age', 'sd_resident']
        df = pre_2018_format(df, yr, special_2018)
        return df[cols]
    
    else:
        cols = ['stop_id', 'pid', 'stop_cause', 'reason_for_stopcode', 'date_stop', 'time_stop', 'date_time', 'stopduration', 
                'searched', 'outcome', 'beat', 'service_area', 'driver_race', 'driver_sex', 'percieved_driver_age',
                'officer_assignment_key', 'exp_years', 'year']
        
        df = post_2018_format(df, yr)
        
        # check for last duplicate
        df = df.drop_duplicates(subset = ['stop_id', 'date_time', 'beat', 'officer_assignment_key'])
        # add year column for future concating / analysis by year
        df['year'] = [yr] * df.shape[0]
        return df[cols]