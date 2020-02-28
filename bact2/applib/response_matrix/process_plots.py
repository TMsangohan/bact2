'''Model agnostic plots of the measured data
'''
from bact2.applib.response_matrix import commons, bpm_plots as bp
import gzip, pickle, datetime, os, sys, importlib

importlib.reload(bp)


def main():
    pickle_file = sys.argv[1]
    target_file_path = sys.argv[2]

    target_file_name = os.path.basename(target_file_path)
    file_name, ext = os.path.split(target_file_name)

    # preprocess the name
    tmp = target_file_name.split('_')
    steerer_name = tmp[2]

    print(f'Processing steerer {steerer_name}')

    start_timestamp = datetime.datetime.now()

    with gzip.open(pickle_file) as fp:
        obj = pickle.load(fp)

    df = obj.processed_dataframe
    one_steerer = df.loc[df.sc_selected == steerer_name]
    preprocess_timestamp = datetime.datetime.now()
    dtp = preprocess_timestamp - start_timestamp

    bp.process_steerer(one_steerer, target_file_name=target_file_path)

    dt = datetime.datetime.now() - start_timestamp
    print(f'plotting steerer {steerer_name} required {dt}'
          f' out of that prepocessing required {dtp}')


if __name__ == '__main__':
    main()
