import datetime
from functools import wraps
from pprint import pprint

import requests
from config import user_token


a = ['photo291122813_457243847', 'photo291122813_456239709', 'photo291122813_456242692']
print(a[-1::-1][:2])













a = 'asdfasdfasdf'
b = 'qwerqwerqwerqwer'

def time_check(old_function):
    @wraps(old_function)
    def new_function(*args, **kwargs):
        start = datetime.datetime.now()
        result = old_function(*args, **kwargs)
        end = datetime.datetime.now()
        work_time = end - start
        print(f"Время работы функции {old_function.__name__} {work_time}")

        return result

    # new_function.__name__ = old_function.__name__
    return new_function
