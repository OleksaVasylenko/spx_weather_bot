#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

token = '5d7725ba7c3d981727e35fac758ba72d'
url = 'http://api.openweathermap.org/data/2.5/weather'
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


def owm_to_summary(data):
    result = {
        'cod': data['cod'],
        'icon': icon_to_emoji(data['weather'][0]['icon']),
        'name': data['name'],
        'temp': data['main']['temp'],
        'condition': data['weather'][0]['description'].capitalize(),
        'humidity': data['main']['humidity'],
        'pressure': data['main']['pressure'],
        'wind_s': data['wind']['speed'],
        'wind_d': wind_dir(data['wind']['deg']),
        'cloudiness': data['clouds']['all']
    }
    summary = (
            'Current weather in <b>{}</b> is:\n'
            '{} {}, Temp: <strong>{:.1f}</strong> °C\n'
            'Humidity: {}%; Pressure {} hPa\n'
            'Wind: {} m/s, {}'
        ).format(result['name'], result['icon'], result['condition'],
                 result['temp'], result['humidity'],
                 result['pressure'], result['wind_s'],
                 result['wind_d'])
    return summary


def curr_weather(location):
    if type(location) == str:
        params['q'] = location
    elif type(location) == tuple:
        params['lat'] = location[0]
        params['lon'] = location[1]
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return owm_to_summary(data)
    return 'Oops'


if __name__ == '__main__':
    print(curr_weather('Kiev,UA'))
