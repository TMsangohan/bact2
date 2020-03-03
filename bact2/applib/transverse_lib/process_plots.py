'''Model agnostic plots of the measured data
'''
import gzip
import pickle
import datetime
import os
import sys


def main_func(process_kicker_func=None, column_with_kicker_name=None):

    assert(column_with_kicker_name is not None)
    assert(process_kicker_func is not None)

    pickle_file = sys.argv[1]
    target_file_path = sys.argv[2]

    target_file_name = os.path.basename(target_file_path)
    plot_dir = os.path.dirname(target_file_path)
    file_name, ext = os.path.split(target_file_name)

    # preprocess the name
    tmp = target_file_name.split('_')
    kicker_name = tmp[2]

    print(f'Processing kicker {kicker_name}')

    start_timestamp = datetime.datetime.now()

    with gzip.open(pickle_file) as fp:
        obj = pickle.load(fp)

    df = obj.processed_dataframe
    t_kicker_col = df.loc[:, column_with_kicker_name]
    one_steerer = df.loc[t_kicker_col == kicker_name]

    preprocess_timestamp = datetime.datetime.now()
    dtp = preprocess_timestamp - start_timestamp

    process_kicker_func(one_steerer, plot_dir=plot_dir,
                        target_file_name=target_file_name)

    dt = datetime.datetime.now() - start_timestamp
    print(f'plotting kicker {kicker_name} required {dt}'
          f' out of that prepocessing required {dtp}')


if __name__ == '__main__':
    main()
