#!/usr/bin/env python
# -*- coding: utf-8 -*-

def to_minutes( iso8601_duration ): """ Take iso8601 duration and returns minutes
        (rounded down to whole minute)
    """
    try:
        minutes = int(to_seconds(iso8601_duration)/60)
    except:
        minutes = 0
    return minutes

def to_seconds( iso8601_duration ):
    """ Take iso8601 duration and returns seconds """
    from re import findall

    def year(number):
        return number * 365 * 24 * 60 * 60

    def month(number):
        return number * 30 * 24 * 60 * 60 # Assumes 30 days

    def week(number):
        return number * 7 * 24 * 60 * 60

    def day(number):
        return number * 24 * 60 * 60

    def hour(number):
        return number * 60 * 60

    def minute(number):
        return number * 60

    def second(number):
        return number

    switcher = {
        'Y': year,
        'M': month,
        'W': week,
        'D': day,
        'H': hour,
        'm': minute,
        'S': second
    }

    if iso8601_duration[0] != 'P':
        raise ValueError('Not an ISO 8601 Duration string')
    seconds = 0
    # split by the 'T'
    for i, item in enumerate(iso8601_duration.split('T')):
        for number, unit in findall( '(?P<number>\d+)(?P<period>S|M|H|D|W|Y)', item ):
            # print '%s -> %s %s' % (d, number, unit )
            number = int(number)
            return_value = 0
            if unit == 'M' and i != 0:
                unit = 'm'
            func = switcher.get(unit, lambda: "Invalid ISO 8601 Duration string")
            seconds = seconds + func(number)
    return seconds

def tests():
    """ Run a number of tests on to_minutes and to_seconds """
    test_data = [
            {'iso8601': 'PT10M', 'minutes': 10, 'seconds': 600},
            {'iso8601': 'PT5H', 'minutes': (5*60), 'seconds': (5*60*60)},
            {'iso8601': 'P3D', 'minutes': (3*24*60), 'seconds': (3*24*60*60)},
            {'iso8601': 'PT45S', 'minutes': (0), 'seconds': (45)},
            {'iso8601': 'P8W', 'minutes': (8*7*24*60), 'seconds': (8*7*24*60*60)},
            {'iso8601': 'P7Y', 'minutes': (7*365*24*60), 'seconds': (7*365*24*60*60)},
            {'iso8601': 'PT5H10M', 'minutes': (5*60+10), 'seconds': ((5*60+10)*60)},
            {'iso8601': 'P2YT3H10M', 'minutes': ((((2*365*24)+3)*60)+10), 'seconds': (((((2*365*24)+3)*60)+10)*60)},
            {'iso8601': 'P3Y6M4DT12H30M5S', 'minutes': ((((((3*365)+(6*30)+4)*24)+12)*60)+30), 'seconds': (((((((3*365)+(6*30)+4)*24)+12)*60)+30)*60+5)},
            {'iso8601': 'P23M', 'minutes': (23*30*24*60), 'seconds': (23*30*24*60*60)},
            {'iso8601': 'P2Y', 'minutes': (2*365*24*60), 'seconds': (2*365*24*60*60)}
        ]
    for test in test_data:
        seconds = to_seconds( test['iso8601'] )
        minutes = to_minutes( test['iso8601'] )
        if seconds == test['seconds']:
            seconds_result='pass (' + str(seconds) + ')'
        else:
            seconds_result='fail (expected ' + str(test['seconds']) + ' returned ' + str(seconds) + ')'
        if minutes == test['minutes']:
            minutes_result='pass (' + str(minutes) + ')'
        else:
            minutes_result='fail (expected ' + str(test['minutes']) + ' returned ' + str(minutes) + ')'

        print ("iso8601 duration Test: %-16s \t to_seconds %-16s \t to_minutes %-16s" % (test['iso8601'], seconds_result, minutes_result))
