from bact2.applib.response_matrix import commons
from bact2.applib.response_matrix import process_dataframe as pr_df
from bact2.applib.transverse_lib.from_json_to_pickle import main_func


def main():
    in_file = commons.json_file_name()
    out_file = commons.pickle_file_name()

    main_func(pr_df.ProcessedBPMData, in_file, out_file)


if __name__ == '__main__':
    main()
