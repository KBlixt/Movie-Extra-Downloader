import traceback

from main import download_extra
from extra_config import ExtraSettings
import os
import sys
from directory import Directory
import shutil
from urllib.error import URLError, HTTPError
import configparser
from _socket import timeout
import argparse
import tools
import time

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--directory", help="directory to search extras for")
parser.add_argument("-l", "--library", help="library of directories to search extras for")
parser.add_argument("-f", "--force", action="store_true", help="force scan the directories.")
parser.add_argument("-r", "--replace", action="store_true", help="remove and ban the existing extra.")
args = parser.parse_args()

if args.directory and os.path.split(args.directory)[1] == '':
    args.directory = os.path.split(args.directory)[0]

if args.library and os.path.split(args.library)[1] == '':
    args.library = os.path.split(args.library)[0]


def handle_directory(folder):
    print('working on directory: "' + os.path.join('...', os.path.split(folder)[1]) + '"')
    for config in configs_content:

        if config.startswith('.') or config.startswith('_'):
            continue
        try:
            try:
                directory = Directory.load_directory(os.path.join(records, os.path.split(folder)[1]))
            except FileNotFoundError:
                if has_tmdb_key:
                    directory = Directory(folder, tmdb_api_key=c.get('SETTINGS', 'tmdb_api_key'))
                else:
                    directory = Directory(folder)

            extra_config = ExtraSettings(os.path.join(configs, config))

            if args.replace and 'trailer' in extra_config.extra_type.lower():
                args.force = True

            if extra_config.config_id in directory.completed_configs and not args.force:
                continue

            if extra_config.skip_movies_with_existing_trailers and not args.replace:
                skip = False
                for file in os.listdir(directory.full_path):
                    if file.lower().endswith('trailer.mp4')\
                            or file.lower().endswith('trailer.mkv'):
                        skip = True
                        break
                if skip:
                    print('movie already have a trailer. skipping.')
                    directory.save_directory(records)
                    continue
                if os.path.isdir(os.path.join(directory.full_path, 'trailers')):
                    for file in os.listdir(os.path.join(directory.full_path, 'trailers')):
                        if file.lower().endswith('.mp4')\
                                or file.lower().endswith('.mkv'):
                            skip = True
                            break
                    if skip:
                        print('movie already have a trailer. skipping.')
                        directory.save_directory(records)
                        continue

            if extra_config.skip_movies_with_existing_theme:
                skip = False
                for file in os.listdir(directory.full_path):
                    if file.lower().endswith('theme.mp3')\
                            or file.lower().endswith('theme.wma')\
                            or file.lower().endswith('theme.flac'):
                        skip = True
                        break
                if skip:
                    print('movie already have a theme song. skipping.')
                    directory.save_directory(records)
                    continue
                if os.path.isdir(os.path.join(directory.full_path, 'theme-music')):
                    for file in os.listdir(os.path.join(directory.full_path, 'theme-music')):
                        if file.lower().endswith('.mp3')\
                                or file.lower().endswith('.wma')\
                                or file.lower().endswith('.flac'):
                            skip = True
                            break
                    if skip:
                        print('movie already have a theme song. skipping.')
                        directory.save_directory(records)
                        continue

            directory.update_content()

            if args.force:
                old_record = directory.record
                directory.record = list()
                for record in old_record:
                    if record != extra_config.extra_type:
                        directory.record.append(record)
                extra_config.force = True

            if args.replace:
                directory.banned_youtube_videos_id.append(directory.trailer_youtube_video_id)
                shutil.rmtree(os.path.join(directory.full_path, extra_config.extra_type))
                os.mkdir(os.path.join(directory.full_path, extra_config.extra_type))

            if not os.path.isdir(tmp_folder):
                os.mkdir(tmp_folder)

            download_extra(directory, extra_config, tmp_folder)
            directory.completed_configs.append(extra_config.config_id)
            directory.save_directory(records)

            if args.force:
                # todo: delete all paths in the old record that are not in the new record
                pass

        except FileNotFoundError as e:
            print('file not found: ' + str(e))
            continue

        except HTTPError:
            print('You might have been flagged by google search. try again tomorrow.')
            sys.exit()

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
            print('exiting! keyboard interrupt.')
            sys.exit()


def handle_library(library):
    if args.replace:
        print('the replace mode is unable in library mode, please use the directory mode.')
        return False
    for folder in os.listdir(library):
        if folder.startswith('.'):
            continue
        if not os.path.isdir(os.path.join(library, folder)):
            continue
        try:
            handle_directory(os.path.join(library, folder))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print("----------------------------------------------------------")
            print("----------------------------------------------------------")
            print("----------------------------------------------------------")
            print("----------------------------------------------------------")
            print("----------------------------------------------------------")
            print("--------------------AN ERROR OCCURRED---------------------")
            print("------------------------SKIPPING--------------------------")
            print("------PLEASE REPORT MOVIE TITLE TO THE GITHUB ISSUES------")
            print("-----------------THE SCRIPT WILL CONTINUE-----------------")
            print("----------------------------------------------------------")
            print("-------------------- Exception: --------------------------")
            print(e)
            traceback.print_exc()
            print("----------------------------------------------------------")
            print("----------------------------------------------------------")
            time.sleep(1)

            if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), "failed_movies")):
                os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), "failed_movies"))
            if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), "failed_movies", folder)):
                os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), "failed_movies", folder))
            if library == 'testdir':
                raise
    return True


c = configparser.ConfigParser()
c.read('default_config.cfg')

tmp_folder = os.path.join(os.path.dirname(sys.argv[0]), 'tmp')

configs = os.path.join(os.path.dirname(sys.argv[0]), 'extra_configs')
configs_content = os.listdir(configs)

records = os.path.join(os.path.dirname(sys.argv[0]), 'records')

result = tools.get_tmdb_search_data(c.get('SETTINGS', 'tmdb_api_key'), 'star wars')
if result is None:
    print('Warning: No working TMDB api key was specified.')
    time.sleep(10)
    has_tmdb_key = False
else:
    has_tmdb_key = True


if args.directory:
    handle_directory(args.directory)
elif args.library:
    handle_library(args.library)
else:
    print('please specify a directory (-d) or a library (-l) to search extras for')

try:
    shutil.rmtree(tmp_folder)
except FileNotFoundError:
    pass
os.mkdir(tmp_folder)

sys.exit()
