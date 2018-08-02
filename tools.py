from _socket import timeout
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.request import quote
import time
import json
import hashlib


def hash_file(file_path):

    md5 = hashlib.md5()
    with open(file_path, 'rb') as file:
        for i in range(10):
            data = file.read(2**20)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def get_keyword_list(string):

    ret = ' ' + get_clean_string(string).lower() + ' '
    ret = (ret.replace(' the ', ' ')
              .replace(' in ', ' ')
              .replace(' a ', ' ')
              .replace(' by ', ' ')
              .replace(' is ', ' ')
              .replace(' am ', ' ')
              .replace(' an ', ' ')
              .replace(' in ', ' ')
              .replace(' with ', ' ')
              .replace(' from ', ' ')
              .replace(' and ', ' ')
              .replace(' movie ', ' ')
              .replace(' trailer ', ' ')
              .replace(' interview ', ' ')
              .replace(' interviews ', ' ')
              .replace(' scenes ', ' ')
              .replace(' scene ', ' ')
              .replace(' official ', ' ')
              .replace(' hd ', ' ')
              .replace(' hq ', ' ')
              .replace(' lq ', ' ')
              .replace(' 1080p ', ' ')
              .replace(' 720p ', ' ')
              .replace(' of ', ' '))

    return list(set(space_cleanup(ret).split(' ')))


def get_clean_string(string):
    ret = ' ' + string.lower() + ' '

    ret = (ret.replace('(', '')
              .replace(')', '')
              .replace('[', '')
              .replace(']', '')
              .replace('{', '')
              .replace('}', '')
              .replace(':', '')
              .replace(';', '')
              .replace('?', '')
              .replace("'", '')
              .replace("’", '')
              .replace("´", '')
              .replace("`", '')
              .replace("*", ' ')
              .replace('.', ' ')
              .replace('·', '-')
              .replace(' -', ' ')
              .replace('- ', ' ')
              .replace('_', ' ')
              .replace(' + ', ' : ')
              .replace('+', '/')
              .replace(' : ', ' + ')
              .replace('/ ', ' ')
              .replace(' /', ' ')
              .replace(' & ', ' '))

    return space_cleanup(replace_roman_numbers(ret))


def replace_roman_numbers(string):
    ret = ' ' + string.lower() + ' '

    ret = (ret.replace(' ix ', ' 9 ')
           .replace(' viiii ', ' 9 ')
           .replace(' viii ', ' 8 ')
           .replace(' vii ', ' 7 ')
           .replace(' vi ', ' 6 ')
           .replace(' iv ', ' 4 ')
           .replace(' iiii ', ' 4 ')
           .replace(' iii ', ' 3 ')
           .replace(' ii ', ' 2 ')
           .replace(' trailer 4 ', ' trailer ')
           .replace(' trailer 3 ', ' trailer ')
           .replace(' trailer 2 ', ' trailer ')
           .replace(' trailer 1 ', ' trailer '))

    return space_cleanup(ret)


def make_list_from_string(string, delimiter=',', remove_spaces_next_to_delimiter=True):
    if remove_spaces_next_to_delimiter:
        while ' ' + delimiter in string:
            string = string.replace(' ' + delimiter, delimiter)
        while delimiter + ' ' in string:
            string = string.replace(delimiter + ' ', delimiter)

    return string.split(delimiter)


def space_cleanup(string):
    ret = string
    while '  ' in ret:
        ret = ret.replace('  ', ' ')
    while ret.endswith(' '):
        ret = ret[:-1]
    while ret.startswith(' '):
        ret = ret[1:]
    return ret


def retrieve_web_page(url, page_name='page'):

    response = None
    print('Downloading ' + page_name + '.')

    for tries in range(1, 10):
        try:
            response = urlopen(url, timeout=2)
            break

        except UnicodeEncodeError as e:
            print('Failed to download ' + page_name + ' : ' + str(e) + '. Skipping.')
            break

        except timeout:
            if tries > 5:
                print('You might have lost internet connection.')
                break

            time.sleep(1)
            print('Failed to download ' + page_name + ' : timed out. Retrying.')

        except HTTPError as e:
            print('Failed to download ' + page_name + ' : ' + str(e) + '. Skipping.')
            break

        except URLError:
            if tries > 3:
                print('You might have lost internet connection.')
                raise

            time.sleep(1)
            print('Failed to download ' + page_name + '. Retrying.')

    return response


def apply_query_template(template, keys):
    ret = template
    for key, value in keys.items():
        if isinstance(value, str):
            ret = ret.replace('{' + key + '}', value)
        elif isinstance(value, int):
            ret = ret.replace('{' + key + '}', str(value))
        elif isinstance(value, float):
            ret = ret.replace('{' + key + '}', str(value))

    return space_cleanup(ret)


def get_tmdb_search_data(tmdb_api_key, title):
    response = retrieve_web_page('https://api.themoviedb.org/3/search/movie'
                                       '?api_key=' + tmdb_api_key +
                                       '&language=en-US&query='
                                       + quote(title.encode('utf-8')) +
                                       '&page=1&include_adult=false', 'tmdb movie search page')
    if response is None:
        return None
    data = json.loads(response.read().decode('utf-8'))
    response.close()

    return data


def get_tmdb_details_data(tmdb_api_key, tmdb_id):
    response = retrieve_web_page('https://api.themoviedb.org/3/movie/'
                                       + str(tmdb_id) +
                                       '?api_key=' + tmdb_api_key +
                                       '&language=en-US', 'movie details')
    if response is None:
        return None
    data = json.loads(response.read().decode('utf-8'))
    response.close()

    return data


def get_tmdb_crew_data(tmdb_api_key, tmdb_id):
    pass
