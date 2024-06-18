# functions.py
import pandas as pd
import matplotlib.pyplot as plt
from pmdarima import auto_arima
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
import statsmodels.api as sm

def test_stationarity(timeseries):
    dftest = adfuller(timeseries, autolag='BIC')
    return dftest[1]

def make_stationary(timeseries):
    p_value = test_stationarity(timeseries)
    d = 0
    while p_value > 0.05:
        timeseries = timeseries.diff().dropna()
        p_value = test_stationarity(timeseries)
        d += 1
    return d

def load_data(file_path, column):
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    data_column = df[column]
    return data_column

def build_model(data_column):
    d = make_stationary(data_column)
    model = auto_arima(data_column, seasonal=False, trace=True, error_action='ignore', suppress_warnings=True, d=d, information_criterion='bic')
    model_fit = model.fit(data_column)
    return model_fit, d

def forecast_future(model_fit, data_column, n_periods=90):
    future_forecast_values = model_fit.predict(n_periods=n_periods)

    last_window = 30
    historical_fluctuations = data_column[-last_window:].pct_change().dropna()
    historical_std = historical_fluctuations.std()

    noise = np.random.normal(0, historical_std, n_periods) * future_forecast_values
    future_forecast_values_with_noise = future_forecast_values + noise

    last_date = data_column.index[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=n_periods, freq='D')

    model_stats = ARIMA(data_column, order=(model_fit.order[0], model_fit.order[1], model_fit.order[2])).fit()
    forecast_result = model_stats.get_forecast(steps=n_periods)
    future_forecast_ci = forecast_result.conf_int(alpha=0.05)

    future_forecast = {
        date: (value, ci[0], ci[1])
        for date, value, ci in zip(future_dates, future_forecast_values_with_noise, future_forecast_ci.values)
    }

    forecast_df = pd.DataFrame(
        [(date, value, ci_low, ci_high) for date, (value, ci_low, ci_high) in future_forecast.items()],
        columns=['Date', 'Forecast', 'Lower CI', 'Upper CI']
    )
    forecast_df.set_index('Date', inplace=True)

    in_sample_forecast = model_fit.predict_in_sample()

    combined_data = pd.concat([data_column, pd.Series(in_sample_forecast, index=data_column.index)], axis=1)
    combined_data.columns = ['Actual', 'In-sample Forecast']

    return combined_data, forecast_df, future_dates, future_forecast_values_with_noise, last_date

def plot_forecast(file_path, column, period):
    data_column = load_data(file_path, column)
    model_fit, d = build_model(data_column)
    combined_data, forecast_df, future_dates, future_forecast_values_with_noise, last_date = forecast_future(model_fit, data_column, n_periods=period)

    plt.figure(figsize=(18, 9))
    plt.plot(combined_data.index, combined_data['Actual'], label='Исходные данные', color='blue')
    plt.plot(combined_data.index, combined_data['In-sample Forecast'], label='Прогноз до последней даты', color='orange')
    plt.plot(future_dates, future_forecast_values_with_noise, label='Прогноз на будущее', color='green')
    plt.fill_between(forecast_df.index, forecast_df['Lower CI'], forecast_df['Upper CI'], color='green', alpha=0.2)
    plt.axvline(x=last_date, color='red', linestyle='--', label='Начало прогноза на будущее')
    plt.title(f'Прогноз с помощью модели ARIMA для столбца "{column}" с доверительным интервалом')
    plt.xlabel('Дата')
    plt.ylabel('Значение')
    plt.legend()
    plt.savefig('forecast_plot.png')
    plt.close()

def plot_time_series(file_path, column):
    data_column = load_data(file_path, column)

    plt.figure(figsize=(18, 9))
    plt.plot(data_column.index, data_column, label='Временной ряд', color='blue')
    plt.title(f'Временной ряд столбца "{column}"')
    plt.xlabel('Дата')
    plt.ylabel('Значение')
    plt.legend()
    plt.savefig('time_series_plot.png')
    plt.close()

def plot_residuals(file_path, column):
    data_column = load_data(file_path, column)
    model_fit, d = build_model(data_column)

    residuals = pd.DataFrame(model_fit.resid(), index=data_column.index)
    plt.figure(figsize=(18, 9))
    plt.plot(residuals, label='Остатки модели', color='blue')
    plt.title(f'Остатки модели ARIMA для столбца "{column}"')
    plt.xlabel('Дата')
    plt.ylabel('Остатки')
    plt.legend()
    plt.savefig('residuals_plot.png')
    plt.close()

def plot_acf_pacf(file_path, column):
    data_column = load_data(file_path, column)

    fig, axes = plt.subplots(2, 1, figsize=(12, 12))
    sm.graphics.tsa.plot_acf(data_column, lags=20, ax=axes[0])
    axes[0].set_title(f'Автокорреляционная функция (ACF) временного ряда для столбца "{column}"')
    sm.graphics.tsa.plot_pacf(data_column, lags=20, ax=axes[1])
    axes[1].set_title(f'Частичная автокорреляционная функция (PACF) временного ряда для столбца "{column}"')
    plt.tight_layout()
    plt.savefig('acf_pacf_plot.png')
    plt.close()

def make_graphic(filename, column, graphics_to_build, period=None):
    if '1' in graphics_to_build:
        plot_time_series(filename, column)
    if '2' in graphics_to_build and period:
        plot_forecast(filename, column, period)
    if '3' in graphics_to_build:
        plot_acf_pacf(filename, column)
    if '4' in graphics_to_build:
        plot_residuals(filename, column)
