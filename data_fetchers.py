from googlesearch import search as google_web_search
from time import sleep
from time import clock
import sys
from bs4 import BeautifulSoup
from _socket import timeout
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, quote
import time
import json

last_request_time = None


def google_search(query, limit):
    """returns a list of [limit] urls to videos that was generated from a google search using the [query] as
    search text"""
    global last_request_time
    url_list = list()

    for tries in range(1, 10):

        if last_request_time is None:
            pass
        if last_request_time:
            sleep(int(60 - (clock() - last_request_time)))
        last_request_time = clock()

        try:
            for url in google_web_search(query, stop=limit):
                if 'youtube.com/watch?v=' in url:
                    url_list.append(url.split('&')[0])

        except KeyboardInterrupt:
            raise

        except HTTPError as e:
            print('google search service unavailable.')

            if tries > 3:
                print('Failed to download google search result. Reason: ' + str(e))
                raise

            print('Failed to download google search result, retrying. Reason: ' + str(e))
            sleep(1)

        except:
            e = sys.exc_info()[0]
            if tries > 3:
                print('Failed to download google search result. Reason: ' + str(e))
                raise

            print('Failed to download google search result, retrying. Reason: ' + str(e))
            sleep(1)
        else:
            break

    return url_list[:limit]


def youtube_search(query, limit):
    """returns a list of [limit] urls to videos that was generated from a youtube search using the [query] as
    search text"""

    url_list = list()

    for tries in range(1, 10):
        try:
            response = retrieve_web_page('https://www.youtube.com/results?search_query=' +
                                         quote(query.encode('utf-8')),
                                         'youtube search result')

        except KeyboardInterrupt:
            raise

        except:
            e = sys.exc_info()[0]
            if tries > 3:
                print('Failed to download google search result. Reason: ' + str(e))
                raise

            print('Failed to download google search result, retrying. Reason: ' + str(e))
            sleep(1)

        else:
            if response:
                soup = BeautifulSoup(response, "html.parser")
                for item in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
                    url = 'https://www.youtube.com' + item['href']
                    url_list.append(url.split('&')[0])
            break

    return url_list[:limit]


def youtube_channel_search(query, limit):
    # todo (1): implement youtube_channel_search.
    print(query + str(limit))


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
    print(tmdb_api_key + tmdb_id)
