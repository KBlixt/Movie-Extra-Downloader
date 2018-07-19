import os
import configparser
from configparser import NoOptionError
import fnmatch
import pprint
import shutil
import time
import sys
import codecs
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import json
from socket import timeout

# pip install these packages:
try:
    from googlesearch import search as google_search  # google package
except ImportError:
    print('Please upgrade to python 3.6 or run the 2.7 version.')
    sys.exit()
from pytube import YouTube  # pytube package
from pytube import exceptions
import ffmpeg
# also, install FFmpeg.

########################################################################################################################

# global variables:
# todo: check config exists.
with codecs.open(os.path.join(os.path.dirname(sys.argv[0]), 'default_config.cfg'), 'r', 'utf-8') as file:
    global_config = configparser.ConfigParser()
    global_config.read_file(file)
global_settings = global_config['SETTINGS']
global_advanced_settings = global_config['ADVANCED_SETTINGS']

library_dir = global_settings.get('library_directory')
# todo: check library_dir exists.

temp_dir = global_settings.get('temporary_directory', os.path.dirname(sys.argv[0]))
movie_folder_naming_scheme = global_settings.get('movie_folder_naming_scheme')

tmdb_api_key = global_settings.get('tmdb_api_key', None)
if tmdb_api_key is None:
    has_tmdb_api_key = False
else:
    has_tmdb_api_key = True
# todo: check tmdb_api_key is ok.

extra_config_dir = os.path.join(os.path.dirname(sys.argv[0]), 'extra_configs')

tmdb_movie_search_result = None
tmdb_movie_details = None
tmdb_movie_cast_members = None

########################################################################################################################


def main():

    global tmdb_movie_details
    global tmdb_movie_cast_members
    global tmdb_movie_search_result

    for directory_name in os.listdir(library_dir):
        tmdb_movie_search_result = None
        tmdb_movie_details = None
        tmdb_movie_cast_members = None
        print(directory_name)
        directory = get_directory_data(directory_name)
        # todo: make sure it's a movie directory
        for config in os.listdir(extra_config_dir):
            # todo: make sure it's a .cfg file
            if process_directory(directory, config):
                pass
                # todo: record info to record_data


def process_directory(directory, config_file):

    with codecs.open(os.path.join(os.path.dirname(sys.argv[0]), extra_config_dir, config_file), 'r', 'utf-8') as file2:
        settings = configparser.ConfigParser()
        settings.read_file(file2)

    # decide if a search is to be made.

    if not settings['EXTRA_CONFIG'].getboolean('force') or not global_advanced_settings.getboolean('force_all'):
        if directory['record_data'].get('completed', False):
            return False

    # make the search and return a youtube video source.

    video = get_video(directory, settings)

    # download the extra from youtube
    download_info = download(video, settings)
    # post process the extra

    post_process(download_info, settings)

    return True


def get_directory_data(directory_name):

    directory_ret = dict()

    directory_ret['name'] = directory_name
    directory_ret['full_path'] = os.path.join(library_dir, directory_name)
    directory_ret['clean_name_tuple'] = (directory_ret['name']
                                         .replace('(', '')
                                         .replace(')', '')
                                         .replace('[', '')
                                         .replace(']', '')
                                         .replace('{', '')
                                         .replace('}', '')
                                         .replace(':', '')
                                         .replace(';', '')
                                         .replace('.', ' ')
                                         .replace('_', ' ')
                                         .lower()).split(' ')

    if global_settings.getboolean('release_year_end_of_file'):
        directory_ret['release_year'] = directory_ret['clean_name_tuple'][-1]
        directory_ret['movie_name'] = ' '.join(directory_ret['clean_name_tuple'][:-1])
    else:
        directory_ret['release_year'] = None
        directory_ret['movie_name'] = ' '.join(directory_ret['clean_name_tuple'])

    # todo: make sure release_year is a year between 1700 and 2100. else > None

    directory_ret['files'] = list()
    for file3 in os.listdir(directory_ret['full_path']):
        directory_ret['files'].append(file3)
        # todo: nested folders.

    # todo: make sure the record_data file exists. and that it is an valid json list
    if os.path.isfile('record_data'):
        with open('record_data') as data_file:
            data = json.load(data_file)
            if directory_ret['name'] in data:
                directory_ret['record_data'] = data[directory_ret['name']]
            else:
                directory_ret['record_data'] = dict()

    else:
        directory_ret['record_data'] = dict()

    get_tmdb_movie_search_result(directory_ret['movie_name'], directory_ret['release_year'])
    get_tmdb_movie_details()
    get_tmdb_movie_cast_members()

    return directory_ret


def get_video(directory, settings):

    def search_result():

        def search():
            item_list = list()

            # todo: limit > 0

            while True:
                try:
                    time.sleep(global_advanced_settings.getint('search_cooldown'))
                    print('searching for: "' + query + '"')
                    for url in google_search(query, stop=limit):
                        if len(item_list) >= limit:
                            break
                        new_item = {'link': url}

                        while True:

                            for existing_candidate in video_candidates:
                                if new_item['link'] == existing_candidate['link']:
                                    break

                            try:
                                new_item['pytube_result'] = YouTube(new_item['link'])
                                item_list.append(new_item)
                                break
                            except KeyError:
                                print('Pytube failed to initialize (KeyError). trying again in 2 seconds.')
                                time.sleep(2)
                            except URLError:
                                print('Pytube failed to initialize (URLError). trying again in 2 seconds.')
                                time.sleep(2)
                            except exceptions.RegexMatchError:
                                new_item['delete_this_item'] = True
                                break

                    break

                except HTTPError as e:
                    if e.code == 503:
                        print('------------------------------------------------------------------------------------')
                        print('It seems that your IP-address have been flagged by google for unusual activity. ')
                        print('They usually put down the flag after some time so try again tomorrow.')
                        print('If this is a reoccurring issue, increase the search cooldown under advanced settings')
                        print('------------------------------------------------------------------------------------')
                        sys.exit()
                    else:
                        print('Failed to retrieve search results, trying again in 2 seconds: ' + e.msg)
                        time.sleep(2)
                        continue

                except URLError as e:
                    print('Failed to retrieve search results, trying again in 2 seconds: ' + e.msg)
                    time.sleep(2)
                    continue

            return item_list

        video_candidates = list()
        for option, query in settings['SEARCHES'].items():
            if 'search_string' not in option:
                continue

            limit = settings['SEARCHES'].getint('search_result_limit' + option.replace('search_string', ''))

            query = query.replace('{movie_name}', directory['movie_name'])

            if directory['release_year'] is not None:
                query = query.replace('{release_year}', directory['release_year'])
            else:
                query = query.replace('{release_year}', '')

            if tmdb_movie_details['production_companies'][0]['name'] is not None and '{main_studio_name}' in query:
                get_tmdb_movie_details()
                query = query.replace('{main_studio_name}', tmdb_movie_details['production_companies'][0]['name'])
            else:
                query = query.replace('{main_studio_name}', '')

            query = query.replace('  ', ' ')

            video_candidates += search()

        return video_candidates

    def scan_candidates():

        selection_info['max_resolution'] = 0
        for candidate in selection_info['candidates']:

            candidate['delete_this_item'] = False

            video = candidate['pytube_result']

            if candidate['delete_this_item'] or video is None:
                continue

            candidate['title'] = video.title
            candidate['rating'] = float(video.player_config_args['avg_rating'])
            candidate['view_count'] = int(video.player_config_args['view_count'])
            candidate['thumbnail_url'] = video.thumbnail_url
            candidate['channel'] = video.player_config_args['author']
            candidate['tags'] = video.player_config_args['keywords']

            if candidate['view_count'] < 100:
                candidate['view_count'] = 100

            candidate['adjusted_rating'] = candidate['rating'] * (1 - 1 / ((candidate['view_count'] / 60) ** 0.5))

            candidate['resolution'] = 0
            for stream in video.streams.filter(type='video').all():
                try:
                    resolution = int(stream.resolution.replace('p', ''))
                except AttributeError:
                    resolution = 0

                if resolution > selection_info['max_resolution']:
                    selection_info['max_resolution'] = resolution
                if resolution > candidate['resolution']:
                    candidate['resolution'] = resolution

            try:
                if 'ad_preroll' in video.player_config_args:
                    candidate['adds_info'] = 'have adds'
                else:
                    candidate['adds_info'] = 'No adds'
            except ValueError:
                candidate['adds_info'] = 'No adds'

        return selection_info

    def filter_candidates():

        filtered_candidates = list()

        required_words = retrive_list_from_string(settings['FILTERING'].get('required_words').lower())
        banned_words = retrive_list_from_string(settings['FILTERING'].get('banned_words').lower())
        banned_channels = retrive_list_from_string(settings['FILTERING'].get('banned_channels').lower())

        banned_years = list(range(1800, 2100))
        for year in banned_years:
            if str(year) in directory['movie_name']:
                banned_years.remove(year)
        if directory['release_year'] is not None:
            if int(directory['release_year']) in banned_years:
                banned_years.remove(int(directory['release_year']))
                # todo: +- 1 year?

        for candidate in selection_info['candidates']:

            append_video = True

            # todo: make filter that match title name with trailer title. (min 66% match rounding up )
            # ignoring words: the, on, of, a, an

            if candidate['delete_this_item']:
                continue

            for year in banned_years:
                if str(year) in candidate['title']:
                    append_video = False
                    break
                if str(year) in candidate['tags']:
                    append_video = False
                    break

            for word in required_words:
                if word.lower() not in candidate['title'].lower():
                    append_video = False

            for word in banned_words:
                if word.lower() in candidate['title'].lower():
                    append_video = False
                    break

            # todo: move to post scoring filter
            for channel in banned_channels:
                if channel.lower() == candidate['channel'].lower():
                    append_video = False
                    break

            if append_video:
                filtered_candidates.append(candidate)

        selection_info['candidates'] = filtered_candidates

        return

    def score_candidates():

        for candidate in selection_info['candidates']:
            candidate['score'] = 0

            if candidate['resolution'] < 700:
                candidate['adjusted_rating'] *= 0.96

        return

    def post_scoring_filter():
        return

    def order_candidates():

        # interviews: limit same person interviews.
        # behind the scenes:
        # trailers:
        #

        selected_extra = None

        top_score = 0
        top_view_count = 0

        for candidate in selection_info['candidates']:

            print('-----------------------------------------------------------------')
            print(candidate['title'])
            print(candidate['adds_info'])
            print(candidate['resolution'])
            print(candidate['link'])
            print(candidate['adjusted_rating'])
            print(candidate['view_count'])

            if candidate['adjusted_rating'] > top_score:
                top_score = candidate['adjusted_rating']

        for candidate in selection_info['candidates']:
            if candidate['adjusted_rating'] > top_score * 0.95:
                if candidate['view_count'] > top_view_count:
                    top_view_count = candidate['view_count']
                    selected_extra = candidate

        print('-----------------------------------------------------------------')
        print('picked: ' + selected_extra['title'] + ' (' + selected_extra['link'] + ')')
        print('-----------------------------------------------------------------')
        return selected_extra

    selection_info = {'candidates': search_result()}

    scan_candidates()

    filter_candidates()

    score_candidates()

    # todo: make post scoring filter

    return order_candidates()


def download(video, settings):
    info_ret = dict()
    return info_ret


def post_process(download_info, settings):
    # todo: reduce sound
    # todo: remove green disclaimer if it exist
    # todo: encode in mp4, aac, h264 or link the stream
    pass


def retrieve_web_page(url, page_name='page'):

    response = None
    print('Downloading ' + page_name + '.')

    for attempt in range(10):
        try:
            response = urlopen(url, timeout=2)
            break

        except timeout:
            print('Failed to download ' + page_name + ' : timed out. Trying again in 2 seconds.')

            if attempt > 5:
                print('You might have lost internet connection.')
                raise ValueError('Failed to retrive web page: url requests timed out.')

            time.sleep(2)

        except HTTPError as e:
            raise ValueError('Failed to download ' + page_name + ' : ' + e.msg + '. Skipping.')

        except URLError as e:
            print('Failed to download ' + page_name + '. Trying again in 2 seconds')

            if attempt > 5:
                print('You might have lost internet connection.')
                raise ValueError('Failed to retrive web page: ' + e.reason + '.')

            time.sleep(2)

    return response


def get_tmdb_movie_search_result(name, release_year):
    global tmdb_movie_search_result
    if tmdb_movie_search_result is not None:
        return

    # todo: modify to not use release_year in search but rather as picking the right one.
    # todo: any word in any other movie not in the wanted movie should be on ban list for filtering.
    # todo: maybe not: false negatives

    url = 'https://api.themoviedb.org/3/search/movie' \
          '?api_key=' + tmdb_api_key + \
          '&language=en-US&query=' \
          + name.replace(' ', '+') + \
          '&page=1&include_adult=false'

    if release_year is not None:
        url += '&year=' + str(release_year)

    response = retrieve_web_page(url, 'movie search api page')

    data = json.loads(response.read().decode('utf-8'))

    if data['total_results'] == 0:
        raise ValueError('Unable to find a movie for the directory "' + name + '", skipping.')

    # todo: add +- 1 year to the year if it's close to new year.

    tmdb_movie_search_result = data['results'][0]
    response.close()


def get_tmdb_movie_details():
    global tmdb_movie_details
    global tmdb_movie_search_result
    if tmdb_movie_details is not None:
        return

    response = retrieve_web_page('https://api.themoviedb.org/3/movie/'
                                 + str(tmdb_movie_search_result['id']) +
                                 '?api_key=' + tmdb_api_key +
                                 '&language=en-US', 'movie details')

    data = json.loads(response.read().decode('utf-8'))
    tmdb_movie_details = data
    response.close()


def get_tmdb_movie_cast_members():
    global tmdb_movie_details
    global tmdb_movie_cast_members
    if tmdb_movie_cast_members is not None:
        return

    response = retrieve_web_page('https://api.themoviedb.org/3/movie/'
                                 + str(tmdb_movie_search_result['id']) +
                                 '/credits'
                                 '?api_key=' + tmdb_api_key, 'cast members')

    data = json.loads(response.read().decode('utf-8'))
    tmdb_movie_cast_members = data
    response.close()


def retrive_list_from_string(string, delimiter=',', remove_spaces_next_to_delimiter=True):
    if remove_spaces_next_to_delimiter:
        while ' ' + delimiter in string:
            string = string.replace(' ' + delimiter, delimiter)
        while delimiter + ' ' in string:
            string = string.replace(delimiter + ' ', delimiter)

    return string.split(delimiter)


main()
# todo: add link_only option and capabilities.
sys.exit()
