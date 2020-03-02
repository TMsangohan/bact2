import os.path


def data_dir():
    path = os.getcwd()
    walk = [os.path.pardir]*4 + ['data', 'response_matrix']
    data_dir = os.path.join(path, *walk)
    data_dir = os.path.normpath(data_dir)
    return data_dir


def json_file_name():
    d_dir = data_dir()
    json_name = os.path.join(d_dir, 'response_measurement.json.bz2')
    return json_name


def pickle_file_name():
    d_dir = data_dir()
    pickle_file_name = 'preprocessed_steerer_response_data_tmp.bk.gz'
    pickle_file_name = os.path.join(d_dir, pickle_file_name)
    return pickle_file_name


def makefile_name():
    return os.path.join(data_dir(), 'plots.mk')
