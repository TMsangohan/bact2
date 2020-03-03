from bact2.applib.response_matrix import commons
import os.path


def to_bba_dir(t_path):
    dir_n = os.path.dirname(t_path)

    t_dir = os.path.join(dir_n, os.path.pardir, 'bba')
    t_dir = os.path.normpath(t_dir)

    return t_dir


def json_file_name():

    t_path = commons.json_file_name()
    t_dir = to_bba_dir(t_path)
    json_file = 'bba_test2.json.bz2'
    t_path = os.path.join(t_dir, json_file)
    return t_path


def pickle_file_name():

    t_path = commons.pickle_file_name()
    t_dir = to_bba_dir(t_path)
    json_file = 'bba_test.pk.gz'
    t_path = os.path.join(t_dir, json_file)
    return t_path


def makefile_name():
    t_path = commons.makefile_name()
    t_dir = to_bba_dir(t_path)
    make_file = 'plots_bba.mk'
    t_path = os.path.join(t_dir, make_file)
    return t_path
