import os
import configparser
from configparser import NoOptionError
import fnmatch
import pprint
import shutil
import time
import sys
from urllib.error import URLError
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from socket import timeout
import json

# pip install these packages:
try:
    from googlesearch import search as google_search  # google package
except ImportError:
    print('Please upgrade to python 3.6 or run the 2.7 version.')
    sys.exit()
from pytube import YouTube  # pytube package
from pytube import exceptions
# also, install FFmpeg.


def find_extra(config, extra_name, search, sort_arguments):

    print('Finding video for extra: "' + extra_name + '".')

    time.sleep(1)
    print('Loading configuration.')
    movie_library_dir = config.get('SETTINGS', 'movie_library_dir')
    try:
        download_dir = config.get('SETTINGS', 'download_dir')
    except NoOptionError:
        download_dir = os.getcwd()
    ffmpeg_status = config.getboolean('SETTINGS', 'FFmpeg_installed')

    time.sleep(1)
    print('Loading library.')
    library = get_library_record(movie_library_dir, config)

    time.sleep(1)
    print('finding movie to download extra for')
    movie_folder = get_movie_folder(movie_library_dir, library, [], [extra_name])

    config.set('LIBRARY_RECORD', movie_folder.replace(' ', '_'), str(library[movie_folder] + 1))

    time.sleep(1)
    print('finding video to download for : ' + movie_folder)
    video_to_download = get_video_to_download(movie_folder, search, sort_arguments)
    time.sleep(1)
    print('Downloading: "' + video_to_download['title'] + '" (' + video_to_download['link'] + ")")
    download(video_to_download, download_dir, extra_name, ffmpeg_status)

    time.sleep(1)
    print('Moving "' + extra_name + '" and cleaning up')
    move_and_cleanup(download_dir, os.path.join(movie_library_dir, movie_folder), extra_name + '.mp4')

    print('All done!')
    return True


def get_library_record(library_dir, config):

    library = dict()

    for folder_name in os.listdir(library_dir):
        if fnmatch.fnmatch(folder_name, config.get('SETTINGS', 'name_pattern')):
            if not config.has_option('LIBRARY_RECORD', folder_name.replace(' ', '_')):
                new_entry = 0
            else:
                new_entry = int(config.getint('LIBRARY_RECORD', folder_name.replace(' ', '_')))

            library[folder_name] = new_entry
    return library


def get_movie_folder(library_dir, earlier_tries, have, have_not):

    min_earlier_tries = 10000
    max_earlier_tries = 0

    for movie in earlier_tries:
        if earlier_tries[movie] < min_earlier_tries:
            min_earlier_tries = earlier_tries[movie]

        if earlier_tries[movie] > max_earlier_tries:
            max_earlier_tries = earlier_tries[movie]

    while min_earlier_tries <= max_earlier_tries:

        for movie in earlier_tries:

            if earlier_tries[movie] > min_earlier_tries:
                continue

            return_movie = True

            for file_name in os.listdir(os.path.join(library_dir, movie)):
                for word in have:
                    if word not in file_name:
                        return_movie = False

            for file_name in os.listdir(os.path.join(library_dir, movie)):
                for word in have_not:
                    if word in file_name:
                        return_movie = False

            if return_movie:
                return movie

        min_earlier_tries += 1

    print("Couldn't find a movie in the library matching the given restriction.")
    print("Or all movies already have the extra you are looking for.")
    print('Shutting down.')
    sys.exit()


def get_video_to_download(movie, search_suffix, filter_arguments):

    def scan_response(response):

        response['max_video_resolution'] = 0
        for result in response['items']:

            result['delete_this_item'] = False

            video = None
            for try_count in range(5):

                if try_count > 2:
                    time.sleep(1)
                    video = YouTube(result['link'])
                else:
                    try:
                        video = YouTube(result['link'])
                        break
                    except KeyError:
                        print('Pytube failed to initialize (KeyError). trying again in 10 seconds.')
                        time.sleep(9)
                    except URLError:
                        print('Pytube failed to initialize (URLError). trying again in 10 seconds.')
                        time.sleep(9)
                    except exceptions.RegexMatchError:
                        result['delete_this_item'] = True
                        break

            if result['delete_this_item']:
                continue

            result['youtube_object'] = video
            result['title'] = video.title
            result['avg_rating'] = float(video.player_config_args['avg_rating'])
            result['view_count'] = int(video.player_config_args['view_count'])

            if result['view_count'] < 60:
                result['view_count'] = 60

            result['video_resolution'] = 0
            for stream in video.streams.filter(type='video').all():
                try:
                    resolution = int(stream.resolution.replace('p', ''))
                except AttributeError:
                    resolution = 0

                if resolution > response['max_video_resolution']:
                    response['max_video_resolution'] = resolution
                if resolution > result['video_resolution']:
                    result['video_resolution'] = resolution

            try:
                if 'ad_preroll' in video.player_config_args:
                    result['adds_info'] = 'have adds'
                else:
                    result['adds_info'] = 'No adds'
            except ValueError:
                result['adds_info'] = 'No adds'

        return response

    def filter_response(response, arguments):

        items = list()

        for result in response['items']:

            append_video = True

            if result['delete_this_item']:
                continue

            for word in arguments['video_name_must_contain']:
                if word.lower() not in result['title'].lower():
                    append_video = False

            for word in arguments['video_name_must_not_contain']:
                if word.lower() in result['title'].lower():
                    append_video = False

            if append_video:
                items.append(result)

        response.pop('items')
        response['items'] = items

        return response

    def score_response(response, scoring_arguments):

        for result in response['items']:

            result['true_rating'] = result['avg_rating'] * (1 - 1 / ((result['view_count'] / 60) ** 0.5))

            if result['video_resolution'] < 700:
                result['true_rating'] *= 0.90
                result['view_count'] *= 0.5

            for bonus in scoring_arguments['video_name_tag_bonuses']:
                for word in scoring_arguments['video_name_tag_bonuses'][bonus]:
                    if word in result['title'].lower():
                        result['true_rating'] *= bonus
                        result['view_count'] *= bonus
                        break

        return response

    # search for movie
    search = movie.replace('(', '').replace(')', '').replace('[', '').replace(']', '') + ' ' + search_suffix
    search = search.replace('.', ' ').replace('_', ' ').replace('-', ' ').replace('  ', ' ').replace('  ', ' ')
    search = str('site:youtube.com ' + search)

    item_list = list()
    for attempt in range(5):
        if attempt > 2:
            for url in google_search(search, stop=10):
                item = {'link': url}
                item_list.append(item)
            break
        else:
            try:
                for url in google_search(search, stop=10):
                    item = {'link': url}
                    item_list.append(item)
                break
            except URLError:
                print('Failed to retrieve search results, trying again in 10 seconds')
                time.sleep(10)
                continue

    item_list.pop()
    item_list.pop()
    item_list.pop()
    search_response = {'items': item_list}

    search_response = scan_response(search_response)
    search_response = filter_response(search_response, filter_arguments)
    search_response = score_response(search_response, filter_arguments)

    # select video
    selected_movie = None

    top_score = 0
    top_view_count = 0

    for item in search_response['items']:

        print('-----------------------------------------------------------------')
        print(item['title'])
        print(item['adds_info'])
        print(item['video_resolution'])
        print(item['link'])
        print(item['true_rating'])
        print(item['view_count'])

        if item['true_rating'] > top_score:
            top_score = item['true_rating']

    for item in search_response['items']:
        if item['true_rating'] > top_score * 0.95:
            if item['view_count'] > top_view_count:
                top_view_count = item['view_count']
                selected_movie = item

    return selected_movie


def download(youtube_video, download_dir, file_name, ffmpeg_status):
    def get_best_adaptive_audio_stream(stream_list):

        max_bit_rate = 0
        top_audio_stream = None
        preferable_max_bit_rate = 0
        preferable_top_audio_stream = None

        for audio_stream in stream_list.streams.filter(type='audio', progressive=False).all():

            if audio_stream.is_progressive \
                    or audio_stream.resolution != '0p' \
                    or audio_stream.video_codec != 'unknown':
                continue

            bit_rate = int(audio_stream.abr.replace('kbps', ''))

            if bit_rate > max_bit_rate:
                max_bit_rate = bit_rate
                top_audio_stream = audio_stream

            if bit_rate > preferable_max_bit_rate and 'mp4a' in audio_stream.audio_codec.lower():
                preferable_max_bit_rate = bit_rate
                preferable_top_audio_stream = audio_stream

        if preferable_max_bit_rate * 1.7 > max_bit_rate:
            return preferable_top_audio_stream
        else:
            return top_audio_stream

    def get_best_adaptive_video_stream(stream_list):

        max_resolution = 0
        top_video_stream = None
        preferable_max_resolution = 0
        preferable_top_video_stream = None

        for video_stream in stream_list.streams.filter(type='video').all():

            if video_stream.is_progressive \
                    or video_stream.abr != '25kbps' \
                    or video_stream.audio_codec != 'unknown':
                continue

            resolution = int(video_stream.resolution.replace('p', ''))

            if resolution > max_resolution:
                max_resolution = resolution
                top_video_stream = video_stream

            if resolution > 1080:
                continue

            if resolution > preferable_max_resolution and 'avc' in video_stream.video_codec.lower():
                preferable_max_resolution = resolution
                preferable_top_video_stream = video_stream

        if preferable_max_resolution == max_resolution:
            return preferable_top_video_stream
        else:
            return top_video_stream

    def get_best_progressive_stream(stream_list):

        max_resolution = 0
        selected_stream = None

        for progressive_stream in stream_list.streams.filter(progressive=True).all():

            resolution = int(progressive_stream.resolution.replace('p', ''))

            if resolution > max_resolution:
                max_resolution = resolution

        max_score = 0
        for progressive_stream in stream_list.streams.filter().all():

            score = 0
            resolution = int(progressive_stream.resolution.replace('p', ''))
            bit_rate = int(progressive_stream.abr.replace('kbps', ''))
            if not ffmpeg_status:
                if progressive_stream.subtype.lower() == 'mp4':
                    score += 1000000000
            if resolution == max_resolution:
                score += 10000
            if 'avc' in progressive_stream.video_codec.lower():
                score += 1000
            if 'mp4a' in progressive_stream.audio_codec.lower():
                score += bit_rate * 1.7
            else:
                score += bit_rate

            if score > max_score:
                max_score = score
                selected_stream = progressive_stream

        return selected_stream

    def download_adaptive_streams(video_stream, audio_stream, target_dir, target_file_name):

        for attempt in range(5):
            if attempt > 2:
                video_stream.download(target_dir, 'video')
                break
            else:
                try:
                    video_stream.download(target_dir, 'video')
                    break
                except URLError:
                    print('Failed to download video stream, trying again in 10 seconds')
                    time.sleep(10)
                    continue

        for attempt in range(5):
            if attempt > 2:
                audio_stream.download(target_dir, 'audio')
                break
            else:
                try:
                    audio_stream.download(target_dir, 'audio')
                    break
                except URLError:
                    print('Failed to download audio stream, trying again in 10 seconds')
                    time.sleep(10)
                    continue

        if 'avc' in video_stream.video_codec.lower():
            video_encode_parameters = 'copy'
        else:
            video_encode_parameters = 'libx264 -preset slow -crf 18'

        if 'mp4a' in audio_stream.audio_codec.lower():
            audio_encode_parameters = 'copy'
        else:
            audio_encode_parameters = 'aac -strict -2 -b:a 128k'

        os.system('ffmpeg -i "' + os.path.join(target_dir, 'video') + '".* '
                  '-i "' + os.path.join(target_dir, 'audio') + '".* '
                  '-c:v ' + video_encode_parameters + ' '
                  '-c:a ' + audio_encode_parameters + ' '
                  '-threads 4 '
                  '"' + os.path.join(target_dir, target_file_name + '.mp4') + '" -y')

    def download_progressive_streams(progressive_stream, target_dir, target_file_name):

        if progressive_stream.subtype.lower() == 'mp4':

            for attempt in range(5):
                if attempt > 2:
                    progressive_stream.download(target_dir, target_file_name)
                    break
                else:
                    try:
                        progressive_stream.download(target_dir, target_file_name)
                        break
                    except URLError:
                        print('Failed to download progressive stream, trying again in 10 seconds')
                        time.sleep(10)
                        continue
            return
        else:

            for attempt in range(5):
                if attempt > 2:
                    progressive_stream.download(target_dir, 'progressive')
                    break
                else:
                    try:
                        progressive_stream.download(target_dir, 'progressive')
                        break
                    except URLError:
                        print('Failed to download progressive stream, trying again in 10 seconds')
                        time.sleep(10)
                        continue

        if 'avc' in progressive_stream.video_codec.lower():
            video_encode_parameters = 'copy'
        else:
            video_encode_parameters = 'libx264 -preset slow -crf 18'

        if 'mp4a' in progressive_stream.audio_codec.lower():
            audio_encode_parameters = 'copy'
        else:
            audio_encode_parameters = 'aac -strict -2 -b:a 128k'

        os.system('ffmpeg -i "' + os.path.join(target_dir, 'progressive') + '".* '
                  '-c:v ' + video_encode_parameters + ' '
                  '-c:a ' + audio_encode_parameters + ' '
                  '-threads 4 '
                  '"' + os.path.join(target_dir, target_file_name + '.mp4') + '" -y')

    # decide adaptive streams to get
    video = youtube_video['youtube_object']
    for stream in video.streams.all():

        if stream.abr is None:
            stream.abr = '25kbps'
        if stream.audio_codec is None:
            stream.audio_codec = 'unknown'
        if stream.resolution is None:
            stream.resolution = '0p'
        if stream.video_codec is None:
            stream.video_codec = 'unknown'
    print('---------------------------------------------------------------------------------------------------')
    print(pprint.pprint(video.streams.all()))
    print('---------------------------------------------------------------------------------------------------')
    best_audio_stream = get_best_adaptive_audio_stream(video)
    best_video_stream = get_best_adaptive_video_stream(video)
    best_progressive_stream = get_best_progressive_stream(video)
    print(pprint.pprint(best_progressive_stream))
    print(pprint.pprint(best_video_stream))
    print(pprint.pprint(best_audio_stream))
    print('---------------------------------------------------------------------------------------------------')

    if 'mp4a' in best_audio_stream.audio_codec.lower():
        best_audio_stream.abr = int(best_audio_stream.abr.replace('kbps', '')) * 1.7
    if 'mp4a' in best_progressive_stream.audio_codec.lower():
        best_progressive_stream.abr = int(best_progressive_stream.abr.replace('kbps', '')) * 1.7

    # decide to get adaptive or progressive
    if not ffmpeg_status:
        print('Picked the progressive streams because the ffmpeg_installed setting is false.')
        download_progressive_streams(best_progressive_stream, download_dir, file_name)

    elif int(best_video_stream.resolution.replace('p', '')) > int(best_progressive_stream.resolution.replace('p', '')):
        print('Picked the adaptive streams because of higher video resolution.')
        download_adaptive_streams(best_video_stream, best_audio_stream, download_dir, file_name)

    elif 'avc' not in best_progressive_stream.video_codec.lower() and 'avc' in best_video_stream.video_codec.lower():
        print('Picked the adaptive streams because of better video codec.')
        download_adaptive_streams(best_video_stream, best_audio_stream, download_dir, file_name)

    elif best_audio_stream.abr > best_progressive_stream.abr * 0.9:
        print('Picked the adaptive streams because of better audio.')
        download_adaptive_streams(best_video_stream, best_audio_stream, download_dir, file_name)

    else:
        print('Picked the progressive stream.')
        download_progressive_streams(best_progressive_stream, download_dir, file_name)

    return


def move_and_cleanup(source_dir, target_dir, file_name):

    # moving file
    if not os.path.isfile(os.path.join(target_dir, file_name)):
        shutil.move(os.path.join(source_dir, file_name), os.path.join(target_dir, file_name))
    else:
        os.remove(os.path.join(source_dir, file_name))
    # deleting downloaded files

    for folder_name in os.listdir(source_dir):
        if fnmatch.fnmatch(folder_name, 'audio.*'):
            os.remove(os.path.join(source_dir, folder_name))
        if fnmatch.fnmatch(folder_name, 'video.*'):
            os.remove(os.path.join(source_dir, folder_name))
        if fnmatch.fnmatch(folder_name, 'progressive.*'):
            os.remove(os.path.join(source_dir, folder_name))


def get_official_trailer(config):
    #################################################################
    # Video constrains:
    extra_name = 'Official Trailer-trailer'
    search_suffix = ' Trailer'
    video_name_must_contain = ['trailer']
    video_name_must_not_contain = ['Side-by-Side', 'Side by Side', 'SidebySide']
    video_name_tag_bonuses = {
        1.01: ['official'],
        0.99: ['preview', 'teaser']
    }
    #################################################################

    filter_arguments = {'video_name_must_contain': video_name_must_contain,
                        'video_name_must_not_contain': video_name_must_not_contain,
                        'video_name_tag_bonuses': video_name_tag_bonuses}

    find_extra(config, extra_name, search_suffix, filter_arguments)


def get_remastered_trailer(config):

    #################################################################
    # Video constrains:
    extra_name = 'Remastered Trailer-trailer'
    search_suffix = ' Remastered Trailer'
    video_name_must_contain = ['trailer', 'remaster']
    video_name_must_not_contain = ['Side-by-Side', 'Side by Side', 'SidebySide']
    video_name_tag_bonuses = {
        0.8: ['preview', 'teaser'],
        1.05: ['fan']
    }
    #################################################################

    filter_arguments = {'video_name_must_contain': video_name_must_contain,
                        'video_name_must_not_contain': video_name_must_not_contain,
                        'video_name_tag_bonuses': video_name_tag_bonuses}

    find_extra(config, extra_name, search_suffix, filter_arguments)

def retrieve_web_page(url, page_name='page'):

    response = None
    print('Downloading ' + page_name + '.')
    for attempt in range(20):
        try:
            response = urlopen(url, timeout=2)
            break
        except timeout:
            print('Failed to download ' + page_name + ' : timed out. Trying again in 2 seconds.')
            time.sleep(2)
            if attempt > 8:
                print('You might have lost internet connection.')
                print('Breaking out of loop and committing')
                sys.exit()
        except HTTPError as e:
            raise ValueError('Failed to download ' + page_name + ' : ' + e.msg + '. Skipping.')
        except URLError:
            print('Failed to download ' + page_name + '. Trying again in 2 seconds')
            time.sleep(2)
            if attempt > 8:
                print('You might have lost internet connection.')
                print('Breaking out of loop and committing')
                sys.exit()

    return response

def get_tmdb_movie_id(movie):
    if len(movie['imdb_id']) != 9:
        raise ValueError("Movie have no IMDB ID. Skipping.")

    response = retrieve_web_page('https://api.themoviedb.org/3/find/'
                                 + movie['imdb_id'] +
                                 '?api_key=' + tmdb_api_key +
                                 '&language=en-US'
                                 '&external_source=imdb_id', 'tmdb id')

    data = json.loads(response.read().decode('utf-8'))

    if len(data['movie_results']) == 0:
        raise ValueError('Unable to find TMDB ID. Skipping.')

    movie['tmdb_id'] = str(data['movie_results'][0]['id'])
    response.close()


config_file = 'default_config.cfg'
conf = configparser.ConfigParser()

while True:
    try:
        conf.read(config_file)
        if conf.getboolean('SETTINGS', 'search_for_remastered'):
            get_remastered_trailer(conf)
        else:
            get_official_trailer(conf)

        with open(config_file, 'w') as new_config_file:
            conf.write(new_config_file)
            new_config_file.close()

        time.sleep(conf.getint('SETTINGS', 'cooldown'))

    except ValueError as error:
        print(error)
        print('pytube failed to initialize after 3 attempts, try again at a later date.')
    time.sleep(10)
