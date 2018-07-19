import time
from _socket import timeout
from urllib.error import HTTPError, URLError


class Stream(object):

    conn_errors = 0

    def __init__(self, source, length):
        ########################################
        self.complete = True
        self.retry = False

        self.source = None
        self.id = None
        self.type = None
        self.container = None
        self.bitrate = None

        self.video_codec = None
        self.bitrate_per_pixel = None
        self.resolution = None
        self.fps = None
        self.is_hdr = None
        self.size = None
        self.is_3d = None

        self.audio_codec = None
        ########################################

        tries = 0
        while True:

            try:
                self.source = source
                self.id = source.itag
                self.container = source.subtype
                self.fps = source.fps
                self.file_size = source.filesize
                self.bitrate = self.file_size * 8 / length

                if source.is_progressive:
                    self.get_audio_data(source)
                    self.get_video_data(source)
                    self.type = 'combined'

                elif source.includes_audio_track:
                    self.get_audio_data(source)
                    self.type = 'audio'

                elif source.includes_video_track:
                    self.get_video_data(source)
                    self.type = 'video'
                    self.size = int(source.size.split('x')[0]), int(source.size.split('x')[1])
                    self.bitrate_per_pixel = self.bitrate / (self.size[0] * self.size[1])
                else:
                    print('both include_audio_track and include_video_track was false')
                    raise AttributeError('failed to categorise stream')

            except KeyError as e:
                print('A stream attribute failed to load. KeyError: ' + str(e))
                self.complete = False
                return
            except AttributeError as e:
                print('A required stream attribute failed to load. AttributeError: ' + str(e))
                self.complete = False
                return
            except timeout as e:
                if tries > 4:
                    print('A stream failed to load because it got timed out: ' + str(e))
                    self.complete = False
                    self.retry = True
                    if Stream.conn_errors > 2:
                        raise
                    else:
                        Stream.conn_errors += 1
                        return

                print('A stream failed to load because it got timed out, retrying. Reason: ' + str(e))
                tries += 1
                time.sleep(1)
            except HTTPError as e:
                print('A stream attribute failed to load, skipping. Reason: ' + str(e))
                self.incomplete = True
                return
            except URLError as e:
                if tries > 2:
                    print('A stream failed to load. Reason: ' + str(e))
                    self.complete = False
                    self.retry = True
                    if Stream.conn_errors > 2:
                        raise
                    else:
                        Stream.conn_errors += 1
                        return

                print('A stream attribute failed to load, retrying. Reason: ' + str(e))
                time.sleep(1)
                tries += 1
            except ConnectionResetError as e:
                if tries > 4:
                    print('A stream failed to load. Reason: ' + str(e))
                    self.complete = False
                    if Stream.conn_errors > 4:
                        raise
                    else:
                        Stream.conn_errors += 1
                        return
                print('A stream attribute failed to load, retrying. Reason: ' + str(e))
                time.sleep(1)
                tries += 1
            else:
                Stream.conn_errors = 0
                break

    def get_video_data(self, source):
        self.video_codec = source.video_codec
        self.resolution = int(source.resolution.replace('p', ''))
        self.is_hdr = source.is_hdr
        self.is_3d = source.is_3d

    def get_audio_data(self, source):
        self.audio_codec = source.audio_codec
