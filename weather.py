#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from config import owm_token
from time import localtime, strftime
import requests

token = owm_token
url = 'http://api.openweathermap.org/data/2.5/'
params = {'units': 'metric', 'appid': token}


def wind_dir(az) -> str:
    """
    Converts azimuth to visual definition of wind direction (uncomment other list to verbal)
    """
    # dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
    dirs = ['⬇️', '↙️', '⬅️', '↖️', '⬆️', '↗️', '➡️', '↘️', '⬇️']
    pointer = round(az / 45)
    return dirs[pointer]


def icon2emoji(icon):
    """
    Converts OWM`s weather icon code to corresponding emoji
    """
    emoji = {'01': '☀️️', '02': '🌤️', '03': '☁️️', '04': '⛅', '09': '🌧️',
             '10': '🌦️', '11': '🌩️', '13': '❄️️', '50': '🌫️'}
    icon = icon[:-1]
    return emoji[icon]


def hpa2mmhg(pressure):
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
        summary  = 'Current weather in <b>{}</b> is:\n'.format(data['name'])
        summary += '{} {}, Temp: <b>{:.1f}</b>° C\n'.format(
            icon2emoji(data['weather'][0]['icon']),
            data['weather'][0]['description'].capitalize(),
            data['main']['temp'])
        summary += 'Humidity: {}%; Pressure: {} mmHg\n'.format(
            data['main']['humidity'], hpa2mmhg(data['main']['pressure']))
        summary += 'Wind: {} m/s, {}\n'.format(data['wind']['speed'],
                                               wind_dir(data['wind']['deg']))
        summary += 'Sunrise: {}; Sunset: {}'.format(
                 strftime('%H:%M', localtime(data['sys']['sunrise'])),
                 strftime('%H:%M', localtime(data['sys']['sunset'])))
        return summary
    # if response_then.status_code == 200:
    #     data_t = response_now.json()
    #     for day in data_t['list']:
    #         date = day['dt_txt'].split()[0]
    return 'Oops! Something is wrong with weather source. Try again later.'


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
                   'Night:   {} {:.1f} — {:.1f}° С\n'
                   'Morning: {} {:.1f} — {:.1f}° С\n'
                   'Noon:    {} {:.1f} — {:.1f}° C\n'
                   'Evening: {} {:.1f} — {:.1f}° C\n')
        values = []
        for entry in data['list']:
            f_date = int(entry['dt_txt'][8:10])
            if f_date == tomorrow:                  # get only tomorrow forecast among others
                f_hour = int(entry['dt_txt'][11:13])
                if f_hour % 2 == 0:                 # get icon code for even hours only
                    values.append(icon2emoji(entry['weather'][0]['icon']))
                values.append(entry['main']['temp'])
        return summary.format(*values)
    return 'Oops! Something is wrong with weather source. Try again later.'


if __name__ == '__main__':
    print(today_weather(input('City?')))
