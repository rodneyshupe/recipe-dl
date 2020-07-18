#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import re
import json

import iso8601
from CustomPrint import custom_print_init, print_info, print_debug, print_to_console

from CustomExceptions import Error, UrlError
from UtilityFunctions import url2domain, url2publisher, json_clean_value, strip_tags

from lxml import html
from bs4 import BeautifulSoup

def url2recipe_json(args, url):
    """ Loads recipe JSON from URL """

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
                print_debug ('Saving cookies...')
                filename = cookie_filename(url)
                with open(filename, 'wb') as f:
                    pickle.dump(requests_cookiejar, f)

            def load_cookies(url):
                """ Loads Cookie jar """
                print_debug ('Loading cookies...')

                filename = cookie_filename(url)
                if not os.path.isfile(filename):
                    print_debug ("Unable to find " + filename + " adjusting.")
                    filename = os.path.dirname(os.path.abspath(__file__)) + "/" + filename

                if os.path.isfile(filename):
                    with open(filename, 'rb') as f:
                        return pickle.load(f)
                else:
                    print_debug ("Unable to find " + filename)
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

                print_debug ("Getting page using cookies...")

                recipe_page = None

                if cookies is None:
                    #load cookies and do a request
                    cookies = load_cookies(url)

                if not cookies is None:
                    print_debug ('cookies = ' + str(requests.utils.dict_from_cookiejar(cookies)))
                    recipe_page = requests.get(url, cookies=cookies).text

                return recipe_page

            def get_page_using_session(args, url):

                print_debug ("Getting page using sessions...")

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

        print_debug("Using Cook's Illustrated scraper...")
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

        print_debug("Using Saveur scraper...")
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
                            #print_debug(json.dumps(return_value, indent=4))
            return return_value

        print_debug("Using Epicurious scraper...")
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

        print_debug("Using recipe-scraper module...")

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

            match = re.search(r'<script[^>]*type=.?application/ld\+json.?[^>]*>', page.text)
            if match:
                soup = BeautifulSoup(page.text, 'html5lib')
                scripts = soup.findAll('script', attrs = {'type':'application/ld+json'})
                for script in scripts:
                    json_stripped=re.sub('^[^\{\[]*', '', script.text)
                    raw_json = json.loads(json_stripped)
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

        print_debug("Using generic scraper...")
        recipe_json={}
        recipe_json['url'] = url
        source_json = get_json(url)

        if source_json is None:
            print_info("No application+ld json attempting to use recipe-scrapers...")
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
            if minutes_total == 0 and (minutes_prep > 0 or minutes_cook > 0):
                minutes_total = minutes_prep + minutes_cook
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

            print_debug(json.dumps(source_json))
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

    custom_print_init (quiet=args.quiet, debug=args.debug)

    print_info ("Processsing %s..." % (url))

    # Branch based on domain
    domain = url2domain(url)
    print_debug ("Branching based on domain (%s)..." % domain)
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
