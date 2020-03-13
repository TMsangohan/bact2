import bact2.pandas.dataframe.df_aggregate as dfg


import pandas as pd
import gzip
import pickle
import importlib

import logging
logging.basicConfig(level=logging.INFO)


def main_func(dataframe_filter_sink, json_file_name, pickle_file_name):

    t_table = pd.read_json(json_file_name)
    t_table = t_table.infer_objects().sort_index()

    nt = dfg.df_vectors_convert(t_table).sort_index()
    t_table = nt

    p = dataframe_filter_sink(t_table)
    p.processed_dataframe
    # p.measurement_fit_data

    # makefile_name = os.path.join(data_dir, 'plots.mk')
    # pickle_file_name, makefile_name

    with gzip.open(pickle_file_name, 'w') as fp:
        pickle.dump(p, fp)
