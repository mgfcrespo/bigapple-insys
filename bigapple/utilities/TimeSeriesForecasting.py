"""
- exponential smoothing (SES/HWES)
- moving averages (ARIMA)
- time series decomposition
BY MONTH, PROJECT 1 MONTH AHEAD
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn import linear_model
from sklearn.metrics import mean_squared_error
from math import sqrt
from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
import warnings
warnings.filterwarnings("ignore")

# create dataframe with relevant columns
# aggregate at monthly/level
# forecast functions takes df with date and qty column


def aggregate_by_day(df):
    df.Timestamp = pd.to_datetime(df[df.columns[0]], format='%d-%m-%Y %H:%M')
    df.index = df.Timestamp
    df = df.resample('D').mean()
    return df


# Given a df with date and qty columns, output test df containing space for data 1 month after train df
def create_split(df):
    # train_length = (len(df))
    split_start = df.tail(1).index.values[0]
    split_start += np.timedelta64(1, 'D')
    month_starts = pd.date_range(start=split_start, periods=31, freq='D')
    # THIS TOOK SO LONG TO SOLVE HUHU
    # print(month_starts)
    return month_starts


def forecast_decomposition(df):
    train = aggregate_by_day(df)
    sm.tsa.seasonal_decompose(train.Count).plot()
    plt.show()
#     TODO: use plotly.plot_mpl(fig) to display matplotlib figs in html


def forecast_ses(df):
    train = aggregate_by_day(df)
    test = train.copy()
    test = test.reindex(create_split(train))
    y_hat_avg = test.copy()
    fit2 = SimpleExpSmoothing(np.asarray(train['Count'])).fit(smoothing_level=0.6, optimized=False)
    y_hat_avg['SES'] = fit2.forecast(len(test))
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['SES'], label='SES')
    plt.legend(loc='best')
    # plt.show()
    # print(y_hat_avg['SES'].iloc[0])
    # get max y value and index (x)
    date_projected = str(y_hat_avg['SES'].idxmax())
    qty_projected = str(int(y_hat_avg.loc[y_hat_avg['SES'].idxmax(), 'SES']))
    result = [date_projected, qty_projected]
    return result


def forecast_hwes(df):
    train = aggregate_by_day(df)
    test = train.copy()
    test = test.reindex(create_split(train))
    y_hat_avg = test.copy()
    fit1 = ExponentialSmoothing(np.asarray(train['Count']), seasonal_periods=7, trend='add', seasonal='add',).fit()
    y_hat_avg['Holt_Winter'] = fit1.forecast(len(test))
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['Holt_Winter'], label='Holt Winter')
    plt.legend(loc='best')
    # plt.show()
    # get max y value and index (x)
    date_projected = str(y_hat_avg['Holt_Winter'].idxmax())
    qty_projected = str(int(y_hat_avg.loc[y_hat_avg['Holt_Winter'].idxmax(), 'Holt_Winter']))
    result = [date_projected, qty_projected]
    return result


def forecast_moving_average(df):
    train = aggregate_by_day(df)
    test = train.copy()
    test = test.reindex(create_split(train))
    y_hat_avg = test.copy()
    # gets the line showing moving average
    y_hat_avg['moving_avg_forecast'] = train['Count'].rolling(60).mean().iloc[-1]
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['moving_avg_forecast'], label='Moving Average Forecast')
    plt.legend(loc='best')
    # plt.show()
    # print(y_hat_avg['moving_avg_forecast'].iloc[0])
    # get max y value and index (x)
    date_projected = str(y_hat_avg['moving_avg_forecast'].idxmax())
    qty_projected = str(int(y_hat_avg.loc[y_hat_avg['moving_avg_forecast'].idxmax(), 'moving_avg_forecast']))
    result = [date_projected, qty_projected]
    return result


def forecast_arima(df):
    train = aggregate_by_day(df)
    test = train.copy()
    test = test.reindex(create_split(train))
    y_hat_avg = test.copy()
    fit1 = sm.tsa.statespace.SARIMAX(train.Count, order=(2, 1, 4), seasonal_order=(0, 1, 1, 7)).fit()  # FIXME why use sarimax
    y_hat_avg['SARIMA'] = fit1.predict(start="2013-11-1", end="2013-12-31", dynamic=True)  # FIXME don't hardcode dates rr
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['SARIMA'], label='SARIMA')
    plt.legend(loc='best')
    # plt.show()
    # get max y value and index (x)
    date_projected = str(y_hat_avg['SARIMA'].idxmax())
    qty_projected = str(int(y_hat_avg.loc[y_hat_avg['SARIMA'].idxmax(), 'SARIMA']))
    result = [date_projected, qty_projected]
    return result


# def main():
#     # get sample data
#     df = pd.read_csv(r'C:\Users\Dante\Downloads\Train.csv', nrows=10392)
#
#     df.drop(['ID'], axis=1, inplace=True)
#     # df.Timestamp = pd.to_datetime(df.Datetime, format='%d-%m-%Y %H:%M')
#
#     # aggregate by day
#     # df.index = df.Timestamp
#     # df = df.resample('D').mean()
#     # df = aggregate_by_day(df)
#     # train_length = (len(df))
#     # print(df.head())
#
#     # pandas.Index.shift to create Datetimeindex series of 1 month worth of days
#     # month_starts = pd.date_range(df.tail(1).index.values[0], periods=30, freq='D')
#     # print(month_starts)
#
#     # TODO: append series to new rows
#     # df = df.append(pd.DataFrame(index=month_starts))
#     #
#     # train = df[0:train_length]
#     # test = df[train_length:]
#
#     # train = aggregate_by_day(df)
#     # test = train.copy()
#     # test = test.reindex(create_split(train))
#
#     # print(train)
#
#     # print(forecast_ses(df))
#     # print(forecast_hwes(df))
#     # print(forecast_moving_average(df))
#     # print(forecast_arima(df))
#     # forecast_decomposition(df)
#
#
# if __name__ == '__main__':
#     main()
