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
from data_fetchers import get_tmdb_search_data
import time

parser = argparse.ArgumentParser()
# standard arguments
parser.add_argument("-d", "--directory", help="Directory to use extra-config(s) on.")
parser.add_argument("-c", "--config", help="Extra-config to use on the directory/directories.")

parser.add_argument("-l", "--library", help="Library of directories to use extra-config(s) on.")
parser.add_argument("--config_folder", help="Use each extra-config in the provided config folder.")
parser.add_argument("-f", "--force", action="store_true", help="Force whatever command(s) issued.")
parser.add_argument("-s", "--search", action="store_true", help="Search and download extras for the movie.")
parser.add_argument("--redownload", action="store_true", help="Redownload monitored extras that should "
                                                              "exist in the movie.")

# advanced arguments
parser.add_argument("--delete", action="store_true", help="Delete any monitored extras for the provided extra-configs.")
parser.add_argument("--blacklist", action="store_true", help="Blacklists any missing extras downloaded by the provided "
                                                             "extra-configs.")
parser.add_argument("--replace", action="store_true", help="Deletes and blacklists currently existing extras if it can "
                                                           "find an extra to replace it with. (only work with "
                                                           "extra-configs that manage one extra)")

# administrative commands
parser.add_argument("--rematch", action="store_true", help="Rematch monitored extras file names to new hashes")
parser.add_argument("--clear_record", action="store_true", help="Clear the directory record.")
parser.add_argument("--clear_blacklist", action="store_true", help="Clear the blacklist for the extra-config.")

args = parser.parse_args()

if args.directory and os.path.split(args.directory)[1] == '':
    args.directory = os.path.split(args.directory)[0]

if args.library and os.path.split(args.library)[1] == '':
    args.library = os.path.split(args.library)[0]


def handle_directory(folder):

    def search():
        if args.force:
            directory.completed_configs.remove(extra_config.config_id)
        else:
            if extra_config.config_id in directory.completed_configs:
                return False

        if extra_config.skip_movies_with_existing_trailers and not args.force:

            for file in os.listdir(directory.full_path):
                if file.lower().endswith('trailer.mp4') \
                        or file.lower().endswith('trailer.mkv'):
                    print('movie already have a trailer. skipping.')
                    return False

            if os.path.isdir(os.path.join(directory.full_path, 'trailers')):
                for file in os.listdir(os.path.join(directory.full_path, 'trailers')):
                    if file.lower().endswith('.mp4') \
                            or file.lower().endswith('.mkv'):
                        print('movie already have a trailer. skipping.')
                        return False

        if extra_config.skip_movies_with_existing_theme and not args.force:

            for file in os.listdir(directory.full_path):
                if file.lower().endswith('theme.mp3') \
                        or file.lower().endswith('theme.wma') \
                        or file.lower().endswith('theme.flac'):
                    print('movie already have a theme song. skipping.')
                    return False

            if os.path.isdir(os.path.join(directory.full_path, 'theme-music')):
                for file in os.listdir(os.path.join(directory.full_path, 'theme-music')):
                    if file.lower().endswith('.mp3') \
                            or file.lower().endswith('.wma') \
                            or file.lower().endswith('.flac'):
                        print('movie already have a theme song. skipping.')
                        return False

        directory.update_content()

        if not os.path.isdir(tmp_folder):
            os.mkdir(tmp_folder)

        download_extra(directory, extra_config, tmp_folder)
        directory.completed_configs.append(extra_config.config_id)
        return True

    def redownload():
        pass

    def delete():
        pass

    def blacklist():
        pass

    def replace():
        pass

    def rematch():
        pass

    def clear_record():
        pass

    def clear_blacklist():
        pass

    print('working on directory: "' + os.path.join('...', os.path.split(folder)[1]) + '"')
    for config in configs_content:

        if config.startswith('.') or config.startswith('_'):
            continue

        try:
            if os.path.isfile(os.path.join(records, os.path.split(folder)[1])):
                directory = Directory.load_directory(os.path.join(records, os.path.split(folder)[1]))
            else:
                if has_tmdb_key:
                    directory = Directory(folder, tmdb_api_key=c.get('SETTINGS', 'tmdb_api_key'))
                else:
                    directory = Directory(folder)

            extra_config = ExtraSettings(os.path.join(configs, config))

            if args.clear_blacklist:
                clear_blacklist()

            if args.clear_record:
                clear_record()

            if args.search:
                search()
                directory.save_directory(records)

            elif args.delete:
                delete()

            elif args.redownload:
                redownload()

            elif args.blacklist:
                blacklist()

            elif args.replace:
                replace()

            elif args.rematch:
                rematch()

        except FileNotFoundError as e:
            print('file not found: ' + str(e))
            continue

        except HTTPError:
            print('You might have been flagged by google search. try again tomorrow or don\'t use the google search.')
            sys.exit()

        except URLError:
            print('you might have lost your internet connection. exiting')
            sys.exit()

        except timeout:
            print('you might have lost your internet connection. exiting')
            sys.exit()

        except ConnectionResetError:
            print('you might have lost your internet connection. exiting')
            sys.exit()

        except KeyboardInterrupt:
            print('exiting! keyboard interrupt.')
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

has_tmdb_key = False
if len(c.get('SETTINGS', 'tmdb_api_key')) > 10:
    result = get_tmdb_search_data(c.get('SETTINGS', 'tmdb_api_key'), 'star wars')
    if result is None:
        print('Warning: No working TMDB api key was specified.')
        time.sleep(10)
    else:
        has_tmdb_key = True


if args.directory:
    handle_directory(args.directory)
elif args.library:
    args.replace = False
    handle_library(args.library)
else:
    print('Please specify a directory or a library with the -d or -l argument respectively.')

try:
    shutil.rmtree(tmp_folder)
except FileNotFoundError:
    pass
os.mkdir(tmp_folder)

sys.exit()
