#!/usr/bin/env python

import sys
import json
import shutil

sys.path.insert(0, 'src') # add library code to path

from etl import get_data, get_data_test
from VoD import get_veil, build_intertw


DATA_PARAMS = 'config/01-data.json'
CLEAN_PARAMS = 'config/02-clean.json'
MODEL_PARAMS = 'config/03-model.json'

TEST_DATA_PARAMS = 'config/test-01-data.json'
TEST_CLEAN_PARAMS = 'config/test-02-clean.json'

def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)

    return param

def main(targets):      
        
    # make the clean target
    if 'clean' in targets:
        shutil.rmtree('data/raw', ignore_errors=True)
        shutil.rmtree('data/cleaned', ignore_errors=True)
        shutil.rmtree('data/sunset', ignore_errors=True)
        shutil.rmtree('data/model', ignore_errors=True)
        shutil.rmtree('data/test', ignore_errors=True)

    if 'test-project' in targets: # create project
    
    # make the data target
    #if 'data' in targets:
        cfg = load_params(DATA_PARAMS)
        data_years = cfg["year"]
        [get_data(data_years[i]) for i in range(len(data_years))]
        
        # make VoD data
        [get_veil(data_years[i]) for i in range(len(data_years))]
        [build_intertw(data_years[i]) for i in range(len(data_years))]
        
        
    # make the test target
    #if 'test' in targets:
        cfg = load_params(TEST_DATA_PARAMS)
        test_year = cfg["year"][0]
        get_data_test(test_year)
        
        # for the test files, since they are only ~10 lines there is not enough data for the veil of darkness data to be made
    
    # jupyter nbconvert --no-input --no-prompt 03-moore-final-project.ipynb    
        
if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
    