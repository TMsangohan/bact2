from bact2.applib.bba import commons, process_dataframe as pr_df
from bact2.applib.transverse_lib.from_json_to_pickle import main_func


def main():

    bba_json = commons.json_file_name()
    pk_fn = commons.pickle_file_name()

    main_func(pr_df.ProcessedBPMData, bba_json, pk_fn)


if __name__ == '__main__':
    main()
