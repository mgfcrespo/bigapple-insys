"""
- exponential smoothing (SES/HWES)
- moving averages (ARIMA) (autoregressive?)
- time series decomposition
BY MONTH, PROJECT 1 MONTH AHEAD
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.metrics import mean_squared_error
from math import sqrt
import statsmodels.api as sm
from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
import warnings
warnings.filterwarnings("ignore")

# create dataframe with relevant columns
# aggregate at monthly/level
# forecast functions takes df with date and qty column


def forecast_decomposition(train):
    sm.tsa.seasonal_decompose(train.Count).plot()
    plt.show()
#     TODO: use plotly.plot_mpl(fig) to display matplotlib figs in html


def forecast_ses(train, test):
    y_hat_avg = test.copy()
    fit2 = SimpleExpSmoothing(np.asarray(train['Count'])).fit(smoothing_level=0.6, optimized=False)
    y_hat_avg['SES'] = fit2.forecast(len(test))
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['SES'], label='SES')
    plt.legend(loc='best')
    plt.show()
    print(y_hat_avg['SES'].iloc[0])


def forecast_hwes(train, test):
    y_hat_avg = test.copy()
    fit1 = ExponentialSmoothing(np.asarray(train['Count']), seasonal_periods=7, trend='add', seasonal='add',).fit()
    y_hat_avg['Holt_Winter'] = fit1.forecast(len(test))
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['Holt_Winter'], label='Holt Winter')
    plt.legend(loc='best')
    plt.show()
    print(y_hat_avg['Holt_Winter'])
    # print(y_hat_avg.loc[y_hat_avg['Holt_Winter'].idxmax()])  # gets max y value and index (x)
    print("Projected Date: " + str(y_hat_avg['Holt_Winter'].idxmax()))
    print("Projected Qty: " + str(y_hat_avg.loc[y_hat_avg['Holt_Winter'].idxmax(), 'Holt_Winter']))  # FIXME: formatting


def forecast_moving_average(train, test):
    y_hat_avg = test.copy()
    # gets the line showing moving average
    y_hat_avg['moving_avg_forecast'] = train['Count'].rolling(60).mean().iloc[-1]
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['moving_avg_forecast'], label='Moving Average Forecast')
    plt.legend(loc='best')
    plt.show()
    print(y_hat_avg['moving_avg_forecast'].iloc[0])


def forecast_arima(train, test):
    y_hat_avg = test.copy()
    fit1 = sm.tsa.statespace.SARIMAX(train.Count, order=(2, 1, 4), seasonal_order=(0, 1, 1, 7)).fit()  # FIXME why use sarimax
    y_hat_avg['SARIMA'] = fit1.predict(start="2013-11-1", end="2013-12-31", dynamic=True)  # FIXME don't hardcode dates rr
    plt.figure(figsize=(16, 8))
    plt.plot(train['Count'], label='Train')
    plt.plot(y_hat_avg['SARIMA'], label='SARIMA')
    plt.legend(loc='best')
    plt.show()


def main():
    df = pd.read_csv(r'C:\Users\Dante\Downloads\Train.csv', nrows=10392)

    df.drop(['ID'], axis=1, inplace=True)
    df.Timestamp = pd.to_datetime(df.Datetime, format='%d-%m-%Y %H:%M')
    df.index = df.Timestamp
    df = df.resample('D').mean()
    train_length = (len(df))

    # pandas.Index.shift to create Datetimeindex series of 1 month worth of days
    month_starts = pd.date_range(df.tail(1).index.values[0], periods=30, freq='D')
    # print(month_starts)

    # TODO: append series to new rows
    df = df.append(pd.DataFrame(index=month_starts))

    train = df[0:train_length]
    test = df[train_length:]

    forecast_hwes(train, test)
    # forecast_decomposition(train)


if __name__ == '__main__':
    main()
