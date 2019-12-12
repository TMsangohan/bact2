import pandas as pd
import numpy as np
import datetime
import unittest

from bact2.pandas.dataframe.df_aggregate import df_with_vectors_mean


class TestAggregationNoOP(unittest.TestCase):
    '''Test that vector functions work even if no vectors are found
    '''

    def createDF(self):
        sel = np.arange(8) % 4
        data = np.arange(8) * 2
        df = pd.DataFrame(
            {
                'sel': sel,
                'data': data
            }
        )
        return df

    def checkDFAggMean(self, r):
        sel_ref = np.arange(4)
        check = r.sel == sel_ref

        data_ref = np.arange(4) * 2 + 4
        check = r.data == data_ref
        self.assertTrue(check.all())

    def test0_SimpleDataFrame(self):
        '''Test a data frame containing only one scalar
        '''

        df = self.createDF()
        r = df_with_vectors_mean(df, 'sel')
        self.checkDFAggMean(r)

    def test1_SimpleDataFrame(self):
        '''Test a data frame containing, only one scalar
        but with different object types

        '''
        df = self.createDF()
        df = df.infer_objects()
        r = df_with_vectors_mean(df, 'sel')
        r = r.infer_objects()
        self.checkDFAggMean(r)


class TestAggregation(unittest.TestCase):

    def createDF(self):
        sel = np.arange(4) % 2
        data = np.arange(4) * 2

        vec = np.arange(3) * 3 + 10
        vecs = [
            vec, vec/2, vec*3, -vec/2
        ]
        df = pd.DataFrame(
            {
                'sel': sel,
                'data': data,
                'vecs': vecs,
            }
        )
        return df

    def checkScalar(self, r):
        check = r.data == np.arange(2) * 2 + 2
        self.assertTrue(check.all())

    def checkNumVector(self, df, r):
        v = r.vecs.iat[0]
        v_check = df.vecs.iat[0]
        v_check = v_check * 4/2
        check = v == v_check
        self.assertTrue(check.all())

        v = r.vecs.iat[1]
        v_check = np.zeros(v.shape)
        check = v == v_check
        self.assertTrue(check.all())

    def test0(self):
        '''Test with one vector of floats
        '''
        df = self.createDF()
        r = df_with_vectors_mean(df, 'sel')
        self.checkScalar(r)
        self.checkNumVector(df, r)

    def test1(self):
        '''Test with a vector and datetime values
        '''

        df = self.createDF()

        now_val = datetime.datetime.now()
        now_val = np.datetime64(now_val)
        ts = pd.DatetimeIndex(start=now_val, freq='1s',
                              periods=len(df.index), name='time')
        df.loc[:, 'time'] = ts
        r = df_with_vectors_mean(df, 'sel')

        self.checkScalar(r)
        self.checkNumVector(df, r)

        dt = r.time - now_val
        self.assertEqual(dt[0], np.timedelta64(1, 's'))
        self.assertEqual(dt[1], np.timedelta64(2, 's'))

    def test2(self):
        '''Test with a vector and with strings
        '''

        df = self.createDF()

        names = ['n_{}'.format(i) for i in range(len(df.index))]
        df2 = pd.DataFrame(columns=['names'], index=df.index,
                           dtype=np.object)
        for i in df.index:
            df2.loc[:, 'names'].at[i] = names
        df.loc[:, 'names'] = df2.names

        r = df_with_vectors_mean(df, 'sel')
        self.checkScalar(r)
        self.checkNumVector(df, r)

        for i in r.index:
            check = r.at[i, 'names']
            self.assertEqual(check, names)

    def test3(self):
        '''Test with a vector and with strings
        '''

        df = self.createDF()

        names = ['n_{}'.format(i) for i in range(len(df.index))]
        df2 = pd.DataFrame(columns=['names'], index=df.index,
                           dtype=np.object)
        df2.loc[:, 'names'] = names
        df.loc[:, 'names'] = df2.names

        r = df_with_vectors_mean(df, 'sel')
        self.checkScalar(r)
        self.checkNumVector(df, r)

        for i in r.index:
            self.assertFalse(np.isfinite(r.at[i, 'names']))


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
