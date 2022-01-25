import configparser
import codecs
import json

import tools as tools


class ExtraSettings:

    # todo: make into dictionary.

    # todo (0): make sure nothing fails to import.

    def __init__(self, config_path):

        with codecs.open(config_path, 'r', 'utf-8') as file:
            self.config = configparser.RawConfigParser()
            self.config.read_file(file)

        self.extra_type = self.config['EXTRA_CONFIG'].get('extra_type')
        self.config_id = self.config['EXTRA_CONFIG'].get('config_id')
        self.force = self.config['EXTRA_CONFIG'].getboolean('force')

        self.searches = self.get_searches()

        self.required_phrases = \
            tools.make_list_from_string(self.config['FILTERING'].get('required_phrases').replace('\n', ''))
        self.banned_phrases = \
            tools.make_list_from_string(self.config['FILTERING'].get('banned_phrases').replace('\n', ''))
        self.banned_channels = \
            tools.make_list_from_string(self.config['FILTERING'].get('banned_channels').replace('\n', ''))

        self.custom_filters = self.get_custom_filters()
        self.last_resort_policy = self.config['DOWNLOADING_AND_POSTPROCESSING'].get('last_resort_policy')

        self.priority_order = self.config['PRIORITY_RULES'].get('order')
        self.preferred_channels = \
            tools.make_list_from_string(self.config['PRIORITY_RULES'].get('preferred_channels', "").replace('\n', ''))

        self.videos_to_download = self.config['DOWNLOADING_AND_POSTPROCESSING'].getint('videos_to_download', 1)
        self.naming_scheme = self.config['DOWNLOADING_AND_POSTPROCESSING'].get('naming_scheme')
        self.youtube_dl_arguments = json.loads(self.config['DOWNLOADING_AND_POSTPROCESSING'].get('youtube_dl_arguments'))

        self.disable_play_trailers = self.config['EXTRA_CONFIG'].getboolean('disable_play_trailers', False)
        self.only_play_trailers = self.config['EXTRA_CONFIG'].getboolean('only_play_trailers', False)
        self.skip_movies_with_existing_trailers = \
            self.config['EXTRA_CONFIG'].getboolean('skip_movies_with_existing_trailers', False)

        self.skip_movies_with_existing_theme = \
            self.config['EXTRA_CONFIG'].getboolean('skip_movies_with_existing_theme', False)
        return

    def get_searches(self):

        ret = dict()

        for option, value in self.config['SEARCHES'].items():

            try:
                index = int(option.split('_')[-1])
            except ValueError:
                continue

            if index not in ret:
                ret[index] = dict()
            ret[index]['_'.join(option.split('_')[:-1])] = value

        return ret

    def get_custom_filters(self):

        ret = dict()

        for option, value in self.config['CUSTOM_FILTERS'].items():

            if option == 'break_limit':
                self.break_limit = int(value)
                continue
            if option == 'last_resort_policy':
                self.last_resort_policy = value
                continue

            try:
                index = int(option.split('_')[0])
            except ValueError:
                continue

            if index not in ret:
                ret[index] = list()
            try:
                ret[index].append('_'.join(option.split('_')[1:]) + ':::' + value)
            except ValueError:
                continue

        sorted_ret = list()
        for key in sorted(ret.keys()):
            sorted_ret.append(ret[key])

        return sorted_ret
