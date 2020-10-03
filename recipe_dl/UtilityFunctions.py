#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

def url2domain(url):
    """ Returns domain portion of URL """

    domain = re.sub('/.*$', '', re.sub('[^/]*//', '', url.rstrip()))
    return domain

def url2publisher(url):
    """ Extracts a human readable Publisher name from a URL """

    domain = url2domain(url)
    if domain == 'www.americatestkitchen.com':
        publisher = "America's Test Kitchen"
    elif domain == 'www.cookscountry.com':
        publisher = "Cook's Country"
    elif domain == 'www.cooksillustrated.com':
        publisher = "Cook's Illustrated"
    elif domain == 'www.epicurious.com':
        publisher = "Epicurious"
    elif domain == 'www.bonappetit.com':
        publisher = "Bon Appetit"
    elif domain == 'www.foodnetwork.com':
        publisher = "Food Network"
    elif domain == 'cooking.nytimes.com':
        publisher = "New York Times"
    elif domain == 'www.food.com':
        publisher = "Food.com"
    elif domain == 'www.saveur.com':
        publisher = "Saveur"
    elif domain == 'www.allrecipes.com':
        publisher = "AllRecipes"
    else:
        publisher = ""

    return publisher

def json_clean_value(json_obj, key, default=''):
    """ Searches for key in JSON and returns value """

    return_value = default

    if key in json_obj:
        if json_obj[key] == None:
            return_value = ''
        else:
            return_value = json_obj[key]
            if type(return_value) == str:
                return_value = strip_tags(return_value.strip())

    return return_value

def strip_tags(str, strip_newline = False):
    """ strips string of html tags """

    #from html import unescape

    ret_value = str
    #ret_value = unescape(ret_value)
    ret_value = ret_value.replace(u'’', u"'")
    ret_value = ret_value.replace('\xa0', ' ')
    ret_value = re.sub('<[^>]*>', '', ret_value)
    ret_value = re.sub('\&nbsp\;', ' ', ret_value)
    ret_value = re.sub('\&\#8217\;', '\'', ret_value)
    ret_value = re.sub('\&\#39\;', '\'', ret_value)
    ret_value = re.sub('\&frac14\;', '1/4', ret_value)
    ret_value = re.sub('\&frac12\;', '1/2', ret_value)
    ret_value = re.sub('\&frac34\;', '3/4', ret_value)
    ret_value = re.sub('\&frac13\;', '1/3', ret_value)
    ret_value = re.sub('\&frac23\;', '2/3', ret_value)
    ret_value = ret_value.replace(u"¼", u" 1/4")
    ret_value = ret_value.replace(u"½", u" 1/2")
    ret_value = ret_value.replace(u"¾", u" 3/4")
    ret_value = ret_value.replace(u"⅓", u" 1/3")
    ret_value = ret_value.replace(u"⅔", u" 2/3")
    ret_value = ret_value.replace(u"Â", u" ")
    ret_value = re.sub('\r', '', ret_value)
    ret_value = re.sub('\t', ' ', ret_value)
    if strip_newline:
        ret_value = re.sub('\n', ' ', ret_value)
    ret_value = re.sub(' \/\/ ', ' / ', ret_value)
    ret_value = re.sub('\)\)', ')', ret_value)
    ret_value = re.sub('\(\(', '(', ret_value)
    ret_value = re.sub(r'\s+', ' ', ret_value)
    return ret_value.strip()
