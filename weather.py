#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from config import owm_token
import requests

token = owm_token
url = 'http://api.openweathermap.org/data/2.5/'
params = {'units': 'metric', 'appid': token}


def wind_dir(az) -> str:
    """
    Converts azimuth to verbal definition of wind direction
    """
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
    pointer = round(az / 45)
    return dirs[pointer]


def icon_to_emoji(icon):
    """
    Converts OWM`s weather icon code to corresponding emoji
    """
    emoji = {'01': '☀️️', '02': '🌤️', '03': '☁️️', '04': '⛅', '09': '🌧️',
             '10': '🌦️', '11': '🌩️', '13': '❄️️', '50': '🌫️'}
    icon = icon[:-1]
    return emoji[icon]


def hpa_to_mmhg(pressure):
    """
    Converts HectoPascals (hPa) to millimeters of mercury (mmHg)
    """
    return round(pressure / 1.33322, 1)


def today_weather(location, url=url):
    if type(location) == str:
        params['q'] = location
    elif type(location) == tuple:
        params['lat'] = location[0]
        params['lon'] = location[1]
    response_now = requests.get(url+'weather', params=params)
    # response_then = requests.get(url+'forecast', params=params)
    if response_now.status_code == 200:
        data = response_now.json()
        summary = (
            'Current weather in <b>{}</b> is:\n'
            '{} {}, Temp: <b>{:.1f}</b>° C\n'
            'Humidity: {}%; Pressure {} mmHg\n'
            'Wind: {} m/s, {}'
        ).format(data['name'], icon_to_emoji(data['weather'][0]['icon']),
                 data['weather'][0]['description'].capitalize(),
                 data['main']['temp'], data['main']['humidity'],
                 hpa_to_mmhg(data['main']['pressure']),
                 data['wind']['speed'], wind_dir(data['wind']['deg']))
        return summary
    # if response_then.status_code == 200:
    #     data_t = response_now.json()
    #     for day in data_t['list']:
    #         date = day['dt_txt'].split()[0]
    return 'Oops! Something went wrong with weather source. Try again later.'


def tomorrow_weather(location, date, url=url):
    if type(location) == str:
        params['q'] = location
    elif type(location) == tuple:
        params['lat'] = location[0]
        params['lon'] = location[1]
    response = requests.get(url+'forecast', params=params)
    if response.status_code == 200:
        data = response.json()
        tomorrow = date[2]
        summary = ('Weather for tomorrow is:\n'
                   'Night:   {} {:.1f}...{:.1f}° С\n'
                   'Morning: {} {:.1f}...{:.1f}° С\n'
                   'Noon:    {} {:.1f}...{:.1f}° C\n'
                   'Evening: {} {:.1f}...{:.1f}° C\n')
        values = []
        for entry in data['list']:
            f_date = int(entry['dt_txt'][8:10])
            if f_date == tomorrow:
                f_hour = int(entry['dt_txt'][11:13])
                if f_hour % 2 == 0:
                    values.append(icon_to_emoji(entry['weather'][0]['icon']))
                values.append(entry['main']['temp'])
        return summary.format(*values)
    return 'Oops! Something went wrong with weather source. Try again later.'


if __name__ == '__main__':
    print(today_weather(input('City?')))
