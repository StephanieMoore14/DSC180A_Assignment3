import geopandas as gpd
import pandas as pd
import numpy as np


def gen_sd_pop():
    shp_file =('src/census_data/nhgis_shape/CA_block_2010.shp')
    census_2010 = gpd.read_file(shp_file)
    
    # filter to SD county
    SD_c2010 = census_2010[census_2010['COUNTYFP10'] == '073']

    # get pop by race files
    csv_NH_fp = 'src/census_data/nhgis_csv/nhgis_ds172_2010_block.csv'
    txt_NH = pd.read_csv(csv_NH_fp)
    
    # filter to SD county
    SD_block = txt_NH[txt_NH['COUNTY'] == 'San Diego County']
    
    # reduce dimensions
    SD_block = SD_block[['GISJOIN','YEAR','H7X001','H7X002','H7X003','H7X004','H7X005','H7X006','H7X007','H7X008']]

    # hispanic race in seperate table
    csv_H_fp = 'src/census_data/nhgis_csv/nhgis_ds172_2010_block_H.csv'
    txt_H = pd.read_csv(csv_H_fp)
    
    # reduce dimensions
    txt_H = txt_H[['GISJOIN', 'H73001', 'H73002']]

    # census block centroids in sd beats: src --> self made arcGIS.online 
    intersect = pd.read_csv('src/asrGIS_cesus_centroids/sd_beats_block.csv')
    
    # reduce dimensions
    intersect = intersect[['GISJOIN','beat', 'div', 'serv']]

    # merge all on GISJOIN
    dd = pd.merge(SD_block, intersect, on=['GISJOIN'])
    df = pd.merge(dd, txt_H, on=['GISJOIN'])

    # map col names
    d = {'H7X001':'Total',
            'H7X002':'White alone',
            'H73002': 'Hispanic or Latino',
            'H7X003':'Black or African American alone',
            'H7X004':'American Indian and Alaska Native alone',
            'H7X005':'Asian alone',
            'H7X006':'Native Hawaiian and Other Pacific Islander alone',
            'H7X007':'Some Other Race alone',
            'H7X008':'Two or More Races'}
    d_codes = {
            'White alone':'W',
            'Hispanic or Latino': 'H',
            'Black or African American alone': 'B',
            'American Indian and Alaska Native alone': 'N',
            'Asian alone':'A',
            'Native Hawaiian and Other Pacific Islander alone': 'U & P',
            'Some Other Race alone': 'O'
    }
    df = df.rename(columns = d)
    df = df.rename(columns = d_codes) # show work to trace later if needed
    
    # get rid of empty rows
    df = df[df['Total'] != 0]
    
    # Groupby: combine row entries to create totals 
    final = df.groupby(['YEAR', 'beat', 'serv'])[['Total', 'W', 'H', 'B', 'N', 'A', 'U & P', 'O', 'Two or More Races']].sum()
    
    return final