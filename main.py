import os

from extra_finder import ExtraFinder


def download_extra(directory, config, tmp_folder):
    def process_trailers_config(tmp_folder):

        finder = ExtraFinder(directory, config)
        print('processing: ' + directory.name)
        finder.search()
        finder.filter_search_result()

        for youtube_video in finder.youtube_videos:
            print('--------------------------------------------------------------------------------------')
            print(youtube_video['webpage_url'])
            print(str(youtube_video['adjusted_rating']))
            print(youtube_video['format'])
            print(str(youtube_video['views_per_day']))
        print('--------------------------------------------------------------------------------------')
        print(directory.name)

        finder.apply_custom_filters()
        finder.order_results()

        if finder.play_trailers and finder.youtube_videos and not config.disable_play_trailers:
            if 'duration' in finder.youtube_videos[0] and 'duration' in finder.play_trailers[0]:
                if finder.youtube_videos[0]['duration'] - 23 <= \
                        finder.play_trailers[0]['duration'] <= \
                        finder.youtube_videos[0]['duration'] + 5:
                    finder.youtube_videos = [finder.play_trailers[0]] + finder.youtube_videos
                    print('picked play trailer.')
            if len(finder.youtube_videos) < config.break_limit:
                finder.youtube_videos = [finder.play_trailers[0]] + finder.youtube_videos

        if config.only_play_trailers:
            if finder.play_trailers:
                finder.youtube_videos = [finder.play_trailers[0]]
            else:
                return

        if not finder.youtube_videos and finder.play_trailers and not config.disable_play_trailers:
            finder.youtube_videos = finder.play_trailers

        for youtube_video in finder.youtube_videos:
            print(youtube_video['webpage_url'] + ' : ' +
                  youtube_video['format'] +
                  ' (' + str(youtube_video['adjusted_rating']) + ')')
        for youtube_video in finder.play_trailers:
            print('play trailer: ' + youtube_video['webpage_url'] + ' : ' + youtube_video['format'])
        print('--------------------------------------------------------------------------------------')
        print('downloading for: ' + directory.name)
        count = 0
        tmp_folder = os.path.join(tmp_folder, 'tmp_0')
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
        if downloaded_videos_meta:
            finder.move_videos(downloaded_videos_meta, tmp_folder)

    def process_interviews_config():
        pass

    def process_behind_the_scenes_config():
        pass

    def process_featurettes_config():
        pass

    def process_deleted_scenes_config():
        pass

    if config.extra_type == 'trailers':
        process_trailers_config(tmp_folder)
    elif config.extra_type == 'interviews':
        process_interviews_config()
    elif config.extra_type == 'behind the scenes':
        process_behind_the_scenes_config()
    elif config.extra_type == 'featurettes':
        process_featurettes_config()
    elif config.extra_type == 'deleted scenes':
        process_deleted_scenes_config()

#
# library1 = '/storage/plex/library/Filmer'
# library2 = 'testdir'
#
# c = configparser.ConfigParser()
# c.read('default_config.cfg')
#
# tmp_folder = os.path.join(os.path.dirname(sys.argv[0]), 'tmp')
#
# library = library1
# library_content = os.listdir(library)
#
# configs = os.path.join(os.path.dirname(sys.argv[0]), 'extra_configs')
# configs_content = os.listdir(configs)
#
# records = os.path.join(os.path.dirname(sys.argv[0]), 'records')
#
# force = False
#
# for folder in library_content:
#     if re.match("^\\(.*\\)$", folder) or re.match("^\\..*", folder):
#         continue
#     for config in configs_content:
#         if config.startswith('.'):
#             continue
#         try:
#             try:
#                 directory = Directory.load_directory(os.path.join(records, folder))
#             except FileNotFoundError:
#                 directory = Directory(os.path.join(library, folder), c.get('SETTINGS', 'tmdb_api_key'))
#
#             extra_config = ExtraSettings(os.path.join(configs, config))
#             if extra_config.config_id in directory.completed_configs and not force:
#                 continue
#
#             directory.update_content()
#
#             if force:
#                 old_record = directory.record
#                 directory.record = list()
#                 extra_config.force = True
#
#             if not os.path.isdir(tmp_folder):
#                 os.mkdir(tmp_folder)
#
#
#             download_extra(directory, extra_config, tmp_folder)
#
#             if force:
#                 # todo: delete all paths in the old record that are not in the new record
#                 pass
#
#         except FileNotFoundError as e:
#             print('file not found: ' + str(e.args[0]))
#             continue
#
#         except HTTPError:
#             print('You might have been flagged by google search. try again tomorrow.')
#             sys.exit()
#
#         except URLError:
#             print('you might have lost your internet connections. exiting')
#             sys.exit()
#
#         except timeout:
#             print('you might have lost your internet connections. exiting')
#             sys.exit()
#
#         except ConnectionResetError:
#             print('you might have lost your internet connections. exiting')
#             sys.exit()
#
#         except KeyboardInterrupt:
#             sys.exit()
# try:
#     shutil.rmtree(tmp_folder)
# except FileNotFoundError:
#     pass
# os.mkdir(tmp_folder)
#
# sys.exit()
