from googlesearch import search as google_web_search
from time import sleep
from time import clock
import sys

from urllib.request import HTTPError

import tools
from bs4 import BeautifulSoup
from urllib.request import quote

last = None


def google_search(query, limit):
    global last
    ret_url_list = list()

    for tries in range(1, 10):
        try:
            if last:
                 sleep(int(60 - (clock() - last)))
        except ValueError:
            pass

        last = clock()

        try:
            for url in google_web_search(query, stop=limit):
                if 'youtube.com/watch?v=' in url:
                    ret_url_list.append(url.split('&')[0])

        except KeyboardInterrupt:
            raise

        except HTTPError as e:
            print('google search service unavailable.')
            break

        except:
            e = sys.exc_info()[0]
            if tries > 3:
                print('Failed to download google search result. Reason: ' + str(e))
                raise

            print('Failed to download google search result, retrying. Reason: ' + str(e))
            sleep(1)
        else:
            break

    return ret_url_list[:limit]


def youtube_search(query, limit):

    ret_url_list = list()

    for tries in range(1, 10):
        try:
            response = tools.retrieve_web_page('https://www.youtube.com/results?search_query=' +
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
                    ret_url_list.append(url.split('&')[0])
            break

    return ret_url_list[:limit]


def youtube_channel_search(query, limit):
    # todo (1): implement youtube_channel_search.
    pass
