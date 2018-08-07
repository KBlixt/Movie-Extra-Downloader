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

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--directory", help="directory to search extras for")
parser.add_argument("-l", "--library", help="library of directories to search extras for")
parser.add_argument("-f", "--force", action="store_true", help="force scan the directories.")
args = parser.parse_args()


def handle_directory(folder):
    for config in configs_content:
        if config.startswith('.'):
            continue
        try:
            try:
                directory = Directory.load_directory(os.path.join(records, os.path.split(folder)[1]))
            except FileNotFoundError:
                directory = Directory(folder, c.get('SETTINGS', 'tmdb_api_key'))

            extra_config = ExtraSettings(os.path.join(configs, config))
            if extra_config.config_id in directory.completed_configs and not args.force:
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
            print('file not found: ' + str(e.args[0]))
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

if args.directory:
    handle_directory(args.directory)
elif args.library:
    handle_library(args.library)
else:
    handle_library('/storage/plex/library/Filmer')
    print('please specify a directory or a library to search extras for')

try:
    shutil.rmtree(tmp_folder)
except FileNotFoundError:
    pass
os.mkdir(tmp_folder)

sys.exit()
