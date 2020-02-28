import bact2.pandas.dataframe.df_aggregate as dfg
from bact2.applib.utils import steerer as st_u, utils as m_u
from bact2.applib.response_matrix import bpm_data as bd, bpm_plots as bp
from bact2.applib.response_matrix import process_dataframe as pr_df

from bact2.applib.response_matrix import commons

import pandas as pd
import gzip
import pickle
import importlib

import logging
logging.basicConfig(level=logging.INFO)

importlib.reload(st_u)
importlib.reload(m_u)
importlib.reload(bd)
importlib.reload(bp)
importlib.reload(dfg)


def main():

    t_table = pd.read_json(commons.json_file_name())
    t_table = t_table.infer_objects().sort_index()

    nt = dfg.df_vectors_convert(t_table).sort_index()
    t_table = nt

    p = pr_df.ProcessedBPMData(t_table)
    p.processed_dataframe
    # p.measurement_fit_data

    # makefile_name = os.path.join(data_dir, 'plots.mk')
    # pickle_file_name, makefile_name

    with gzip.open(commons.pickle_file_name(), 'w') as fp:
        pickle.dump(p, fp)


if __name__ == '__main__':
    main()
