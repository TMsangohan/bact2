import pandas as pd
import pickle
import importlib
import datetime

import sys
import datetime
import os
import gzip

bact2_dir = '/home/mfp/Devel/github'
if bact2_dir not in sys.path:
    sys.path.insert(0, bact2_dir)

#
# sys.path.append()

from bact2.applib.response_matrix import  bpm_plots as bp


importlib.reload(bp)


def prepare_for_queue(df, steerer_name, cnt):
    return one_steerer, cnt


pickle_file = '/home/mfp/Devel/github/data/response_matrix/preprocessed_steerer_response_data_tmp.bk.gz'


def main():
    target_file_name = sys.argv[1]

    file_name, ext = os.path.split(target_file_name)
    # preprocess the name
    tmp = target_file_name.split('_')
    steerer_name = tmp[2]

    print(f'Processing steerer {steerer_name}')

    start_timestamp = datetime.datetime.now()
    with gzip.open(pickle_file) as fp:
        df = pickle.load(fp)

    one_steerer = df.loc[df.sc_selected == steerer_name]
    preprocess_timestamp = datetime.datetime.now()
    dtp = preprocess_timestamp - start_timestamp

    bp.process_steerer(one_steerer, target_file_name = target_file_name)

    dt = datetime.datetime.now() - start_timestamp
    print(f'plotting steerer {steerer_name} required {dt}'
          f' out of that prepocessing required {dtp}')


if __name__ == '__main__':
    main()
