'''Generates make file to generate the different plots
'''
from bact2.applib.bba import commons
from bact2.applib.transverse_lib.plots_makefile import main_func


def main():
    pickle_file_name = commons.pickle_file_name()
    main_func(makefile_name=commons.makefile_name(),
              pickle_file_name=pickle_file_name,
              column_with_kicker_name='mux_selector_selected',
              app_dir='bba',
              plots_dir='plots_bba')


if __name__ == '__main__':
    main()
