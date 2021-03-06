'''Generates make file to generate the different plots
'''
from bact2.applib.response_matrix import commons
from bact2.applib.transverse_lib.plots_makefile import main_func


def main():
    pickle_file_name = commons.pickle_file_name()
    main_func(makefile_name=commons.makefile_name(),
              pickle_file_name=pickle_file_name,
              column_with_kicker_name='sc_selected',
              app_dir='response_matrix',
              plots_dir='plots_response_matrix')


if __name__ == '__main__':
    main()
