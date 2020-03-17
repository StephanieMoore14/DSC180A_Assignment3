import matplotlib.pyplot as plt
from functools import reduce
import pandas as pd
import numpy as np
import regex as re
import datetime

def to_DT(df):
    df['date_time'] = pd.to_datetime(df['date_time'])
    return df

def null_dist(df, cols):
         
    n = df[cols].isnull().sum()
    f = pd.DataFrame(n.values / df.shape[0], columns=['% Null'], index = n.index).T
    
    if cols == ['subject_race']:
        f = f.rename(columns={'subject_race': 'race'})
        
    return f

def plot_counts(df, col):
    new = pd.DataFrame(df[col].value_counts()).rename(columns={col: 'Counts: {}'.format(col)})
    return new
    

# bad age helper
def get_non_numeric(ser, col):
    non_num = {}
    for element in list(ser):
        if type(element) == int:
            pass
        elif str(element) == 'nan':
            if 'nan' in non_num.keys(): non_num['nan'] += 1
            else: non_num['nan'] = 1
        
        elif re.match(r'^-?\d+(?:\.\d+)?$', element) is None:
            if element in non_num.keys(): non_num[element] += 1
            else: non_num[element] = 1
    d =  pd.DataFrame(non_num, index=[0]).T.rename(columns={0:'Counts'}).sort_values(by='Counts', ascending=False)
    d = d.reset_index()
    d = d.set_index('index')
    d.index.name = col
    
    if col == 'subject_age':
        d.index.name = 'perceived_age'
    return d

def plot_bad_ages(df, age_col):
    ignore = list(get_non_numeric(df[age_col], age_col).index.values)
    filt = df[age_col].apply(lambda x: False if x in ignore else True)
    bad = df[filt]
    bad[age_col] = bad[age_col].astype(str)
    bad = bad[(bad[age_col] < '13') | (bad[age_col] > '85')][age_col].value_counts()
    bad = pd.DataFrame(bad)
    bad = bad.rename(columns={age_col:'Counts'})
    bad.index.name = 'perceived_age'
    return bad    

def get_bins(ser):
    # get bin size
    n = ser.shape[0]
    Range = int(np.round(max(ser) - min(ser)))
    num_intervals = int(np.round(np.sqrt(n)))
    width_intervals = int(np.round(Range / num_intervals))
    bs = []
    val = 0
    for i in range(num_intervals):
        bs.append(val)
        val += width_intervals
    return bs
    
def make_hist_age(df, t, col):
    ser = pd.to_numeric(df[col], errors='coerce').dropna()
    age = np.arange(0,100,1)
    ser.plot.hist(bins=age, title=t, colormap='jet')
    plt.xlabel(col)
    plt.ylabel('FREQUENCY')
    #plt.axis([0, 100, 0, 40000]);  #[xmin, xmax, ymin, ymax]
    plt.grid(axis='y', alpha=0.75)

def plot_minute(df):
    d = to_DT(df)
    yr = d.date_time[0].year
    t = d.date_time.apply(lambda x: x.minute)
    b = np.arange(0, 60, 1)
    t.plot.hist(bins=b, title='Histogram of Time Distribution of Minutes: {}'.format(yr), colormap='jet')
    plt.xlabel('minute')
    plt.ylabel('FREQUENCY')
    #plt.axis([0, 60, 0, 10000]);  #[xmin, xmax, ymin, ymax]
    plt.grid(axis='y', alpha=0.75)


def plot_outcomes(df, yr):
    format_cols = ['Search was conducted', 'Arrested', 'Property was seized', 'Contraband Found']
    
    d = df[df.outcome != 'Not Applicable']
    
    if yr < 2018:
        ser = d.outcome.value_counts()
    
    if yr == 2018:
        s1 = d[d['date_time'].astype(str) < '2018-07-00 00:00:00']
        s1 = s1.outcome.value_counts()
        
        labels = s1.index
        sizes = s1.values
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, autopct='%1.1f%%', shadow=False, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title('Outcome Distribution: {} pre-RIPA'.format(yr))
        plt.legend(labels=labels, loc='upper center', bbox_to_anchor=(0.5, -0.05),fancybox=True, shadow=False, ncol=2)
        plt.show()
        
        
        s2 = d[d['date_time'].astype(str) >= '2018-07-01 00:00:00']
        s2 = s2.outcome.value_counts()
        s2['Search was conducted'] = d.searched.sum()
        labels = s2.index
        sizes = s2.values
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, autopct='%1.1f%%', shadow=False, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title('Outcome Distribution: {} post-RIPA'.format(yr))
        plt.legend(labels=labels, loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=2)
        plt.show()   
    
    else:
        ser = d.outcome.value_counts()
        ser['Search was conducted'] = d.searched.sum()
        
        labels = ser.index
        sizes = ser.values
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, autopct='%1.1f%%', shadow=False, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title('Outcome Distribution: {}'.format(yr))
        plt.legend(labels=labels, loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=False, ncol=2)
        plt.show()   

def plot_races(df, yr):
    df.driver_race.value_counts().plot(kind='bar')
    plt.title('Distribtion of Race Codes: {}'.format(yr))
    plt.xlabel('Race Code')
    plt.ylabel('Number of Stops')
    plt.show()
    
def outcome_dist(df, races):
    yr = str(df.date_time[0])[:4]
    if yr == '2018':
        # return 2 dfs
        d = df[(df['driver_race'].isin(races)) &(df['outcome'] != 'Not Applicable')]
        s1 = d[d['date_time'].astype(str) < '2018-07-00 00:00:00']
        s2 = d[d['date_time'].astype(str) >= '2018-07-00 00:00:00']
        
        d1 = s1.groupby('driver_race')['outcome'].value_counts()
        for r in races:
            val = d1.loc[r].values
            d1.loc[r] = val / val.sum()
        f1 =  pd.DataFrame(d1).rename(columns={'outcome': 'Distribution of Outcomes'}).sort_values(by=['driver_race', 'Distribution of Outcomes'], ascending = False)
        
        d2 = s2.groupby('driver_race')['outcome'].value_counts()
        for r in races:
            val = d2.loc[r].values
            d2.loc[r] = val / val.sum()
        f2 =  pd.DataFrame(d2).rename(columns={'outcome': 'Distribution of Outcomes'}).sort_values(by=['driver_race', 'Distribution of Outcomes'], ascending = False)

        return (f1, f2)
    
    else:
        d = df[(df['driver_race'].isin(races)) &(df['outcome'] != 'Not Applicable')]
        dg = d.groupby('driver_race')['outcome'].value_counts()
        for r in races:
            val = dg.loc[r].values
            dg.loc[r] = val / val.sum()
        final =  pd.DataFrame(dg).rename(columns={'outcome': 'Distribution of Outcomes'}).sort_values(by=['driver_race', 'Distribution of Outcomes'], ascending = False)

        return final