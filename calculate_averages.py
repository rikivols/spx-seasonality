from generate_graph import get_market_data, get_last_year_close, perc_increase
import time
import pandas as pd


# get monthly, weekly, daily avg


def get_monthly_avg(df):
    """
    Calculate monthly percentage gains (close price of previous month and current month) and the end of current month
    """

    monthly_returns = {}
    print(df.index[0].year, df.index[0].month)
    last_close = get_last_year_close(df.index[0].year, df.index[0].month)
    print('last close:', last_close)
    df['last_month_day'] = 0
    for i in range(len(df) - 1):
        # get closing value of last year
        row = df.iloc[i]
        ind = row.name
        adj_close = row['Adj Close']

        if f'{ind.month}_{ind.year}' not in monthly_returns:
            monthly_returns[f'{ind.month}_{ind.year}'] = last_close

        if df.iloc[i+1].name.month != ind.month:
            df.loc[ind, 'last_month_day'] = 1

        last_close = adj_close

    df['monthly_increase'] = df.apply(lambda row: perc_increase(monthly_returns[f'{row.name.month}_{row.name.year}'], row['Adj Close']), axis=1)
    df['daily_increase'] = (df['Adj Close'] - df['Adj Close'].shift(1)) / df['Adj Close']
    print('YOOOO')
    print(df['daily_increase'])

    return df, monthly_returns


def calc_freq(incs):
    pos = 0
    for inc in incs.values:
        if inc > 0:
            pos += 1

    return pos / len(incs.values) * 100


def get_period_data(df_grouped):
    df_monthly_avg = df_grouped['monthly_increase'].mean()
    df_monthly_max = df_grouped['monthly_increase'].max()
    df_monthhly_max_index = df_grouped['monthly_increase'].idxmax()
    df_monthhly_freq = df_grouped['monthly_increase'].apply(calc_freq)
    df = pd.concat([df_monthly_avg, df_monthly_max, df_monthhly_max_index, df_monthhly_freq], axis=1)
    df.columns = ['avg', 'max', 'max_date', 'freq']

    return df


def group_data(df, monthly_returns):
    """ Calculate avg % return, win frequency and max return """

    df_monthly = df[df['last_month_day'] == 1]
    df_monthly = df_monthly.groupby(df_monthly.index.strftime('%m'))
    get_period_data(df_monthly)
    quit()
    df_monthly_avg = df_monthly['monthly_increase'].mean()
    df_monthly_max = df_monthly['monthly_increase'].max()
    df_monthhly_max_index = df_monthly['monthly_increase'].idxmax()
    df_monthhly_freq = df_monthly['monthly_increase'].apply(calc_freq)

    print('AVG:', df_monthly_avg)
    print('MAX:', df_monthly_max)
    print('INDEX:', df_monthhly_max_index)
    print('FREQ:', df_monthhly_freq)

    # df_daily = df_monthly.groupby(df_monthly.index.strftime('%m-%d'))


if __name__ == '__main__':
    st = time.time()
    years = 20
    sp = get_market_data(years)
    df, monthly_returns = get_monthly_avg(sp)
    group_data(df, monthly_returns)
    print(time.time() - st)