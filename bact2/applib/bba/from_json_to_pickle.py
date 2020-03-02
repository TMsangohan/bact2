
from bact2.applib.response_matrix import commons
import bact2.pandas.dataframe.df_aggregate as dfg

from bact2.applib.bba import process_dataframe as pr_df

import pandas as pd
import gzip
import pickle
import importlib

import os.path
import logging
logging.basicConfig(level=logging.INFO)


def to_bba_dir(t_path):
    dir_n = os.path.dirname(t_path)

    t_dir = os.path.join(dir_n, os.path.pardir, 'bba')
    t_dir = os.path.normpath(t_dir)

    return t_dir

def to_bba_json_name(t_path):
    
    t_dir = to_bba_dir(t_path)
    json_file = 'bba_test2.json.bz2'
    t_path = os.path.join(t_dir, json_file)
    return t_path

def to_bba_pickle_name(t_path):

    t_dir = to_bba_dir(t_path)
    json_file = 'bba_test.pk.gz'
    t_path = os.path.join(t_dir, json_file)
    return t_path



def main():

    rp_mat_fn = commons.json_file_name()
    bba_fn = to_bba_json_name(rp_mat_fn)

    t_table = pd.read_json(bba_fn)
    t_table = t_table.infer_objects().sort_index()

    nt = dfg.df_vectors_convert(t_table).sort_index()
    t_table = nt
 

    p = pr_df.ProcessedBPMData(t_table)
    p.dataframe
    p.agg
    p.measurement_fit_data
    p.processed_dataframe


    # makefile_name = os.path.join(data_dir, 'plots.mk')
    # pickle_file_name, makefile_name

    pickle_file = to_bba_pickle_name(commons.pickle_file_name())
    with gzip.open(pickle_file, 'w') as fp:
        pickle.dump(p, fp)


if __name__ == '__main__':
    main()
