import bact2.pandas.dataframe.df_aggregate as dfg


import pandas as pd
import gzip
import pickle
import importlib

import logging
logging.basicConfig(level=logging.INFO)

def preprocess_table(t_table):
    t_table = t_table.infer_objects().sort_index()
    nt = dfg.df_vectors_convert(t_table).sort_index()
    return nt

def main_func(dataframe_filter_sink, json_file_name, pickle_file_name):

    t_table = pd.read_json(json_file_name)
    t_table = preprocess_table(t_table)

    p = dataframe_filter_sink(t_table)
    # Processes the data frame
    # All intermedidate steps are accessible
    p.processed_dataframe

    with gzip.open(pickle_file_name, 'w') as fp:
        pickle.dump(p, fp)
