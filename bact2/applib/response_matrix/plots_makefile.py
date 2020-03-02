'''Generates make file to generate the different plots
'''
import bact2
from bact2.applib.response_matrix import commons
import gzip
import pickle
import io
import os.path

#: Header of make file
header = '''# Automatic generated file

PYTHON3 = python3
SCRIPT_DIR=${BACT2_DIR}/applib/response_matrix
SCRIPT_NAME=${SCRIPT_DIR}/process_plots.py
SCRIPT_NAME_FIT=${SCRIPT_DIR}/process_model_fits.py
PLOT_DIR = plots_tmp

'''


def create_target_dependency_list(target_name, t_list):
    sep = ' \\\n    '
    build_deps = sep.join(t_list)
    txt = f'{target_name} : {build_deps}\n\n'
    return txt


def main():

    pickle_file_name = commons.pickle_file_name()
    with gzip.open(pickle_file_name) as fp:
        obj = pickle.load(fp)
    df = obj.dataframe
    steerer_names = df.sc_selected
    steerer_names = set(steerer_names)

    bact2_dir = os.path.dirname(bact2.__file__)
    buf = io.StringIO()
    buf.write(header)

    print(f'Using pickle stored in {pickle_file_name}')
    # Put scripts to proper place
    buf.write(f'BACT2_DIR={bact2_dir}\n')
    buf.write(f'PICKLE_FILE={pickle_file_name}\n\n')
    buf.write('all : all_files_agnostic all_files_fit\n')
    buf.write('all_files_fit : all_files_fit_1d all_files_fit_2d\n\n')

    all_files_agnostic = []
    all_files_fit_1d = []
    all_files_fit_2d = []

    cnt = 0
    for name in steerer_names:
        cnt += 1
        horizontal = name[0] == 'h'
        if horizontal:
            suffix = 'x'
        else:
            suffix = 'y'

        # the agnostic fits
        target_file = ('${PLOT_DIR}/' +
                       f'pltm_{cnt:03d}_{name}_main_{suffix}.pdf')
        all_files_agnostic.append(target_file)
        buf.write(f'{target_file}' + ' : ${PICKLE_FILE}\n')
        buf.write('\t${PYTHON3} ${SCRIPT_NAME} $< $@ \n\n')

        # the model fits
        target_file = ('${PLOT_DIR}/' +
                       f'pltfit_{cnt:03d}_{name}_1d_{suffix}.pdf')
        all_files_fit_1d.append(target_file)
        buf.write(f'{target_file}' + ' : ${PICKLE_FILE}\n')
        buf.write('\t${PYTHON3} ${SCRIPT_NAME_FIT} $< $@ \n\n')

        # the model fits
        target_file = ('${PLOT_DIR}/' +
                       f'pltfit_{cnt:03d}_{name}_2d_{suffix}.pdf')
        all_files_fit_2d.append(target_file)
        buf.write(f'{target_file}' + ' : ${PICKLE_FILE}\n')
        buf.write('\t${PYTHON3} ${SCRIPT_NAME_FIT} $< $@ \n\n')

    txt = create_target_dependency_list('all_files_agnostic', all_files_agnostic)
    buf.write(txt)
    txt = create_target_dependency_list('all_files_fit_1d', all_files_fit_1d)
    buf.write(txt)
    txt = create_target_dependency_list('all_files_fit_2d', all_files_fit_2d)
    buf.write(txt)
    buf.write('\n\n#EOF\n')

    buf.seek(0)

    makefile_name = commons.makefile_name()
    print(f'Writing makefile to  {makefile_name}')
    with open(makefile_name, 'wt') as fp:
        fp.write(buf.read())


if __name__ == '__main__':
    main()
