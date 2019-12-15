import numpy as np
import pandas as pd
import json
import requests
from fbprophet import Prophet
from sklearn.metrics import mean_squared_error, mean_absolute_error
from datetime import date

def generate_api_call_times(start_time, interval_length, intervals):
    """
    Generates a list of times for which api calls can be requested
    based on a given start time, interval length and number of intervals.
    """
    api_times = [start_time]
    for interval in range(0, intervals):
        sample_time = api_times[-1] + interval_length
        api_times.append(sample_time)
    return api_times

def label_historicalType_and_precipType(api_json_data):
    """
    Function loops through the hourly records in the input
    json data to label the data as a historical 'type',
    and to populate the 'precipType' with 'none' if this
    key-value pair is not present, which occurs when there
    was no precipitation at that time.
    """
    data_records = api_json_data['hourly']['data']
    for record in data_records:
        record.update({'type': 'historical'})
        try:
            record.update({'precipType': record['precipType']})
        except:
            record.update({'precipType': 'none'})
    return data_records

def label_forecastType_and_precipType(api_json_data):
    """
    Function loops through the hourly records in the input
    json data to label the data as a historical 'type',
    and to populate the 'precipType' with 'none' if this
    key-value pair is not present, which occurs when there
    was no precipitation at that time.
    """
    data_records = api_json_data['hourly']['data']
    for record in data_records:
        record.update({'type': 'forecast'})
        try:
            record.update({'precipType': record['precipType']})
        except:
            record.update({'precipType': 'none'})
    return data_records

def api_dataframe_conversion(json_data, hourly_records, column_headers):
    """
    Function generates a dataframe from the hourly historical
    weather records for the given day and also provides
    locational and type (e.g. historical or forecast) designations.
    """
    data_frame = pd.DataFrame(hourly_records)
    data_frame['time'] = pd.to_datetime(data_frame['time'],unit='s')
    data_frame['latitude'] = json_data['latitude']
    data_frame['longitude'] = json_data['longitude']
    data_frame['timezone'] = json_data['timezone']
    data_frame = data_frame[column_headers]
    data_frame.set_index('time', inplace=True)
    return data_frame

def historical_dataframe_from_api_calls(list_of_times, url_base, api_key, location):
    """
    Function loops through the list of times provided and
    returns a dataframe with hourly data from the date when
    each time occurs.
    """
    # initializing the final dataframe
    column_headers = ['time', 'latitude', 'longitude', 'timezone', 'type', 'summary', 'icon',
                      'precipIntensity', 'precipProbability', 'precipType', 'temperature',
                      'apparentTemperature', 'dewPoint', 'humidity', 'pressure', 'windSpeed',
                      'windGust', 'windBearing', 'cloudCover', 'uvIndex', 'visibility']
    historical_data_frame = pd.DataFrame(columns=column_headers)
    historical_data_frame.set_index('time', inplace=True)
    # looping through the list of times
    for time in list_of_times:
        url = url_base+api_key+'/'+location+','+str(time)+'?exclude=currently,minutely,daily,alerts,flags'
        response = requests.get(url)
        data = response.json()
        hourly_data = label_historicalType_and_precipType(data)
        time_data_frame = api_dataframe_conversion(data, hourly_data, column_headers)
        historical_data_frame = historical_data_frame.append(time_data_frame, sort=False)
    return historical_data_frame

def forecast_dataframe_from_api_calls(list_of_times):
    """
    Function loops through the list of times provided and
    returns a dataframe with hourly data from the date when
    each time occurs.
    """
    # initializing the final dataframe
    column_headers = ['time', 'latitude', 'longitude', 'timezone', 'type', 'summary', 'icon',
                      'precipIntensity', 'precipProbability', 'precipType', 'temperature',
                      'apparentTemperature', 'dewPoint', 'humidity', 'pressure', 'windSpeed',
                      'windGust', 'windBearing', 'cloudCover', 'uvIndex', 'visibility']
    forecast_data_frame = pd.DataFrame(columns=column_headers)
    forecast_data_frame.set_index('time', inplace=True)
    # looping through the list of times
    for time in list_of_times:
        url = url_base+api_key+'/'+location+','+str(time)+'?exclude=currently,minutely,daily,alerts,flags'
        response = requests.get(url)
        data = response.json()
        hourly_data = label_forecastType_and_precipType(data)
        time_data_frame = api_dataframe_conversion(data, hourly_data, column_headers)
        forecast_data_frame = forecast_data_frame.append(time_data_frame, sort=False)
    return forecast_data_frame

def is_peak(time_info_row):
    """
    Encodes a given hour as Peak or Off-Peak per PJM/NERC published standards.
    Per published standards:
    weekdays from hour 7 through 22 are Peak and all others are Off-Peak
    with specific NERC holidays treated as entirely Off-Peak as well.
    Row of data must be from a DataFrame that includes these datetime columns:
    'date', 'dayofweek', 'hour'.
    """
    nerc_holidays = [date(2017, 1, 2),
                     date(2017, 5, 29),
                     date(2017, 7, 4),
                     date(2017, 9, 4),
                     date(2017, 11, 23),
                     date(2017, 12, 25),
                     date(2018, 1, 1),
                     date(2018, 5, 28),
                     date(2018, 7, 4),
                     date(2018, 9, 3),
                     date(2018, 11, 22),
                     date(2018, 12, 25),
                     date(2019, 1, 1),
                     date(2019, 5, 27),
                     date(2019, 7, 4),
                     date(2019, 9, 2),
                     date(2019, 11, 28),
                     date(2019, 12, 25),
                     date(2020, 1, 1),
                     date(2020, 5, 25),
                     date(2020, 7, 4),
                     date(2020, 9, 7),
                     date(2020, 11, 26),
                     date(2020, 12, 25)]
    if time_info_row['date'] in nerc_holidays:
        return 0
    elif time_info_row['dayofweek'] >= 5:
        return 0
    elif (time_info_row['hour'] == 23) or (time_info_row['hour'] <= 6):
        return 0
    else:
        return 1

def encode_circular_time(data, col):
    """
    Creates sin/cos circular time for a given type of time (hour, day of week, etc)
    to allow for regression on time metrics
    using Linear Regression or Decision Tree models as opposed to Prophet.
    """
    max_val = data[col].max()
    data[col + '_sin'] = round(np.sin(2 * np.pi * data[col]/max_val),6)
    data[col + '_cos'] = round(np.cos(2 * np.pi * data[col]/max_val),6)
    return data

def mean_abs_pct_err(y_true, y_pred): 
    """
    Calculates Mean Absolute Percent Error (MAPE)
    given actual target values (y_true) and predicted values (y_pred)
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def print_metrics(y_true, y_pred):
    """
    Prints mean squared error, mean absolute error and MAPE
    given actual target values (y_true) and predicted values (y_pred)
    """
    print('MSE: ', round(mean_squared_error(y_true, y_pred),2))
    print('MAE: ', round(mean_absolute_error(y_true, y_pred),2))
    print('MAPE: ', round(mean_abs_pct_err(y_true, y_pred),2),'%')

def init_prophet_model(regressors=[], holidays=False, model=Prophet()):
    """
    Initializes a prophet model.
    Adds regressors from a list of column names to be used as regressors.
    Includes holidays if holidays=True
    """
    # m = model
    if len(regressors) > 0:
        for reg in regressors:
            model.add_regressor(reg)
    if holidays == True:
        model.add_country_holidays(country_name='US')
    return model

def prophet_df(df, time, target, regressors=[]):
    """
    Prepares dataframe of the time series, target and regressors
    in the format required by Prophet.
    """
    df_prep = df.rename(columns={time: 'ds', target: 'y'})
    df_prep = df_prep[['ds', 'y']+regressors]
    return df_prep

def create_poly_feat(data, list_of_cols, poly_names):
    """
    Adds a polynomial feature to the data
    for each column in the provided list of columns.
    Names of resulting polynomial columns must be passed.
    """
    for ix, col in enumerate(list_of_cols):
        data[poly_names[ix]] = data[col] * data[col]
    return data
        
def create_interact_feat(data, list_of_tuples, interact_names):
    """
    Adds an interaction feature to the data
    for each tuple of columns in the provided list of tuples.
    Names of resulting interaction columns must be passed.
    """
    for ix, tup in enumerate(list_of_tuples):
        data[interact_names[ix]] = data[tup[0]] * data[tup[1]]
    return data