import pandas as pd
import numpy as np


def twiss_to_df(twiss):
    '''Store ocelot twiss parameter list in a dataframe

    Args:
        twiss : output of a twiss tabel

    Returns:
        dataframe : each row contains the twiss parameters
                    for one element
    '''
    tw = twiss[0]
    columns = list(filter(lambda n: n[:2] != '__', dir(tw)))
    indices = np.arange(len(twiss))
    df = pd.DataFrame(columns=columns, index=indices)
    for i in indices:
        tw = twiss[i]
        for elem in columns:
            df.at[i, elem] = getattr(tw, elem)
    df = df.infer_objects()
    return df
