import hashlib
import os


def hash_file(file_path):
    if not os.path.isdir(file_path):
        md5 = hashlib.md5()
        with open(file_path, 'rb') as file:
            for i in range(10):
                data = file.read(2**20)
                if not data:
                    break
                md5.update(data)
        return md5.hexdigest()


def get_keyword_list(string):

    ret = ' ' + get_clean_string(string).lower() + ' '
    ret = (ret.replace(' the ', ' ')
              .replace(' in ', ' ')
              .replace(' a ', ' ')
              .replace(' by ', ' ')
              .replace(' for ', ' ')
              .replace(' is ', ' ')
              .replace(' am ', ' ')
              .replace(' an ', ' ')
              .replace(' in ', ' ')
              .replace(' with ', ' ')
              .replace(' from ', ' ')
              .replace(' and ', ' ')
              .replace(' movie ', ' ')
              .replace(' trailer ', ' ')
              .replace(' interview ', ' ')
              .replace(' interviews ', ' ')
              .replace(' scenes ', ' ')
              .replace(' scene ', ' ')
              .replace(' official ', ' ')
              .replace(' hd ', ' ')
              .replace(' hq ', ' ')
              .replace(' lq ', ' ')
              .replace(' 1080p ', ' ')
              .replace(' 720p ', ' ')
              .replace(' of ', ' '))

    return list(set(ret.strip().split(' ')))


def get_clean_string(string):
    ret = ' ' + string.lower() + ' '

    ret = (ret.replace('(', '')
              .replace(')', '')
              .replace('[', '')
              .replace(']', '')
              .replace('{', '')
              .replace('}', '')
              .replace(':', '')
              .replace(';', '')
              .replace('?', '')
              .replace("'", '')
              .replace("’", '')
              .replace("´", '')
              .replace("`", '')
              .replace("*", ' ')
              .replace('.', ' ')
              .replace('·', '-')
              .replace(' -', ' ')
              .replace('- ', ' ')
              .replace('_', ' ')
              .replace(' + ', ' : ')
              .replace('+', '/')
              .replace(' : ', ' + ')
              .replace('/ ', ' ')
              .replace(' /', ' ')
              .replace(' & ', ' '))

    ret_tup = ret.split(' ')
    ret_count = 0
    for ret_tup_count in range(len(ret_tup)-1):
        if len(ret_tup[ret_tup_count]) == 1 and len(ret_tup[ret_tup_count + 1]) == 1:
            ret_count += 1
            ret = ret[:ret_count] + ret[ret_count:ret_count + 1].replace(' ', '.') + ret[ret_count + 1:]
            ret_count += 1
        else:
            ret_count += len(ret_tup[ret_tup_count]) + 1

    return replace_roman_numbers(ret).strip()


def replace_roman_numbers(string):
    ret = ' ' + string.lower() + ' '

    ret = (ret.replace(' ix ', ' 9 ')
           .replace(' viiii ', ' 9 ')
           .replace(' viii ', ' 8 ')
           .replace(' vii ', ' 7 ')
           .replace(' vi ', ' 6 ')
           .replace(' iv ', ' 4 ')
           .replace(' iiii ', ' 4 ')
           .replace(' iii ', ' 3 ')
           .replace(' ii ', ' 2 ')
           .replace(' trailer 4 ', ' trailer ')
           .replace(' trailer 3 ', ' trailer ')
           .replace(' trailer 2 ', ' trailer ')
           .replace(' trailer 1 ', ' trailer '))

    return ret.strip()


def make_list_from_string(string, delimiter=',', remove_spaces_next_to_delimiter=True):
    if remove_spaces_next_to_delimiter:
        while ' ' + delimiter in string:
            string = string.replace(' ' + delimiter, delimiter)
        while delimiter + ' ' in string:
            string = string.replace(delimiter + ' ', delimiter)

    return string.split(delimiter)


def apply_query_template(template, keys):
    ret = template
    for key, value in keys.items():
        if isinstance(value, str):
            ret = ret.replace('{' + key + '}', value)
        elif isinstance(value, int):
            ret = ret.replace('{' + key + '}', str(value))
        elif isinstance(value, float):
            ret = ret.replace('{' + key + '}', str(value))

    return ret.strip()
