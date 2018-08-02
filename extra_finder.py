import os
from youtube_dl import DownloadError
import tools as tools
import youtube_dl
import url_finders
from bisect import bisect
from datetime import date
import time
import shutil


class ExtraFinder:

    conn_errors = 0

    def __init__(self, directory, extra_config):

        self.directory = directory
        self.config = extra_config
        self.complete = True

        self.youtube_videos = list()
        self.play_trailers = list()

    def search(self):

        def create_youtube_video():

            def get_video_data():

                for tries in range(1, 11):

                    try:

                        with youtube_dl.YoutubeDL({'socket_timeout': '3'}) as ydl:
                            return ydl.extract_info(url, download=False)

                    except DownloadError as e:

                        if 'ERROR: Unable to download webpage:' in e.args[0]:

                            if tries > 3:
                                print('hey, there: error!!!')
                                raise

                            print('failed to get video data, retrying')
                            time.sleep(1)
                        else:
                            return None

            youtube_video = get_video_data()

            if not youtube_video:
                return None

            youtube_video['title'] = tools.get_clean_string(youtube_video['title'])

            if youtube_video['view_count'] < 100:
                youtube_video['view_count'] = 100

            youtube_video['adjusted_rating'] = \
                youtube_video['average_rating'] * (1 - 1 / ((youtube_video['view_count'] / 60) ** 0.5))

            youtube_video['resolution_ratio'] = youtube_video['width'] / youtube_video['height']

            if 'resolution' not in youtube_video or not youtube_video['resolution']:
                resolution = max(int(youtube_video['height']),
                                 int(youtube_video['width'] / 16 * 9))
                resolutions = [144, 240, 360, 480, 720, 1080, 1440, 2160]

                youtube_video['resolution'] = resolutions[bisect(resolutions, resolution * 1.2) - 1]

            if youtube_video['upload_date']:
                date_str = youtube_video['upload_date']
                upload_date = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
                time_delta = date.today() - upload_date
                youtube_video['views_per_day'] = (youtube_video['view_count'] /
                                                  (365 + time_delta.total_seconds() / 60 / 60 / 24))

            else:
                print('no "upload_date"!!!')
            return youtube_video

        url_list = list()

        for search_index, search in self.config.searches.items():
            query = tools.apply_query_template(search['query'], self.directory.__dict__)
            limit = int(search['limit'])

            if search['source'] == 'google_search':
                urls = url_finders.google_search(query, limit)

            elif search['source'] == 'youtube_search':
                urls = url_finders.youtube_search(query, limit)

            elif search['source'] == 'google_channel_search':
                urls = url_finders.youtube_channel_search(query, limit)

            else:
                print("The search engine \"" + search['source'] + "\" wasn't recognized. Skipping.")
                print('Please use "google_search", "youtube_search" or "youtube_channel_search" as the source.')
                continue

            if urls:
                url_list += urls

        for url in list(set(url_list)):
            if not any(url in youtube_video['webpage_url']
                       or youtube_video['webpage_url'] in url
                       for youtube_video in self.youtube_videos):
                if 'youtube.com/watch?v=' not in url:
                    continue
                video = create_youtube_video()

                if video:
                    self.youtube_videos.append(video)
                    if not video['categories']:
                        self.play_trailers.append(video)
        return

    def filter_search_result(self):

        filtered_candidates = list()

        for youtube_video in self.youtube_videos:

            info = 'Video "' + youtube_video['webpage_url'] + '" was removed. reasons: '
            append_video = True

            for year in self.directory.banned_years:
                if str(year) in youtube_video['title'].lower():
                    append_video = False
                    info += 'containing banned year in title, '
                    break
                if any(str(year) in tag.lower() for tag in youtube_video['tags']):
                    append_video = False
                    info += 'containing banned year in tags, '
                    break

            buffer = 0
            if len(self.directory.banned_title_keywords) > 3:
                buffer = 1
            if len(self.directory.banned_title_keywords) > 10:
                buffer = 2
            for keyword in self.directory.banned_title_keywords:
                if ' ' + keyword.lower() + ' ' in ' ' + youtube_video['title'].lower() + ' ':
                    buffer -= 1
                    if buffer < 0:
                        append_video = False
                        info += 'containing banned similar title keywords, '
                        break

            for phrases in self.config.required_phrases:
                if not any(phrase.lower() in youtube_video['title'].lower() for phrase in phrases.split('|')):
                    append_video = False
                    info += 'not containing a required phrase, '
                    break

            for phrase in self.config.banned_phrases:
                if phrase.lower() in youtube_video['title'].lower():
                    append_video = False
                    info += 'containing a banned phrase, '
                    break

            for channel in self.config.banned_channels:
                if channel.lower() == youtube_video['uploader'].lower():
                    append_video = False
                    info += 'made by a banned channel, '
                    break

            title_in_video = False
            original_title_in_video = False

            buffer = 0
            if len(self.directory.movie_title_keywords) > 3:
                buffer = 1
            if len(self.directory.movie_title_keywords) > 7:
                buffer = 2

            for keyword in self.directory.movie_title_keywords:
                if keyword.lower() not in youtube_video['title'].lower():
                    buffer -= 1
                    if buffer < 0:
                        break
            else:
                title_in_video = True

            if self.directory.movie_original_title is not None:
                buffer = int(len(self.directory.movie_original_title_keywords) / 4 + 0.1)

                for keyword in self.directory.movie_original_title_keywords:
                    if keyword.lower() not in youtube_video['title'].lower():
                        buffer -= 1
                        if buffer < 0:
                            break
                else:
                    original_title_in_video = True

            if not original_title_in_video and not title_in_video:
                append_video = False
                info += 'not containing title, '

            if append_video:
                filtered_candidates.append(youtube_video)
            else:
                print(info[:-2] + '.')

        self.youtube_videos = filtered_candidates

        filtered_candidates = list()

        for youtube_video in self.play_trailers:

            info = 'Video "' + youtube_video['webpage_url'] + '" was removed. reasons: '
            append_video = True

            for year in self.directory.banned_years:
                if str(year) in youtube_video['title'].lower():
                    append_video = False
                    info += 'containing banned year in title, '
                    break
                if any(str(year) in tag.lower() for tag in youtube_video['tags']):
                    append_video = False
                    info += 'containing banned year in tags, '
                    break

            buffer = 0
            if len(self.directory.banned_title_keywords) > 3:
                buffer = 1
            if len(self.directory.banned_title_keywords) > 6:
                buffer = 2
            for keyword in self.directory.banned_title_keywords:
                if ' ' + keyword.lower() + ' ' in ' ' + youtube_video['title'].lower() + ' ':
                    buffer -= 1
                    if buffer < 0:
                        append_video = False
                        info += 'containing banned similar title keywords, '
                        break

            title_in_video = False
            original_title_in_video = False

            buffer = 0
            if len(self.directory.movie_title_keywords) > 3:
                buffer = 1
            if len(self.directory.movie_title_keywords) > 7:
                buffer = 2

            for keyword in self.directory.movie_title_keywords:
                if keyword.lower() not in youtube_video['title'].lower():
                    buffer -= 1
                    if buffer < 0:
                        break
            else:
                title_in_video = True

            if self.directory.movie_original_title is not None:
                buffer = int(len(self.directory.movie_original_title_keywords) / 4 + 0.1)

                for keyword in self.directory.movie_original_title_keywords:
                    if keyword.lower() not in youtube_video['title'].lower():
                        buffer -= 1
                        if buffer < 0:
                            break
                else:
                    original_title_in_video = True

            if not original_title_in_video and not title_in_video:
                append_video = False
                info += 'not containing title, '

            if append_video:
                filtered_candidates.append(youtube_video)
            else:
                print(info[:-2] + '.')

        self.play_trailers = filtered_candidates

    def apply_custom_filters(self):

        def absolute():

            minimum = filter_args[0] == 'min'
            ret = list()

            for youtube_video in filtered_list:
                if minimum:
                    if youtube_video[key] >= limit_value:
                        ret.append(youtube_video)
                else:
                    if youtube_video[key] <= limit_value:
                        ret.append(youtube_video)
            return ret

        def relative():

            minimum = filter_args[0] == 'min'
            ret = list()
            max_value = float('-inf')

            for youtube_video in filtered_list:
                video_value = youtube_video[key]
                if video_value > max_value:
                    max_value = video_value

            for youtube_video in filtered_list:
                if minimum:
                    if youtube_video[key] >= max_value * limit_value:
                        ret.append(youtube_video)
                else:
                    if youtube_video[key] <= max_value * limit_value:
                        ret.append(youtube_video)
            return ret

        def highest():
            keep = filter_args[0] == 'keep'

            ret = sorted(filtered_list, key=lambda x: x[key], reverse=True)

            if keep:
                if len(ret) > limit_value:
                    ret = ret[:limit_value]
                else:
                    ret = ret
            else:
                if len(ret) > limit_value:
                    ret = ret[limit_value:]
                else:
                    ret = list()

            return ret

        def lowest():
            keep = filter_args[0] == 'keep'

            ret = sorted(filtered_list, key=lambda x: x[key])

            if keep:
                if len(ret) > limit_value:
                    ret = ret[:limit_value]
                else:
                    ret = ret
            else:
                if len(ret) > limit_value:
                    ret = ret[limit_value:]
                else:
                    ret = list()

            return ret

        filtered_list = None

        for filter_package in self.config.custom_filters:

            filtered_list = list(self.youtube_videos)

            for data in filter_package:
                filter_args = data.split(':::')[0].split('_')
                limit_value = float(data.split(':::')[1])
                try:
                    int(filter_args[-1])
                except ValueError:
                    key = '_'.join(filter_args[2:])
                else:
                    key = '_'.join(filter_args[2:-1])

                if filter_args[1] == 'relative':
                    filtered_list = relative()
                if filter_args[1] == 'absolute':
                    filtered_list = absolute()
                if filter_args[1] == 'highest':
                    filtered_list = highest()
                if filter_args[1] == 'lowest':
                    filtered_list = lowest()
            if self.play_trailers and self.config.extra_type == 'trailers':
                if len(filtered_list) + 1 >= self.config.break_limit:
                    break
            else:
                if len(filtered_list) >= self.config.break_limit:
                    break

        self.youtube_videos = filtered_list

        return

    def order_results(self):

        attribute_tuple = self.config.priority_order.split('_')
        highest = attribute_tuple[0] == 'highest'
        key = '_'.join(attribute_tuple[1:])

        if highest:
            self.youtube_videos = sorted(self.youtube_videos, key=lambda x: x[key], reverse=True)
        else:
            self.youtube_videos = sorted(self.youtube_videos, key=lambda x: x[key])

        preferred_videos = list()
        not_preferred_channels = list()

        for youtube_video in self.youtube_videos:
            if youtube_video['uploader'] in self.config.preferred_channels:
                preferred_videos.append(youtube_video)
            else:
                not_preferred_channels.append(youtube_video)

        self.youtube_videos = preferred_videos + not_preferred_channels

    def download_videos(self, tmp_file):

        downloaded_videos_meta = list()

        arguments = self.config.youtube_dl_arguments
        arguments['outtmpl'] = os.path.join(tmp_file, arguments['outtmpl'])
        for key, value in arguments.items():
            if isinstance(value, str):
                if value.lower() == 'false' or value.lower() == 'no':
                    arguments[key] = ''

        count = 0

        for youtube_video in self.youtube_videos[:]:
            if not self.config.force:
                for vid_id in self.directory.record:
                    if vid_id == youtube_video['id']:
                        continue

            for tries in range(1, 11):
                try:
                    with youtube_dl.YoutubeDL(arguments) as ydl:
                        meta = ydl.extract_info(youtube_video['webpage_url'])
                        downloaded_videos_meta.append(meta)
                        count += 1
                        break

                except DownloadError as e:
                    if tries > 3:
                        if str(e).startswith('ERROR: Did not get any data blocks'):
                            return
                        print('failed to download the video.')
                        break
                    print('failed to download the video. retrying')
                    time.sleep(3)

            if count >= self.config.videos_to_download:
                break

        return downloaded_videos_meta

    def move_videos(self, downloaded_videos_meta, tmp_folder):

        def copy_file():
            if not os.path.isdir(os.path.split(target_path)[0]):
                os.mkdir(os.path.split(target_path)[0])
            shutil.move(source_path, target_path)

        def record_file():
            vid_id = 'unknown'
            for meta in downloaded_videos_meta:
                if meta['title'] + '.' + meta['ext'] == file:
                    vid_id = meta['id']
                    break

            self.directory.record.append(
                {'hash': file_hash,
                 'file_path': os.path.join(self.directory.full_path, self.config.extra_type, file),
                 'file_name': file,
                 'youtube_video_id': vid_id,
                 'config_type': self.config.extra_type})

        def determine_case():
            for content_file, content_file_hash in self.directory.content.items():
                if content_file == file:
                    return 'name_in_directory'

                if file_hash == content_file_hash:
                    return 'hash_in_directory'

            for sub_content in self.directory.subdirectories.values():
                for content_file, content_file_hash in sub_content.items():
                    if content_file == file:
                        return 'name_in_directory'
                    if file_hash == content_file_hash:
                        return 'hash_in_directory'

            return ''

        def handle_name_in_directory():
            if self.config.force:
                copy_file()
                record_file()
                self.directory.subdirectories[self.config.extra_type][file] = file_hash
            else:
                os.remove(source_path)

        def handle_hash_in_directory():
            if self.config.force:
                copy_file()
                record_file()
                if self.config.extra_type in self.directory.subdirectories:
                    self.directory.subdirectories[self.config.extra_type] = {file: file_hash}
                else:
                    self.directory.subdirectories = {self.config.extra_type: {file: file_hash}}
            else:
                os.remove(source_path)

        for file in os.listdir(tmp_folder):
            source_path = os.path.join(tmp_folder, file)
            target_path = os.path.join(self.directory.full_path, self.config.extra_type, file)

            file_hash = tools.hash_file(source_path)

            if any(file_hash == record['hash'] for record in self.directory.record):
                os.remove(source_path)
                continue

            case = determine_case()

            if case == 'name_in_directory':
                handle_name_in_directory()
            elif case == 'hash_in_directory':
                handle_hash_in_directory()
            else:
                copy_file()

                if self.config.extra_type in self.directory.subdirectories:
                    self.directory.subdirectories[self.config.extra_type][file] = file_hash
                else:
                    self.directory.subdirectories = {self.config.extra_type: {file: file_hash}}

                record_file()
