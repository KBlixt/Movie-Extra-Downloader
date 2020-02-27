from _socket import timeout
from urllib.error import URLError

from pytube import YouTube
from pytube.exceptions import RegexMatchError
from old_code.Stream import Stream
import time
import string_tools as tools


class YoutubeVideo(object):

    # todo (2): subtitles
    conn_errors = 0

    def __init__(self, url, score=0, preferred_container='mp4', min_resolution=360,
                 max_resolution=1080, force_preferred_container=False):

        ########################################
        self.url = None
        self.source = None
        self.delete = None
        self.complete = None
        self.is_play_trailer = None

        self.title = None
        self.thumbnail_url = None
        self.channel = None
        self.tags = list()

        self.view_count = None
        self.rating = None
        self.adjusted_rating = None
        self.resolution = None
        self.quality_score = None
        self.length = None
        self.resolution_ratio = None

        self.streams = list()
        self.best_video_stream = None
        self.best_audio_stream = None
        self.best_combined_stream = None
        ########################################

        self.url = url
        self.delete = False
        self.is_play_trailer = False
        self.complete = True

        tries = 0
        while True:
            try:
                self.source = YouTube(url)
            except KeyError as e:
                if e.args[0] == 'url':
                    self.delete = True
                    self.is_play_trailer = True
                    # todo (1): add youtube-dl info grabber/downloader
                    # stuff I need: title, length, keywords?
                    return
                elif e.args[0] == 'url_encoded_fmt_stream_map':
                    if tries > 4:
                        print('Failed to load youtube data, retrying. Reason: ' + str(e))
                        self.delete = True
                        return

                    print('Failed to load youtube data, retrying. Reason: ' + str(e))
                    time.sleep(2)
                    tries += 1

                else:
                    raise
            except RegexMatchError as e:
                print('Pytube failed to load video info. Reason: ' + url + ': ' + str(e))
                self.delete = True
                return
            except timeout as e:
                if tries > 4:
                    print('Pytube failed to load video info. Reason: ' + str(e))
                    self.complete = False
                    if Stream.conn_errors > 2:
                        raise
                    else:
                        Stream.conn_errors += 1
                    return

                print('Pytube failed to load video info. Reason: ' + str(e) + ', retrying...')
                tries += 1
                time.sleep(1)
            except URLError as e:
                if tries > 2:
                    print('Pytube failed to load video info. Reason: ' + str(e))
                    self.complete = False
                    if YoutubeVideo.conn_errors > 2:
                        raise
                    else:
                        YoutubeVideo.conn_errors += 1
                    return

                print('Pytube failed to load video info. Reason: ' + str(e) + ', retrying...')
                time.sleep(1)
                tries += 1
            else:
                YoutubeVideo.conn_errors = 0
                break

        self.score = score

        self.title = self.source.title
        self.title = tools.get_clean_string(self.title)
        self.rating = float(self.source.player_config_args['avg_rating'])
        self.view_count = int(self.source.player_config_args['view_count'])
        self.channel = self.source.player_config_args['author']
        self.length = self.source.player_config_args['length_seconds']

        self.thumbnail_url = self.source.thumbnail_url
        try:
            self.thumbnail_url = self.source.thumbnail_url
        except KeyError:
            self.thumbnail_url = None

        try:
            self.tags = self.source.player_config_args['keywords'].split(',')
        except KeyError:
            self.tags = ''

        if self.view_count < 100:
            self.view_count = 100

        self.adjusted_rating = self.rating * (1 - 1 / ((self.view_count / 60) ** 0.5))

        self.load_streams(min_resolution, max_resolution)
        self.update_quality_score(preferred_container)
        self.update_best_audio_stream(preferred_container, force_preferred_container)
        self.update_best_video_stream(preferred_container, force_preferred_container)
        self.update_best_combined_stream(preferred_container, force_preferred_container)

        if self.is_play_trailer:
            self.update_youtube_dl_info()



    def update_youtube_dl_info(self):
        pass

    def update_quality_score(self, preferred_container='mp4'):
        self.quality_score = 0
        max_res = 0

        for stream in self.streams:

            if stream.type != 'video':
                continue

            quality_score = 0
            pixel_bitrate = stream.bitrate_per_pixel

            if stream.resolution == 1080:
                pixel_bitrate /= 1
                quality_score = 120
            elif stream.resolution == 720:
                pixel_bitrate /= 1.22
                quality_score = 108
            elif stream.resolution == 480:
                pixel_bitrate /= 1.52
                quality_score = 65
            elif stream.resolution == 360:
                pixel_bitrate /= 1.39
                quality_score = 40
            elif stream.resolution == 240:
                pixel_bitrate /= 2.15
                quality_score = 20
            elif stream.resolution == 144:
                pixel_bitrate /= 2.65
                quality_score = 10

            if preferred_container.lower() == stream.container:
                quality_score *= 1.2
            quality_score *= pixel_bitrate

            if stream.resolution > max_res:
                self.quality_score = quality_score
                max_res = stream.resolution
                self.resolution_ratio = stream.size[0] / stream.size[1]
            elif stream.resolution == max_res:
                if quality_score > self.quality_score:
                    self.quality_score = quality_score

    def load_streams(self, min_resolution=360, max_resolution=1080):

        self.streams = list()
        self.complete = True

        for source_stream in self.source.streams.fmt_streams:
            stream = Stream(source_stream, int(self.length))
            if stream.complete:
                if stream.resolution is not None:
                    if stream.resolution > max_resolution or stream.resolution < min_resolution:
                        continue
                self.streams.append(stream)
            elif stream.retry:
                self.complete = False
        if Stream.conn_errors != 0:
            self.complete = False

    def update_best_video_stream(self, preferred_container='mp4', force_preferred_container=False):

        highest_resolution = 0
        best_stream = None
        highest_pref_resolution = 0
        best_pref_stream = None

        for stream in self.streams:
            if 'video' != stream.type:
                continue

            if stream.resolution > highest_resolution:
                highest_resolution = stream.resolution
                best_stream = stream

            if stream.container.lower() == preferred_container.lower():
                if stream.resolution > highest_pref_resolution:
                    highest_pref_resolution = stream.resolution
                    best_pref_stream = stream

        if highest_resolution == highest_pref_resolution or force_preferred_container:
            ret = best_pref_stream
        else:
            ret = best_stream

        self.best_video_stream = ret

    def update_best_audio_stream(self, preferred_container='mp4', force_preferred_container=False):

        highest_bitrate = 0
        best_stream = None
        highest_pref_bitrate = 0
        best_pref_stream = None

        for stream in self.streams:
            if 'audio' != stream.type:
                continue

            if stream.bitrate > highest_bitrate:
                highest_bitrate = stream.bitrate
                best_stream = stream

            if stream.container.lower() == preferred_container.lower():
                if stream.bitrate > highest_pref_bitrate:
                    highest_pref_bitrate = stream.bitrate
                    best_pref_stream = stream

        if highest_bitrate <= highest_pref_bitrate * 1.35 or force_preferred_container:
            ret = best_pref_stream
        else:
            ret = best_stream
        self.best_audio_stream = ret

    def update_best_combined_stream(self, preferred_container='mp4', force_preferred_container=False):

        highest_resolution = 0

        for stream in self.streams:
            if 'combined' != stream.type:
                continue

            if stream.resolution > highest_resolution:
                highest_resolution = stream.resolution

        max_score = 0
        selected_stream = None

        for stream in self.streams:
            if 'combined' != stream.type:
                continue

            score = 0
            resolution = stream.resolution

            if force_preferred_container:
                if stream.container != preferred_container:
                    continue
            if resolution == highest_resolution:
                score += 10 ** 1
            if stream.container == preferred_container:
                score += 10 ** 0

            if score > max_score:
                max_score = score
                selected_stream = stream

        self.best_combined_stream = selected_stream
