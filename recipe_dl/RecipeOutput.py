#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import textwrap

from CustomPrint import print_info, print_debug, print_error, print_warning, print_to_console
from UtilityFunctions import url2domain, url2publisher, json_clean_value, strip_tags

def recipe_output(args, recipe_json):
    """ Output recipe_json document """

    def recipe_output_file(args, recipe_json, format=""):
        """ Output recipe_json document in the desired format """

        def recipe_json2doc(args, recipe_json, format='rst', base_level=1):
            """ Build reStructuredText from recipe JSON """

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
            print_debug(args, recipe_json)

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

        def output_filename(filename, ext=""):
            """ Ensures filename has proper extension. """

            ret_value = filename
            if ext != "":
                ret_value = (filename + "." + ext).replace("." + ext + "." + ext, "." + ext)
            return ret_value

        ret_value = 0

        title = json_clean_value(recipe_json, "title")
        if format == '':
            if not args.outfile is None and args.outfile != '':
                try:
                    format = (os.path.splitext(args.outfile)[1]).split(".")[-1]
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

    title = json_clean_value(recipe_json, "title")
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
