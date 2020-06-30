#!/usr/bin/env python

import sys, os
import argparse

import requests

import re
import json

import iso8601

import textwrap

from CustomExceptions import Error, UrlError
from CustomPrint import print_info, print_debug, print_error, print_warning, print_to_console

from lxml import html
from bs4 import BeautifulSoup

__version__ = '0.1.0'
__author__ = u'Rodney Shupe'

def parse_arguments(print_usage = False, detail = False):
    """ Creates a new argument parser. """

    parser = argparse.ArgumentParser('recipe-dl')
    version = '%(prog)s ' + __version__
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=version
    )
    parser.add_argument(
        '-a',
        '--authorize',
        action="store_true",
        dest="authorize_ci",
        default=False,
        help='Force authorization of Cook Illustrated sites',
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="Add additional Output",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        dest="quiet",
        default=False,
        help="Suppress most output aka Silent Mode.",
    )
    parser.add_argument(
        "-j",
        "--output-json",
        action="store_true",
        dest="output_json",
        default=False,
        help="Output results in JSON format.",
    )
    parser.add_argument(
        "-m",
        "--output-md",
        action="store_true",
        dest="output_md",
        default=False,
        help="Output results in Markdown format.",
    )
    parser.add_argument(
        "-r",
        "--output-rst",
        action="store_true",
        dest="output_rst",
        default=False,
        help="Output results in reStructuredText format.",
    )
    parser.add_argument(
        '-i',
        '--infile',
        action="store",
        dest="infile",
        help="Specify input json file infile.",
    )
    parser.add_argument(
        '-o',
        '--outfile',
        action="store",
        dest="outfile",
        help="Specify output file outfile.",
    )
    parser.add_argument(
        "-s",
        "--save-to-file",
        action="store_true",
        dest="save_to_file",
        default=False,
        help="Save output file(s).",
    )
    parser.add_argument(
        "-f",
        "--force-recipe-scraper",
        action="store_true",
        dest="force_recipe_scraper",
        default=False,
        help="For the use of the recipe scraper where applicable.",
    )

    parser.add_argument('URL', nargs='*', action="append", default=[],)

    if print_usage:
        if detail:
            parser.print_help()
        else:
            parser.print_usage()
    else:
        args = parser.parse_args()

        if args.debug and args.quiet:
            args.quiet = False
            print_warning (args, "Debug option selected. Can not run in \"Silent Mode\"")

        filetype_count = 0
        if args.output_json:
            filetype_count += 1
        if args.output_md:
            filetype_count += 1
        if args.output_rst:
            filetype_count += 1

        print_debug(args, "filetype_count=%s" % filetype_count)
        if filetype_count == 0:
            args.output_rst = True
        elif filetype_count > 1:
            print_warning (args, "More than one output file type select. Assuming 'Save to File'")
            args.save_to_file = True

        if not args.save_to_file and not args.outfile is None and args.outfile != '':
            args.save_to_file = True

        return args

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
        publisher = "Bon Appétit"
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

def minutes2time(minutes = 0, default = 'TBD'):
    """ Takes minutes and returns a human friendly version """

    return_time = ''

    if minutes > 0:
        return_hours = int( minutes/60 )
        return_minutes = ( minutes - ( return_hours*60 ) )

        if return_hours > 0:
            return_time = str(return_hours)
            if return_hours > 1:
                return_time = return_time + ' hours '
            else:
                return_time = return_time + ' hour '
        if return_minutes > 0:
            return_time = return_time + str(return_minutes)
            if return_minutes > 1:
                return_time = return_time + ' minutes'
            else:
                return_time = return_time + ' minute'
    else:
        return_time = default

    return return_time

def json_find_key(dictionary, key):
    """ Finds a key and returns value(s) """

    for k, v in dictionary.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in json_find_key(v, key):
                yield result
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict):
                    for result in json_find_key(d, key):
                        yield result

def json_find_array_element(json_obj, key, value):
    """ Searches for key in JSON array and returns value """

    ret_value = None
    for array in json_obj:
        if array[key] == value:
            ret_value = array
            break
    return ret_value

def json_clean_value(json_obj, key, default=''):
    """ Searches for key in JSON and returns value """

    if key in json_obj:
        return_value=json_obj[key]
        if type(return_value) == str:
            return_value = strip_tags(return_value.strip())
    else:
        return_value=default
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
    ret_value = re.sub('\r', '', ret_value)
    ret_value = re.sub('\t', ' ', ret_value)
    if strip_newline:
        ret_value = re.sub('\n', ' ', ret_value)
    ret_value = re.sub(' \/\/ ', ' / ', ret_value)
    ret_value = re.sub('\)\)', ')', ret_value)
    ret_value = re.sub('\(\(', '(', ret_value)
    ret_value = re.sub(r'\s+', ' ', ret_value)
    return ret_value.strip()

def ci2json(args, url):
    """ Loads Cook's Illustrated (and affiliated) URL and checks for
        authentication and then builds Recipe JSON
    """

    def get_json(args, url):
        """ Get JSON from page """

        import pickle

        def find_script(source_html):
            if source_html is None:
                return None
            else:
                tree = html.fromstring(source_html)
                script_element = tree.xpath('//script[@id="__NEXT_DATA__"]')[0]
                return json.loads(script_element.text)

        def found_paywall(source_json):
            ret_value = False
            paywall_json = list(json_find_key(source_json, 'paywall'))

            if paywall_json or paywall_json[0] == 'TRUE' or json_clean_value(paywall_json[1], 'status') == "READY":
                ret_value = True

        def cookie_filename(url):
            return '.' + url2domain(url) + '.cookies'

        def save_cookies(requests_cookiejar, url):
            """ save cookie jar """
            print_debug (args, 'Saving cookies...')
            filename = cookie_filename(url)
            with open(filename, 'wb') as f:
                pickle.dump(requests_cookiejar, f)

        def load_cookies(url):
            """ Loads Cookie jar """
            print_debug (args, 'Loading cookies...')
            filename = cookie_filename(url)
            if os.path.isfile(filename):
                with open(filename, 'rb') as f:
                    return pickle.load(f)
            else:
                return None

        def get_credentials():
            """ Retrieve Credentals """

            def input_credential(prompt):
                """ Prompt and input credentals """
                credential = ''
                while credential == '':
                    print_to_console(prompt)
                    credential = input()
                return credential

            credential_json = {}
            credential_json['user'] = input_credential("Enter email address:")
            credential_json['pass'] = input_credential("Enter password:")

            return credential_json

        def get_page_using_cookie(args, url, cookies = None):
            """ Load page using existing cookies """

            print_debug (args, "Getting page using cookies...")

            recipe_page = None

            if cookies is None:
                #load cookies and do a request
                cookies = load_cookies(url)

            if not cookies is None:
                print_debug (args, 'cookies = ' + str(requests.utils.dict_from_cookiejar(cookies)))
                recipe_page = requests.get(url, cookies=cookies).text

            return recipe_page

        def get_page_using_session(args, url):

            print_debug (args, "Getting page using sessions...")

            auth_json = get_credentials()

            session_requests = requests.session()

            domain = url2domain(url)
            signin_url = "https://" + domain +"/sign_in?next=%2F"

            signin_page = session_requests.get(signin_url)
            tree = html.fromstring(signin_page.text)
            action = tree.xpath('//form[@class="appForm"]/@action')[0]

            payload={}
            input_elements = tree.xpath('//form[@class="appForm"]//input')
            for input_element in input_elements:
                payload[input_element.name] = input_element.value
            payload['utf8'] = '&#x2713;'
            payload['user[email]'] = auth_json['user']
            payload['user[password]'] = auth_json['pass']

            # Perform login
            authorize_url = "https://" + domain + action + "?next=%2F"
            result = session_requests.post(authorize_url, data = payload, headers = dict(referer = signin_url))

            save_cookies(session_requests.cookies, url)

            # Grab page
            recipe_page = session_requests.get(url, headers = dict(referer = url))

            return recipe_page.text

        raw_json = json.loads('{ "paywall": true }')
        if not args.authorize_ci:
            # Getting file using cookies
            raw_html = get_page_using_cookie(args, url)
            if not raw_html is None:
                raw_json = find_script(raw_html)

        if args.authorize_ci or raw_html is None or found_paywall(raw_json):
            'Getting page using full authentication'
            raw_html = get_page_using_session(args, url)
            raw_json = find_script(raw_html)

        raw_json = raw_json['props']['initialState']['content']['documents']
        raw_json = raw_json[list(json.loads(json.dumps(raw_json)))[0]]

        return raw_json

    print_debug(args, "Using Cook's Illustrated scraper...")
    recipe_json={}
    recipe_json['url'] = url

    source_json = get_json(args, url)

    if not source_json is None:
        recipe_json['title'] = json_clean_value(source_json, 'title')
        recipe_json['description'] = strip_tags(json_clean_value(source_json['metaData']['fields'], 'description'), strip_newline = True)
        recipe_json['yield'] = json_clean_value(source_json, 'yields')

        # Parse Times
        time_note = json_clean_value(source_json, 'recipeTimeNote')
        if time_note == '':
            time_note = 'TBD'
        recipe_json['preptime'] = ''
        recipe_json['cooktime'] = ''
        recipe_json['totaltime'] = time_note

        author = json_clean_value(source_json['metaData']['fields'], 'source')
        if author == '':
            author=domain2publisher(url)
        recipe_json['author'] = author

        # Ingredients
        recipe_json['ingredient_groups'] = []
        ingredient_groups = json_clean_value(source_json, "ingredientGroups")
        for group in ingredient_groups:
            group_json = json.loads('{"title":"","ingredients":[]}')
            if len(ingredient_groups) > 1:
                group_json['title'] = json_clean_value(group['fields'], 'title')
            ingredients = json_clean_value(group['fields'], "recipeIngredientItems")
            for ingredient in ingredients:
                qty  = json_clean_value(ingredient['fields'], "qty")
                unit  = json_clean_value(ingredient['fields'], "preText")
                item  = json_clean_value(json_clean_value(ingredient['fields'], "ingredient", json.loads('{"fields": ""}'))['fields'], 'title')
                modifier  = json_clean_value(ingredient['fields'], "postText")
                group_json['ingredients'].append(strip_tags("%s %s %s%s" % (qty, unit, item, modifier), strip_newline = True))
            recipe_json['ingredient_groups'].append(group_json)

        # Directions
        recipe_json['direction_groups'] = []
        group_json = json.loads('{"group":"","directions":[]}')
        steps = json_clean_value(source_json, "instructions")
        for step in steps:
            group_json['directions'].append(strip_tags(json_clean_value(step['fields'], "content"), strip_newline = True))
        recipe_json['direction_groups'].append(group_json)

        recipe_json['notes'] = []
        recipe_json['notes'].append(strip_tags(json_clean_value(source_json, 'headnote'), strip_newline = True))

    else:
        raise UrlError(url, 'URL not supported.')

    return recipe_json

def saveur2json(args, url):
    """ Loads Saveur URL and builds recipe JSON """

    print_debug(args, "Using Saveur scraper...")
    recipe_json={}
    recipe_json['url'] = url

    page = BeautifulSoup(requests.get(url).text.replace("\u2014"," "), 'html5lib')

    recipe_json['title'] = page.select_one('.article_title').text
    recipe_json['description'] = page.select_one('p.paragraph:first-child').text
    recipe_json['yield'] = page.select_one('div.yield span').text

    # Parse Times
    minutes_prep = 0
    minutes_cook = iso8601.to_minutes(page.select_one('div.cook-time meta')['content'])
    minutes_total = minutes_prep + minutes_cook
    if minutes_prep == 0 and minutes_total > 0 and minutes_cook > 0:
        minutes_prep = minutes_total - minutes_cook
    recipe_json['preptime'] = minutes2time(minutes_prep, '')
    recipe_json['cooktime'] = minutes2time(minutes_cook, '')
    recipe_json['totaltime'] = minutes2time(minutes_total)

    recipe_json['author'] = url2publisher(url)

    # Ingredients
    recipe_json['ingredient_groups'] = []
    recipe_json['ingredient_groups'].append(json.loads('{"title":"","ingredients":[]}'))
    for ingredient in page.find_all("li", class_="ingredient"):
        recipe_json['ingredient_groups'][0]['ingredients'].append(ingredient.text.replace("\n","").strip())

    # Directions
    out_instruction=[]
    for instruction in page.find_all("li", class_="instruction"):
        try:
            instruction_json = instruction
            out_instruction.append(instruction_json['text'].text.replace("\n","").strip())
        except:
            out_instruction.append(instruction.text.replace("\n","").strip())
    recipe_json['direction_groups'] = []
    recipe_json['direction_groups'].append(json.loads('{"group":"","directions":[]}'))
    recipe_json['direction_groups'][0]['directions'] = out_instruction
    #raise UrlError(url, 'URL not supported.')
    return recipe_json

def epicurious2json(args, url):
    """ Loads Epicurious URL and builds recipe JSON """

    def get_json(args, url):
        """ Find and load "standardized" json document containing recipe """
        return_value = None
        page = requests.get(url)

        page = BeautifulSoup(requests.get(url).text, 'html5lib')
        scripts = page.findAll('script')
        for script in scripts:
            match = re.search(r'root\.__INITIAL_STATE__\.store', script.text)
            if match:
                for line in iter(script.text.splitlines()):
                    match = re.search(r'root\.__INITIAL_STATE__\.store', line)
                    if match:
                        raw_json_text = re.sub('[^}]*$','', line)
                        raw_json_text = re.sub('^[^{]*', '', raw_json_text)
                        raw_json_text = re.sub('"email":{"regExp":.*,"password"', '"email":{"regExp":"","password"', raw_json_text)
                        raw_json_text = re.sub('"password":{"regExp":.*,"messages"', '"password":{"regExp":""},"messages"', raw_json_text)
                        raw_json = json.loads(raw_json_text)
                        return_value = json_clean_value(raw_json, 'content', json.loads('{}'))
                        #print_debug(args, json.dumps(return_value, indent=4))
        return return_value

    print_debug(args, "Using Epicurious scraper...")
    recipe_json={}
    recipe_json['url'] = url

    source_json = get_json(args, url)

    if not source_json is None:
        recipe_json['title'] = json_clean_value(source_json, 'hed')
        recipe_json['description'] = strip_tags(json_clean_value(source_json, 'dek'))
        recipe_json['yield'] = json_clean_value(json_clean_value(source_json, 'servingSizeInfo',json.loads('{}')), 'servingSizeDescription')

        # Parse Times
        minutes_prep = iso8601.to_minutes(json_clean_value(source_json, 'formattedPrepTime'))
        minutes_cook = iso8601.to_minutes(json_clean_value(source_json, 'formattedCookTime'))
        minutes_total = minutes_prep + minutes_cook
        if minutes_prep == 0 and minutes_total > 0 and minutes_cook > 0:
            minutes_prep = minutes_total - minutes_cook
        recipe_json['preptime'] = minutes2time(minutes_prep, '')
        recipe_json['cooktime'] = minutes2time(minutes_cook, '')
        recipe_json['totaltime'] = minutes2time(minutes_total)

        # Parse Author
        publisher = "Epicurious"
        author = json_clean_value(source_json, 'author', '')
        if type(author) == list:
            if 'name' in author[0]:
                author = author[0]['name']
        elif 'name' in author:
            author = author['name']
        if publisher != "":
            if author == "" or publisher == author:
                author == publisher
            else:
                if not (publisher in author):
                    author = publisher + ' (' + author + ')'
        recipe_json['author'] = author

        # Ingredients
        recipe_json['ingredient_groups'] = []
        ingredient_groups = json_clean_value(source_json, "ingredientGroups")
        for group in ingredient_groups:
            group_json = json.loads('{"title":"","ingredients":[]}')
            if len(ingredient_groups) > 1:
                group_json['title'] = json_clean_value(group_json, "hed")
            ingredients = json_clean_value(group, "ingredients")
            for ingredient in ingredients:
                group_json['ingredients'].append(strip_tags(json_clean_value(ingredient, "description")))
            recipe_json['ingredient_groups'].append(group_json)

        # Directions
        recipe_json['direction_groups'] = []
        direction_groups = json_clean_value(source_json, "preparationGroups")
        for group in direction_groups:
            group_json = json.loads('{"group":"","directions":[]}')
            if len(direction_groups) > 1:
                group_json['group'] = strip_tags(json_clean_value(group_json, "hed"))
            steps = json_clean_value(group, "steps")
            for step in steps:
                group_json['directions'].append(strip_tags(json_clean_value(step, "description")))
            recipe_json['direction_groups'].append(group_json)

    else:
        raise UrlError(url, 'URL not supported.')

    return recipe_json

def recipe_scraper2json(args, url):
    from recipe_scrapers import scrape_me

    print_debug(args, "Using recipe-scraper module...")

    recipe_json={}
    recipe_json['url'] = url

    try:
        scraper = scrape_me(url)

        recipe_json['title'] = scraper.title()
        recipe_json['description'] = ''
        recipe_json['yield'] = scraper.yields()
        recipe_json['preptime'] = ''
        recipe_json['cooktime'] = ''
        recipe_json['totaltime'] = minutes2time(scraper.total_time())
        recipe_json['ingredient_groups'] = []
        recipe_json['ingredient_groups'].append(json.loads('{"title":"","ingredients":[]}'))
        recipe_json['ingredient_groups'][0]['ingredients'] = scraper.ingredients()
        recipe_json['direction_groups'] = []
        recipe_json['direction_groups'].append(json.loads('{"group":"","directions":[]}'))
        instructions = scraper.instructions().split('\n')
        recipe_json['direction_groups'][0]['directions'] = instructions

    except:
        raise UrlError(url, 'URL not supported.')

    return recipe_json

def generic2json(args, url):
    """ Loads generic URL and builds recipe JSON """

    def get_json(url):
        """ Find and load "standardized" json document containing recipe """

        return_value = None
        page = requests.get(url)

        match = re.search(r'<script[^>]*type=.application/ld\+json.[^>]*>', page.text)
        if match:
            soup = BeautifulSoup(page.text, 'html5lib')
            scripts = soup.findAll('script', attrs = {'type':'application/ld+json'})
            for script in scripts:
                raw_json = json.loads(script.text)
                if type(raw_json) == list:
                    return_value = json_find_array_element(raw_json, '@type', 'Recipe')
                    try:
                        return_value['publisher'] = json_clean_value(json_clean_value(source_json, 'publisher', json.loads('{}'), 'name', ''))
                        if return_value['publisher'] == '':
                            return_value['publisher'] = json_clean_value(json_find_array_element(raw_json, '@type', 'Organization'), 'name', url2publisher(url))
                    except:
                        if not return_value is None:
                            return_value['publisher'] = url2publisher(url)
                elif '@graph' in raw_json and type(raw_json['@graph']) == list:
                    return_value = json_find_array_element(raw_json['@graph'], '@type', 'Recipe')
                    try:
                        return_value['publisher'] = json_clean_value(json_clean_value(source_json, 'publisher', json.loads('{}'), 'name', ''))
                        if return_value['publisher'] == '':
                            return_value['publisher'] = json_clean_value(json_find_array_element(raw_json['@graph'], '@type', 'Organization'), 'name', url2publisher(url))
                    except:
                        if not return_value is None:
                            return_value['publisher']=url2publisher(url)
                else:
                    if 'recipeIngredient' in raw_json:
                        return_value = raw_json
                        try:
                            return_value['publisher'] = json_clean_value(json_clean_value(source_json, 'publisher', json.loads('{}')), 'name', url2publisher(url))
                        except:
                            if not return_value is None:
                                return_value['publisher']=url2publisher(url)
                    else:
                        return_value = None

                if (not return_value is None) and ('recipeIngredient' in return_value):
                    pass
                else:
                    return_value = None
        return return_value

    print_debug(args, "Using generic scraper...")
    recipe_json={}
    recipe_json['url'] = url
    source_json = get_json(url)

    if source_json is None:
        print_info(args, "No application+ld json attempting to use recipe-scrapers...")
        recipe_json = recipe_scraper2json(args, url)
    else:
        recipe_json['title'] = json_clean_value(source_json, 'headline', json_clean_value(source_json, 'name'))
        recipe_json['description'] = json_clean_value(source_json, 'description')
        if 'recipeYield' in source_json and type(source_json['recipeYield']) == list:
            recipe_json['yield'] = max(source_json['recipeYield'])
        else:
            recipe_json['yield'] = json_clean_value(source_json, 'recipeYield')

        # Parse Times
        minutes_total = iso8601.to_minutes(json_clean_value(source_json, 'totalTime'))
        minutes_cook = iso8601.to_minutes(json_clean_value(source_json, 'cookTime'))
        minutes_prep = iso8601.to_minutes(json_clean_value(source_json, 'prepTime'))
        if minutes_prep == 0 and minutes_total > 0 and minutes_cook > 0:
            minutes_prep = minutes_total - minutes_cook
        recipe_json['preptime'] = minutes2time(minutes_prep, '')
        recipe_json['cooktime'] = minutes2time(minutes_cook, '')
        recipe_json['totaltime'] = minutes2time(minutes_total)

        # Parse Author
        publisher = json_clean_value(source_json, 'publisher')
        author = json_clean_value(source_json, 'author')
        if type(author) == list:
            if 'name' in author[0]:
                author = author[0]['name']
        elif 'name' in author:
            author = author['name']
        if publisher != "":
            if author == "" or publisher == author:
                author == publisher
            else:
                if not (publisher in author):
                    author = publisher + ' (' + author + ')'
        recipe_json['author'] = author

        # Ingredients
        ingredients = list(json_find_key(source_json, "recipeIngredient"))[0]
        recipe_json['ingredient_groups'] = []
        recipe_json['ingredient_groups'].append(json.loads('{"title":"","ingredients":[]}'))
        out_ingredients = []
        for ingredient in ingredients:
            out_ingredients.append(strip_tags(ingredient))
        recipe_json['ingredient_groups'][0]['ingredients'] = out_ingredients

        print_debug(args, json.dumps(source_json))
        # Directions
        out_instruction=[]
        instructions=list(json_find_key(source_json, 'recipeInstructions'))[0]
        for instruction in instructions:
            try:
                instruction_json = instruction
                out_instruction.append(strip_tags(instruction_json['text']))
            except:
                out_instruction.append(strip_tags(str(instruction)))
        recipe_json['direction_groups'] = []
        recipe_json['direction_groups'].append(json.loads('{"group":"","directions":[]}'))
        recipe_json['direction_groups'][0]['directions'] = out_instruction

    return recipe_json

def url2recipe_json(args, url):
    """ Loads recipe JSON from URL """

    print_info (args, "Processsing %s..." % (url))

    # Branch based on domain
    domain = url2domain(url)
    print_debug (args, "Branching based on domain (%s)..." % domain)
    if domain in [ 'www.americatestkitchen.com','www.cookscountry.com','www.cooksillustrated.com' ]:
        recipe_json = ci2json(args, url)
    elif domain == 'www.epicurious.com':
        if args.force_recipe_scraper:
            try:
                recipe_json = recipe_scraper2json(args, url)
            except:
                recipe_json = epicurious2json(args, url)
        else:
            recipe_json = epicurious2json(args, url)
    elif domain == 'www.saveur.com':
        recipe_json = saveur2json(args, url)
    else:
        if args.force_recipe_scraper:
            try:
                recipe_json = recipe_scraper2json(args, url)
            except:
                recipe_json = generic2json(args, url)
        else:
            recipe_json = generic2json(args, url)
    return recipe_json

def format2text(format):
    """ Formats output ext to human readable format name """

    format_text = ''
    if format == 'json':
        format_text = 'JSON'
    elif format == 'md':
        format_text = 'Markdown'
    elif format == 'rst':
        format_text = 'reStructuredText'
    else:
        format_text = "Unknown format [%s]" % (format)
        print_warning(None, "Unknown format [%s]" % (format))
        #raise ("ERROR: Unknown format [%s]" % (format))
    return format_text

def recipe_json2doc(args, recipe_json, format='rst', base_level=1):
    """ Build reStructuredText from recipe JSON """

    def output_header(header_text, format='rst', level=1):
        """ returns string containg formated header """

        out_string = ''
        if format == 'md':
            out_string += '#' * (level + 1)
            out_string += ' '
        out_string += header_text + '\n'
        if format == 'rst':
            level_chars = ['=', '-', '^']
            level_char = level_chars[level - 1]
            out_string += re.sub('.', level_char, header_text) + '\n'
        out_string += '\n'

        return out_string

    def output_group(json_obj, group_key, item_key, item_prefix, item_wrap = False, format='rst', base_level=2):
        """ returns string containg formated groups/lists """

        out_string = ''
        group_index = 0
        group_count = len(json_clean_value(recipe_json, group_key))
        for group in json_clean_value(recipe_json, group_key):
            group_title = json_clean_value(group, 'title')

            if group_title != '':
                if group_index > 0:
                    out_string += '\n'
                out_string += output_header(group_title, format=format, level=(base_level+1))

            item_count = 0
            for item in json_clean_value(group, item_key):
                item_count += 1
                if item_prefix == '#':
                    prefix = str(item_count).strip() + '. '
                else:
                    prefix = item_prefix.strip() + ' '
                if item_wrap:
                    item_lines = textwrap.wrap(item, width = 75, initial_indent = prefix, subsequent_indent = re.sub('.', ' ', prefix))
                    for line in item_lines:
                        out_string += line + '\n'
                else:
                    out_string += prefix.strip() + ' ' + str(item) + '\n'
            group_index += 1

        return out_string

    format_prefix = '-'
    if format == 'md':
        format_prefix = '*'

    print_debug(args, "Building " + format2text(format) + " from recipe JSON...")

    output = output_header(json_clean_value(recipe_json, 'title'), format)

    recipe_yield = json_clean_value(recipe_json, 'yield')
    preptime = json_clean_value(recipe_json, 'preptime')
    cooktime = json_clean_value(recipe_json, 'cooktime')
    totaltime = json_clean_value(recipe_json, 'totaltime')

    info = "| "
    if preptime != '':
        info += 'Prep: ' + preptime + ' | '
    if totaltime != '':
        info += 'Total: ' + totaltime + ' | '
    if recipe_yield != '':
        info += 'Yield: ' + recipe_yield + ' | '
    info = info.strip()

    if info != '|':
        divider_line = re.sub('[^|]', '-', info)
        if format == 'rst':
            divider_line = re.sub('[|]', '+', divider_line)
        output += divider_line + '\n' + info +'\n' + divider_line + '\n\n'

    # TODO: make this work with markdown and missing URL
    url = json_clean_value(recipe_json, 'url')
    author = json_clean_value(recipe_json, 'author')
    if url is None or url == '':
        if not author is None and author != '':
            output += 'Source: ' + author + '\n\n'
    else:
        if author is None or author == '':
            author = url2domain(url)
        if format == 'md':
            output += 'Source: [' + author + '](' + url + ')\n\n'
        elif format == 'rst':
            output += 'Source: `' + author + ' <' + url + '>`__\n\n'
        else:
            output += 'Source: ' + author + '\n\n'

    description = textwrap.wrap(json_clean_value(recipe_json, 'description'), width = 75)
    for line in description:
        output += line + '\n'

    output += '\n'
    output += output_header('Ingredients', format=format, level=2)
    output += output_group(recipe_json, 'ingredient_groups', 'ingredients', format_prefix, format=format, base_level=2)

    output += '\n'
    output += output_header('Directions', format=format, level=2)
    output += output_group(recipe_json, 'direction_groups', 'directions', '#', item_wrap = True, format=format, base_level=2)

    notes = json_clean_value(recipe_json, 'notes')
    if not notes is None and notes != '':
        output += '\n'
        output += output_header('Notes', format=format, level=2)

        for note in notes:
            note = re.sub('\*\*\*', '', note)
            if len(notes) > 1:
                not_prefic = format_prefix.strip() + ' '
                for line in textwrap.wrap(note, width = 75, initial_indent = note_prefix, subsequent_indent = re.sub('.', ' ', note_prefix)):
                    output += line + '\n'
            else:
                for line in textwrap.wrap(note, width = 75):
                    output += line + '\n'
            output += '\n'

    return output

def recipe_output(args, recipe_json):
    """ Output recipe_json document in the desired format """

    def output_filename(filename, ext = ''):
        """ Ensures filename has proper extension. """
        ret_value = filename
        if ext != "":
            ret_value = (filename + '.' + ext).replace('.' + ext + '.' + ext, '.' + ext)

        return ret_value

    def recipe_output_file(args, recipe_json, format=''):
        """ Output recipe_json document in the desired format """

        ret_value = 0

        title = json_clean_value(recipe_json, 'title')
        if format == '':
            if not args.outfile is None and args.outfile != '':
                try:
                    format = (os.path.splitext(args.outfile)[1]).split('.')[-1]
                except:
                    pass

        if format == 'json':
            output = json.dumps(recipe_json, indent=4)
        elif format == 'md':
            output = recipe_json2doc(args, recipe_json, format='md')
        elif format == 'rst':
            output = recipe_json2doc(args, recipe_json, format='rst')
        else:
            print_error(args, "Unknown format [%s]" % (format))
            raise ("ERROR: Unknown format [%s]" % (format))

        if output is None or output.strip() == "":
            print_error(args,"Problem output is empty")
        else:
            if args.save_to_file:
                if args.outfile is None or args.outfile == "":
                    savefile = output_filename(re.sub(r'\W+', '', title), format)
                else:
                    savefile = output_filename(args.outfile, format)
                print_info(args, "Writing output to %s..." % savefile)
                text_file = open(savefile, "w")
                ret_value = text_file.write(output)
                text_file.close()
            else:
                print (output)

        return ret_value

    title = json_clean_value(recipe_json, 'title')
    if title != "":
        print_info (args, "   Processing complete: %s" % (title))
        if args.output_json:
            recipe_output_file (args, recipe_json, "json")
        if args.output_md:
            recipe_output_file (args, recipe_json, "md")
        if args.output_rst:
            recipe_output_file (args, recipe_json, "rst")
    else:
        print_warning (args, "Unable to retrieve title from json")

def quick_tests(args):
    """ some quick tests """

    url2domain("https://www.finecooking.com/recipe/herbed-grill-roasted-lamb")

    tests=[
        'https://www.finecooking.com/recipe/herbed-grill-roasted-lamb',
        'https://www.bonappetit.com/recipe/instant-pot-glazed-and-grilled-ribs',
        'https://www.saveur.com/perfect-brown-rice-recipe/',
        'https://www.thechunkychef.com/easy-slow-cooker-mongolian-beef-recipe'
    ]
    for test in tests:
        print_info (args, "==========================")
        print_info (args, recipe_output(args, url2recipe_json(test)))
        print_info (args, "==========================")

def main(args):
    print_debug (args, args)

    if not args.URL == [[]]:
        for url in args.URL[0]:
            recipe_json = url2recipe_json(args, url)
            recipe_output(args, recipe_json)
    else:
        if not args.infile is None and args.infile != "":
            print_info (args, "Processsing %s..." % args.infile)
            with open(args.infile) as json_file:
                recipe_json = json.load(json_file)
                recipe_output(args, recipe_json)
        else:
            print_error (args,"You must specify an input URL or input JSON file.\n")
            parse_arguments(print_usage=True)

if __name__ == '__main__':
    args = parse_arguments()
    #print_debug (json.dumps(saveur2json(args, 'https://www.epicurious.com/recipes/food/views/instant-pot-macaroni-and-cheese'), indent=4))
    main(args)

#quick_tests()

#iso8601.tests()
