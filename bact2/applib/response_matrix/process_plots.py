'''Model agnostic plots of the measured data
'''
from bact2.applib.response_matrix.bpm_plots import process_steerer
from bact2.applib.transverse_lib.process_plots import main_func


def main():
    main_func(process_kicker_func=process_steerer,
              column_with_kicker_name='sc_selected')


if __name__ == '__main__':
    main()
