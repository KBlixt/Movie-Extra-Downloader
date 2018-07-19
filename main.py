import os
import shutil
import sys
from _socket import timeout

from extra_finder import ExtraFinder
from directory import Directory
from extra_config import ExtraSettings
import configparser
import re
from urllib.error import URLError
import tools


def download_extra(directory, config, tmp_folder):
    def process_trailers_config(tmp_folder):

        finder = ExtraFinder(directory, config)
        print('processing: ' + directory.name)
        finder.search()
        finder.filter_search_result()

        # for youtube_video in finder.youtube_videos:
        #     print('--------------------------------------------------------------------------------------')
        #     print(youtube_video['webpage_url'])
        #     print(str(youtube_video['adjusted_rating']))
        #     print(youtube_video['format'])
        #     print(str(youtube_video['views_per_day']))
        # print('--------------------------------------------------------------------------------------')
        # print(folder)

        finder.apply_custom_filters()
        finder.order_results()

        if finder.play_trailers:
            if 'duration' in finder.youtube_videos[0] and 'duration' in finder.play_trailers[0]:
                if finder.youtube_videos[0]['duration'] - 23 <= \
                        finder.play_trailers[0]['duration'] <= \
                        finder.youtube_videos[0]['duration'] + 5:
                    finder.youtube_videos = [finder.play_trailers[0]] + finder.youtube_videos
                    print('picked play trailer.')

        for youtube_video in finder.youtube_videos:
            print(youtube_video['webpage_url'] + ' : ' +
                  youtube_video['format'] +
                  ' (' + str(youtube_video['adjusted_rating']) + ')')
        for youtube_video in finder.play_trailers:
            print('play trailer: ' + youtube_video['webpage_url'])
        print('--------------------------------------------------------------------------------------')
        print('downloading for: ' + directory.name)
        count = 0
        while True:
            try:
                while os.listdir(tmp_folder):
                    if count == 0 and not tmp_folder.endswith('_0'):
                        tmp_folder += '_0'
                    else:
                        tmp_folder = tmp_folder[:-2] + '_' + str(count)
                        count += 1
                break
            except FileNotFoundError:
                os.mkdir(tmp_folder)

        downloaded_videos_meta = finder.download_videos(tmp_folder)
########################################################################################################################

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

            directory.record.append(
                {'hash': file_hash,
                 'file_path': os.path.join(directory.full_path, config.extra_type, file),
                 'file_name': file,
                 'youtube_video_id': vid_id,
                 'config_type': config.extra_type})

        def determine_case():
            for content_file, content_file_hash in directory.content.items():
                if content_file == file:
                    return 'name_in_directory'

                if file_hash == content_file_hash:
                    return 'hash_in_directory'

            for sub_content in directory.subdirectories.values():
                for content_file, content_file_hash in sub_content.items():
                    if content_file == file:
                        return 'name_in_directory'
                    if file_hash == content_file_hash:
                        return 'hash_in_directory'

            return ''

        def handle_name_in_directory():
            print('1')
            if force:
                copy_file()
                record_file()
                directory.subdirectories[config.extra_type][file] = file_hash
            else:
                os.remove(source_path)

        def handle_hash_in_directory():
            print('2')
            if force:
                copy_file()
                record_file()
                if config.extra_type in directory.subdirectories:
                    directory.subdirectories[config.extra_type] = {file: file_hash}
                else:
                    directory.subdirectories = {config.extra_type: {file: file_hash}}
            else:
                os.remove(source_path)

        for file in os.listdir(tmp_folder):
            source_path = os.path.join(tmp_folder, file)
            target_path = os.path.join(directory.full_path, config.extra_type, file)

            file_hash = tools.hash_file(source_path)

            if any(file_hash == record['hash'] for record in directory.record):
                os.remove(source_path)
                continue

            case = determine_case()

            if case == 'name_in_directory':
                handle_name_in_directory()
            elif case == 'hash_in_directory':
                handle_hash_in_directory()
            else:
                copy_file()

                if config.extra_type in directory.subdirectories:
                    directory.subdirectories[config.extra_type][file] = file_hash
                else:
                    directory.subdirectories = {config.extra_type: {file: file_hash}}

                record_file()

########################################################################################################################
        directory.completed_configs.append(config.config_id)
        directory.save_directory(records)

        # todo: pick play trailer if it's same length as number one ((+5)-(-20)sec)

    def process_interviews_config():
        pass

    def process_behind_the_scenes_config(tmp_folder):
        finder = ExtraFinder(directory, config)
        print('processing: ' + directory.name)
        finder.search()
        finder.filter_search_result()

        # for youtube_video in finder.youtube_videos:
        #     print('--------------------------------------------------------------------------------------')
        #     print(youtube_video['webpage_url'])
        #     print(str(youtube_video['adjusted_rating']))
        #     print(youtube_video['format'])
        #     print(str(youtube_video['views_per_day']))
        # print('--------------------------------------------------------------------------------------')
        # print(folder)

        finder.apply_custom_filters()
        finder.order_results()
        for youtube_video in finder.youtube_videos:
            print(youtube_video['webpage_url'] + ' : ' +
                  youtube_video['format'] +
                  ' (' + str(youtube_video['adjusted_rating']) + ')')
        for youtube_video in finder.play_trailers:
            print('play trailer: ' + youtube_video['webpage_url'])
        print('--------------------------------------------------------------------------------------')
        print('downloading for: ' + directory.name)
        count = 0
        while True:
            try:
                while os.listdir(tmp_folder):
                    if count == 0 and not tmp_folder.endswith('_0'):
                        tmp_folder += '_0'
                    else:
                        tmp_folder = tmp_folder[:-2] + '_' + str(count)
                        count += 1
                break
            except FileNotFoundError:
                os.mkdir(tmp_folder)

        finder.download_videos(tmp_folder)

########################################################################################################################

        def copy_file():
            if not os.path.isdir(os.path.split(target_path)[0]):
                os.mkdir(os.path.split(target_path)[0])
            shutil.move(source_path, target_path)

        def record_file():
            directory.record.append(
                {'hash': file_hash,
                 'file_path': os.path.join(directory.full_path, config.extra_type, file),
                 'file_name': file,
                 'youtube_video_id': 0,
                 'config_type': config.extra_type})

        def determine_case():
            for content_file, content_file_hash in directory.content.items():
                if content_file == file:
                    return 'name_in_directory'

                if file_hash == content_file_hash:
                    return 'hash_in_directory'

            for sub_content in directory.subdirectories.values():
                for content_file, content_file_hash in sub_content.items():
                    if content_file == file:
                        return 'name_in_directory'
                    if file_hash == content_file_hash:
                        return 'hash_in_directory'

            return ''

        def handle_name_in_directory():
            print('1')
            if force:
                copy_file()
                record_file()
                directory.subdirectories[config.extra_type][file] = file_hash
            else:
                os.remove(source_path)

        def handle_hash_in_directory():
            print('2')
            if force:
                copy_file()
                record_file()
                if config.extra_type in directory.subdirectories:
                    directory.subdirectories[config.extra_type] = {file: file_hash}
                else:
                    directory.subdirectories = {config.extra_type: {file: file_hash}}
            else:
                os.remove(source_path)

        for file in os.listdir(tmp_folder):
            source_path = os.path.join(tmp_folder, file)
            target_path = os.path.join(directory.full_path, config.extra_type, file)

            file_hash = tools.hash_file(source_path)

            if any(file_hash == record['hash'] for record in directory.record):
                os.remove(source_path)
                continue

            case = determine_case()

            if case == 'name_in_directory':
                handle_name_in_directory()
            elif case == 'hash_in_directory':
                handle_hash_in_directory()
            else:
                copy_file()

                if config.extra_type in directory.subdirectories:
                    directory.subdirectories[config.extra_type][file] = file_hash
                else:
                    directory.subdirectories[config.extra_type] = {file: file_hash}

                record_file()

########################################################################################################################
        directory.completed_configs.append(config.config_id)
        directory.save_directory(records)

    def process_featurettes_config():
        pass

    def process_deleted_scenes_config():
        pass

    if config.extra_type == 'trailers':
        process_trailers_config(tmp_folder)
    elif config.extra_type == 'interviews':
        process_interviews_config()
    elif config.extra_type == 'behind the scenes':
        process_behind_the_scenes_config(tmp_folder)
    elif config.extra_type == 'featurettes':
        process_featurettes_config()
    elif config.extra_type == 'deleted scenes':
        process_deleted_scenes_config()


library1 = '\\\BULBASAUR\Plex library\Filmer'
library2 = 'testdir'

c = configparser.ConfigParser()
c.read('default_config.cfg')

tmp_folder = os.path.join(os.path.dirname(sys.argv[0]), 'tmp')

library = library2
library_content = os.listdir(library)

configs = os.path.join(os.path.dirname(sys.argv[0]), 'extra_configs')
configs_content = os.listdir(configs)

records = os.path.join(os.path.dirname(sys.argv[0]), 'records')

force = False

for folder in library_content:
    if re.match("^\\(.*\\)$", folder) or re.match("^\\..*", folder):
        continue
    for config in configs_content:
        try:
            try:
                directory = Directory.load_directory(os.path.join(records, folder))
            except FileNotFoundError:
                directory = Directory(os.path.join(library, folder), c.get('SETTINGS', 'tmdb_api_key'))

            extra_config = ExtraSettings(os.path.join(configs, config))
            if extra_config.config_id in directory.completed_configs and not force:
                continue

            if force:
                old_record = directory.record
                directory.record = list()

            download_extra(directory, extra_config, tmp_folder)

            if force:
                # todo: delete all paths in the old record that are not in the new record
                pass

        except FileNotFoundError as e:
            print('file not found: ' + e.args[0])
            continue

        except URLError:
            print('you might have lost your internet connections. exiting')
            sys.exit()

        except timeout:
            print('you might have lost your internet connections. exiting')
            sys.exit()

        except ConnectionResetError:
            print('you might have lost your internet connections. exiting')
            sys.exit()

        except KeyboardInterrupt:
            sys.exit()
sys.exit()
