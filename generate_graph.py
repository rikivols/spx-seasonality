import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
import datetime
from calendar import monthrange
import time


class SpxData:

    def __init__(self, years):
        self.years = years
        nw = datetime.datetime.now()
        past = datetime.datetime(year=nw.year - self.years, month=nw.month, day=nw.day)
        self.df = self.download_spx(past, nw)

    @staticmethod
    def download_spx(start, end):
        return yf.download('^GSPC',
                           start=start,
                           end=end,
                           progress=False,
                           )

    @staticmethod
    def perc_increase(original, inc):
        # return inc / original
        return (inc - original) / original

    @staticmethod
    def calc_freq(incs):
        pos = 0
        for inc in incs.values:
            if inc > 0:
                pos += 1

        return pos / len(incs.values) * 100

    def get_last_close(self, yr, month=0):
        if month:
            if month == 1:
                yr -= 1
                month = 13
            day = monthrange(yr, month-1)[-1]
            start_str = f'{yr}-{month-1}-{day-3}'
            if month == 13:
                yr += 1
                month = 12
            end_str = f'{yr}-{month}-01'
        else:
            start_str = f'{yr-1}-12-27'
            end_str = f'{yr}-01-01'

        sp = self.download_spx(start_str, end_str)

        return sp.iloc[-1]['Adj Close']

    def prepare_graph(self):

        yearly_returns = {}
        last_close = self.get_last_close(self.df.index[0].year)

        for ind, row in self.df.iterrows():
            # get closing value of last year
            if ind.year not in yearly_returns:
                yearly_returns[ind.year] = {'original': last_close}
            last_close = row['Adj Close']

        self.df['increase'] = self.df.apply(lambda row: self.perc_increase(yearly_returns[row.name.year]['original'], row['Adj Close']), axis=1)

    def plot_seasonality(self):

        df_graph = self.df.groupby(self.df.index.strftime('%m-%d'))['increase'].mean()
        df_graph['01-01'] = 0
        df_graph = df_graph.sort_index()

        df_graph.index = pd.to_datetime(df_graph.index, format='%m-%d', errors='coerce')
        df_ma = df_graph.rolling(window=7).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_graph.index, y=df_graph.values, mode='lines', name='raw',
                                 line={'color': 'firebrick', 'width': 1, 'dash': 'dash'}))
        fig.add_trace(go.Scatter(x=df_ma.index, y=df_ma.values, mode='lines', name='MA',
                                 line={'color': 'blue', 'width': 2}))
        fig.update_layout(xaxis=dict(tickformat="%d-%B", nticks=12, gridcolor='LightPink'))
        fig.update_layout(yaxis=dict(tickformat=".1%"))
        fig.update_layout(title=f'Showing SPX cumulative performance over the last <b>{self.years} years</b>', title_x=0.5)

        return fig

    def prepare_averages(self):
        """
        Calculate monthly percentage gains (close price of previous month and current month) and the end of current month
        """
        tm = time.time()
        monthly_returns = {}
        last_close = self.get_last_close(self.df.index[0].year, self.df.index[0].month)

        self.df['last_month_day'] = 0
        for i in range(len(self.df) - 1):
            # get closing value of last year
            row = self.df.iloc[i]
            ind = row.name
            adj_close = row['Adj Close']

            if f'{ind.month}_{ind.year}' not in monthly_returns:
                monthly_returns[f'{ind.month}_{ind.year}'] = last_close

            if self.df.iloc[i + 1].name.month != ind.month:
                self.df.loc[ind, 'last_month_day'] = 1

            last_close = adj_close

        self.df['monthly_increase'] = self.df.apply(
            lambda row: self.perc_increase(monthly_returns[f'{row.name.month}_{row.name.year}'], row['Adj Close']), axis=1)
        self.df['daily_increase'] = self.perc_increase(self.df['Adj Close'].shift(1), self.df['Adj Close'])

    def process_group_data(self, df_grouped):
        df_monthly_avg = df_grouped['monthly_increase'].mean()
        df_monthly_max = df_grouped['monthly_increase'].max()
        df_monthhly_max_index = df_grouped['monthly_increase'].idxmax()
        df_monthhly_freq = df_grouped['monthly_increase'].apply(self.calc_freq)
        df = pd.concat([df_monthly_avg, df_monthly_max, df_monthhly_max_index, df_monthhly_freq], axis=1)
        df.columns = ['avg', 'max', 'max_date', 'freq']

        return df

    def prettify_tables(self, df, index_name):

        format_str = '%m' if index_name == 'Month' else '%m-%d'
        # df.index = pd.to_datetime(df.index, format=format_str).month_name().str.slice(stop=3)
        df = df.drop('02-29', axis=0, errors='ignore')
        df.index = pd.to_datetime(df.index, format=format_str).strftime(format_str.replace('m', 'b'))

        df.index.names = [index_name]
        df['avg'] = (df['avg'] * 100).round(2).astype(str) + '%'
        df['max'] = (df['max'] * 100).round(2).astype(str) + '% (' + df['max_date'].dt.year.astype(str) + ')'
        df['freq'] = (df['freq']).round(1).astype(str) + '%'
        df = df.drop(labels='max_date', axis=1)
        if index_name == 'Day': index_name = 'Dai'
        df.columns = [f'Average {index_name}ly % gain', f'Max {index_name}ly % gain', f'{index_name}ly gain frequency']

        return df

    def get_data(self):
        """ Calculate avg % return, win frequency and max return """

        df_monthly = self.df[self.df['last_month_day'] == 1]
        df_monthly = df_monthly.groupby(df_monthly.index.strftime('%m'))
        monthly_data = self.process_group_data(df_monthly)

        df_daily = self.df.groupby(self.df.index.strftime('%m-%d'))
        # print(df_daily)
        daily_data = self.process_group_data(df_daily)

        monthly_data = self.prettify_tables(monthly_data, 'Month')
        daily_data = self.prettify_tables(daily_data, 'Day')

        return monthly_data, daily_data


def main(years):

    st = time.time()
    s = time.time()
    sp = SpxData(years)
    sp.prepare_graph()

    fig = sp.plot_seasonality()
    sp.prepare_averages()
    monthly_data, daily_data = sp.get_data()

    # print('MONTHLY')
    # print(monthly_data)
    # print('DAILY')
    # print(daily_data)
    print('loop took:', round(time.time() - st, 2))

    return fig, monthly_data, daily_data


if __name__ == '__main__':
    years = 50
    fig = main(years)
    fig.show()