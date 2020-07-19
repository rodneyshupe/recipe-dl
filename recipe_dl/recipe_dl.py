#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.dirname(__file__))

import argparse

from CustomPrint import custom_print_init, print_info, print_debug, print_error, print_warning

from Scrapers import url2recipe_json
from RecipeOutput import recipe_output

__version__ = '0.2.3'
__author__ = u'Rodney Shupe'

def parse_arguments(print_usage = False, detail = False):
    """ Creates a new argument parser. """

    parser = argparse.ArgumentParser('recipe-dl')
    version = '%(prog)s v' + __version__
    parser.add_argument(
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
        default=None,
        #help="Suppress most output aka Silent Mode.",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Make output verbose",
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
    parser.add_argument(
        "--quick-tests",
        action="store_true",
        dest="quick_tests",
        help=argparse.SUPPRESS,
        default=False
    )

    parser.add_argument('URL', nargs='*', action="append", default=[],)

    if print_usage:
        if detail:
            parser.print_help()
        else:
            parser.print_usage()
    else:
        args = parser.parse_args()

        if args.quiet is None:
            args.quiet = not args.verbose

        if args.debug and args.quiet:
            args.quiet = False
            print_warning ("Debug option selected. Can not run in \"Silent Mode\"")

        custom_print_init (quiet=args.quiet, debug=args.debug)

        filetype_count = 0
        if args.output_json:
            filetype_count += 1
        if args.output_md:
            filetype_count += 1
        if args.output_rst:
            filetype_count += 1

        print_debug("filetype_count=%s" % filetype_count)
        if filetype_count == 0:
            args.output_rst = True
        elif filetype_count > 1:
            print_warning ("More than one output file type select. Assuming 'Save to File'")
            args.save_to_file = True

        if not args.save_to_file and not args.outfile is None and args.outfile != '':
            args.save_to_file = True

        return args

def quick_tests(args):
    """ some quick tests """

    from UtilityFunctions import url2domain
    url2domain("https://www.finecooking.com/recipe/herbed-grill-roasted-lamb")

    tests=[
        'https://www.finecooking.com/recipe/herbed-grill-roasted-lamb',
        'https://www.bonappetit.com/recipe/instant-pot-glazed-and-grilled-ribs',
        'https://www.saveur.com/perfect-brown-rice-recipe/',
        'https://www.thechunkychef.com/easy-slow-cooker-mongolian-beef-recipe'
    ]
    for test_url in tests:
        custom_print_init (quiet=args.quiet, debug=args.debug)

        print_info ("==========================")
        recipe_output(args, url2recipe_json(args, test_url))
        print_info ("==========================")

def main(args=None):
    if args is None:
        args = parse_arguments()

    print_debug (args)
    if args.quick_tests:
        quick_tests(args)
    else:
        if not args.URL == [[]]:
            for url in args.URL[0]:
                recipe_json = url2recipe_json(args, url)
                recipe_output(args, recipe_json)
        else:
            if not args.infile is None and args.infile != "":
                print_info ("Processsing %s..." % args.infile)
                with open(args.infile) as json_file:
                    recipe_json = json.load(json_file)
                    recipe_output(args, recipe_json)
            else:
                print_error ("You must specify an input URL or input JSON file.\n")
                parse_arguments(print_usage=True)

if __name__ == '__main__':
    args = parse_arguments()
    main(args)

#quick_tests()
