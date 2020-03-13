'''Model agnostic plots of the measured data
'''
from bact2.applib.bba.bpm_plots import process_quadrupoles
from bact2.applib.transverse_lib.process_plots import main_func


def main():
    main_func(process_kicker_func=process_quadrupoles,
              column_with_kicker_name='mux_selector_selected')


if __name__ == '__main__':
    main()
