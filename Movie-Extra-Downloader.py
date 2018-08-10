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
            if extra_config.config_id in directory.completed_configs and not args.force:
                continue

            if extra_config.skip_movies_with_existing_trailers:
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

            directory.update_content()

            if args.force:
                old_record = directory.record
                directory.record = list()
                extra_config.force = True

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
            sys.exit()


def handle_library(library):
    for folder in os.listdir(library):
        if folder.startswith('.'):
            continue
        if not os.path.isdir(os.path.join(library, folder)):
            continue
        handle_directory(os.path.join(library, folder))


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
    print('please specify a directory or a library to search extras for')

try:
    shutil.rmtree(tmp_folder)
except FileNotFoundError:
    pass
os.mkdir(tmp_folder)

sys.exit()
