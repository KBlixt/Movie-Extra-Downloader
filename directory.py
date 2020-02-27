import os
import tools as tools
from datetime import date
import json


class Directory(object):

    def __init__(self, full_path, tmdb_api_key=None, tmdb_id=None, json_dict=None):

        ########################################
        self.name = None
        self.full_path = None
        self.content = dict
        self.subdirectories = dict()

        self.tmdb_id = None
        self.movie_title = None
        self.movie_original_title = None
        self.movie_original_title_keywords = None
        self.movie_release_year = None
        self.movie_title_keywords = list()
        self.movie_crew_data = list()

        self.banned_title_keywords = list()
        self.banned_years = list()

        self.record = list()
        self.completed_configs = list()
        ########################################

        if full_path is None:
            for key, value in json_dict.items():
                setattr(self, key, value)
        else:
            self.update_all(full_path=full_path, tmdb_api_key=tmdb_api_key, tmdb_id=tmdb_id)

    @classmethod
    def load_directory(cls, file):
        with open(file, 'r') as load_file:
            return Directory(None, json_dict=json.load(load_file))

    def update_all(self, full_path=None, tmdb_api_key=None, tmdb_id=None):
        if full_path is not None:
            self.name = os.path.split(full_path)[1]
            self.full_path = full_path
        self.update_content()
        self.update_movie_info(tmdb_api_key=tmdb_api_key, tmdb_id=tmdb_id)
        if tmdb_api_key is not None:
            self.update_similar_results(tmdb_api_key)

    def update_content(self):

        self.content = dict()
        self.subdirectories = dict()

        for file in os.listdir(self.full_path):
            if os.path.isdir(os.path.join(self.full_path, file)):
                sub_content = dict()
                for sub_file in os.listdir(os.path.join(self.full_path, file)):
                    sub_content[sub_file] = tools.hash_file(os.path.join(self.full_path, file, sub_file))
                self.subdirectories[file] = sub_content
            else:
                self.content[file] = tools.hash_file(os.path.join(self.full_path, file))

    def update_movie_info(self, tmdb_api_key=None, tmdb_id=None):
        def get_info_from_directory():
            clean_name_tuple = tools.get_clean_string(self.name).split(' ')

            if any(clean_name_tuple[-1] == str(year) for year in range(1896, date.today().year + 2)):
                self.movie_release_year = int(clean_name_tuple[-1])
                self.movie_title = ' '.join(clean_name_tuple[:-1])
                self.movie_original_title = ' '.join(clean_name_tuple[:-1])

            else:
                self.movie_release_year = None
                self.movie_title = ' '.join(clean_name_tuple)
                self.movie_original_title = ' '.join(clean_name_tuple)

            self.movie_title_keywords = tools.get_keyword_list(self.movie_title)
            self.movie_original_title_keywords = tools.get_keyword_list(self.movie_original_title)

            return True

        def get_info_from_details():
            details_data = tools.get_tmdb_details_data(tmdb_api_key, tmdb_id)
            if details_data is not None:
                self.tmdb_id = details_data['id']
                self.movie_title = details_data['title']
                self.movie_original_title = details_data['original_title']
                self.movie_title_keywords = tools.get_keyword_list(details_data['title'])
                self.movie_original_title_keywords = tools.get_keyword_list(details_data['original_title'])

                if len(details_data['release_date'][:4]) == 4:
                    self.movie_release_year = int(details_data['release_date'][:4])
                else:
                    self.movie_release_year = None
                return True
            else:
                return False

        def get_info_from_search():
            search_data = tools.get_tmdb_search_data(tmdb_api_key, self.movie_title)

            if search_data is None or search_data['total_results'] == 0:
                return False

            movie_data = None
            movie_backup_data = None

            if self.movie_release_year is None:
                movie_data = search_data['results'][0]
            else:

                for result in search_data['results'][:5]:
                    if movie_data is None:
                        if str(self.movie_release_year) == result['release_date'][:4]:
                            movie_data = result
                        elif result['release_date'][6:8] in ['09', '10', '11', '12'] \
                                and str(self.movie_release_year - 1) == result['release_date'][:4]:
                            movie_data = result
                        elif result['release_date'][6:8] in ['01', '02', '03', '04'] \
                                and str(self.movie_release_year + 1) == result['release_date'][:4]:
                            movie_data = result
                    elif movie_backup_data is None:
                        if str(self.movie_release_year - 1) == result['release_date'][:4]:
                            movie_backup_data = result

                        elif str(self.movie_release_year + 1) == result['release_date'][:4]:
                            movie_backup_data = result

                if movie_data is None and movie_backup_data is not None:
                    print('None of the search results had a correct release year, picking the next best result')
                    movie_data = movie_backup_data

                if movie_data is None:
                    movie_data = search_data['results'][0]

            self.tmdb_id = movie_data['id']
            self.movie_title = tools.get_clean_string(movie_data['title'])
            self.movie_original_title = tools.get_clean_string(movie_data['original_title'])
            self.movie_title_keywords = tools.get_keyword_list(movie_data['title'])
            self.movie_original_title_keywords = tools.get_keyword_list(movie_data['original_title'])

            if len(movie_data['release_date'][:4]) == 4:
                self.movie_release_year = int(movie_data['release_date'][:4])
            else:
                self.movie_release_year = None
            return True

        if tmdb_api_key is not None:
            if tmdb_id is not None:
                if get_info_from_details():
                    return True
                else:
                    tmdb_id = None
            if get_info_from_directory():
                if get_info_from_search():
                    return True
            else:
                return False

        return get_info_from_directory()

    def update_similar_results(self, tmdb_api_key):

        def find_similar_results():

            def find_by_tmdb_id():
                similar_movies_data = list()
                movie_found = False

                for result in search_data['results']:

                    if self.tmdb_id == result['id']:
                        movie_found = True
                    else:
                        similar_movies_data.append(result)

                if movie_found:
                    return similar_movies_data
                else:
                    return None

            def find_by_release_year():
                similar_movies_data = list()
                movie_found = False
                backup_found = False

                for result in search_data['results']:

                    if not movie_found and str(self.movie_release_year) == result['release_date'][:4]:
                        movie_found = True
                        continue

                    elif not backup_found:

                        if result['release_date'][6:8] in ['09', '10', '11', '12'] \
                                and str(self.movie_release_year - 1) == result['release_date'][:4]:
                            backup_found = True

                        elif result['release_date'][6:8] in ['01', '02', '03'] \
                                and str(self.movie_release_year + 1 == result['release_date'][:4]):
                            backup_found = True

                    if len(similar_movies_data) < 5:
                        similar_movies_data.append(result)

                if movie_found or backup_found:
                    return similar_movies_data
                else:
                    return None

            search_data = tools.get_tmdb_search_data(tmdb_api_key, self.movie_title)

            if search_data is None or search_data['total_results'] == 0:
                return list()

            ret = find_by_tmdb_id()
            if ret is not None:
                return ret[:5]

            if self.movie_release_year is None:
                return search_data['results'][1:6]

            ret = find_by_release_year()
            if ret is not None:
                return ret[:5]

            return None

        def process_similar_results():
            self.banned_title_keywords = list()
            self.banned_years = list()

            for similar_movie in similar_movies:

                for word in tools.get_keyword_list(similar_movie['title']):

                    if (word.lower() not in self.movie_title.lower()
                            and word.lower() not in self.banned_title_keywords):

                        if self.movie_original_title is not None:

                            if word.lower() not in self.movie_original_title.lower():
                                self.banned_title_keywords.append(word)

                        else:
                            self.banned_title_keywords.append(word)

                if len(similar_movie['release_date'][:4]) == 4 \
                        and int(similar_movie['release_date'][:4]) not in ([self.movie_release_year] +
                                                                           self.banned_years):
                    self.banned_years.append(int(similar_movie['release_date'][:4]))

        similar_movies = find_similar_results()
        if similar_movies is not None:
            process_similar_results()
            return True
        else:
            return False

    def save_directory(self, save_path):
        self.content = None
        self.subdirectories = None
        if not os.path.isdir(save_path):
            os.mkdir(os.path.join(save_path))
        with open(os.path.join(save_path, self.name), 'w') as save_file:
            json.dump(self.__dict__, save_file)
