from cleaning import format_df
import pandas as pd
import numpy as np
import os

def get_table(yr):
    '''
    Gets a table of raw data given a year
    '''
    if int(yr) < 2018:
        url = 'http://seshat.datasd.org/pd/vehicle_stops_{}_datasd_v1.csv'.format(yr)
        df = pd.read_csv(url)
        # save to data/raw
        path = 'data/raw'
        if not os.path.exists(path):
            os.makedirs(path)
        
        df.to_csv(path + '/{}_raw.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        return df
    
    else: # post- 2018
        # cols we care about
        cols_2018 = ['stop_id', 'pid', 'date_stop', 'time_stop', 'stopduration', 
                 'officer_assignment_key', 'exp_years', 'beat', 
                 'perceived_age', 'gend']

        url = 'http://seshat.datasd.org/pd/ripa_stops_datasd_v1.csv'
        df = pd.read_csv(url)        
        return df[cols_2018]


def get_merge_data():
    '''
    Gets data from tables needed to add to post- 2018 basic data
    '''
    reason = 'stop_reason'
    reason_cols = ['stop_id', 'pid', 'reason_for_stop', 'reason_for_stopcode']

    result = 'stop_result'
    result_cols= ['stop_id', 'pid', 'result']

    race = 'race'
    race_cols = ['stop_id', 'pid', 'race']

    action = 'actions_taken'
    action_cols = ['stop_id', 'pid', 'action']

    base = 'http://seshat.datasd.org/pd/ripa_{}_datasd.csv'

    reason_df = pd.read_csv(base.format(reason))
    result_df = pd.read_csv(base.format(result))
    race_df = pd.read_csv(base.format(race))
    action_df = pd.read_csv(base.format(action))
    
    return [[reason_cols, result_cols, race_cols, action_cols], [reason_df, result_df, race_df, action_df]]

def gen_cols(df1, gen_df, cols):
    '''
    Merges a table of additional data with current data
    '''

    new = df1.merge(gen_df, on = ['stop_id', 'pid'])
    drop = [x for x in new.columns if x not in cols]
    new = new.drop(columns = drop).drop_duplicates(subset = ['stop_id', 'pid'])
    return new

def merge_data(tbl):
    '''
    Merges all the additional data for post- 2018 with the raw basic data
    '''

    merge_cols = get_merge_data()[0]
    merge_dfs = get_merge_data()[1]
    merged = []

    for i in range(len(merge_dfs)):
        merged.append(gen_cols(tbl, merge_dfs[i], merge_cols[i]))
          
    first = merged[0]
    for i in range(0, len(merged)):
        if i == len(merged) - 1:
            break 
        first = pd.merge(first, merged[i + 1], on =  ['stop_id', 'pid'], how='outer')

    df = pd.merge(tbl, first, on = ['stop_id', 'pid'])
    df = df.drop_duplicates(subset = ['stop_id', 'pid'])
    
    return df


def get_data(yr):
    '''
    Gets cleaned and formatted data given the year
    '''
    tbl = get_table(yr)
    
    if int(yr) < 2018:
        final = format_df(tbl, yr)
        # save to data/cleaned
        path = 'data/cleaned'
        if not os.path.exists(path):
            os.makedirs(path)
        
        final.to_csv(path + '/{}_clean.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        return 
    else:
        df = merge_data(tbl)
        # save to data/raw
        path1 = 'data/raw'
        if not os.path.exists(path1):
            os.makedirs(path1)    
        
        df.to_csv(path1 + '/{}_raw.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        
        # make clean
        final = format_df(df, yr)
        
        
        if int(yr) == 2018:
            # concat data:
            t = get_table(2017)
            pre_ = format_df(t, yr, True)
            final = pd.concat([pre_, final])
        
        # save to data/cleaned
        path2 = 'data/cleaned'
        if not os.path.exists(path2):
            os.makedirs(path2)
            
        final.to_csv(path2 + '/{}_clean.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        return 
    
    
    
def get_data_test(yr):
    '''
    Gets cleaned and formatted data given the year
    '''
    tbl = get_table(yr)
    
    if int(yr) < 2018:
        path1 = 'data/test/raw'
        if not os.path.exists(path1):
            os.makedirs(path1)
        
        tbl_f = tbl.iloc[:100, :]
        tbl_f.to_csv(path1 + '/{}_raw.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        
        
        
        final = format_df(tbl, yr)
        # save to data/cleaned
        path2 = 'data/test/cleaned'
        if not os.path.exists(path2):
            os.makedirs(path2)
        
        test_f = final.iloc[:100, :]
        test_f.to_csv(path2 + '/{}_clean.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        return 
    
    else:
        df = merge_data(tbl)
        # save to data/raw
        path1 = 'data/test/raw'
        if not os.path.exists(path1):
            os.makedirs(path1)    
        
        test_df = df.iloc[:100, :]
        test_df.to_csv(path1 + '/{}_raw.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        
        # make clean
        final = format_df(df, yr)
        
        
        if int(yr) == 2018:
            # concat data:
            t = get_table(2017)
            pre_ = format_df(t, yr, True)
            final = pd.concat([pre_, final])
        
        # save to data/cleaned
        path2 = 'data/test/cleaned'
        if not os.path.exists(path2):
            os.makedirs(path2)
            
        test_f = final.iloc[:100, :]
        final.to_csv(path2 + '/{}_clean.csv'.format(yr), date_format='%Y-%m-%d %H:%M:%S', index=False)
        
        return  
    
    