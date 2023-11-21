from vk_api.longpoll import VkLongPoll, VkEventType
from config import main_token, user_token, user_vk_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from pprint import pprint

import requests
import vk_api


class VKinderBot:

    def __init__(self, city, gender, age):

        self.vk_session = vk_api.VkApi(token=main_token)
        self.longpoll = VkLongPoll(self.vk_session)
        self.session = vk_api.VkApi(token=user_token) # использовала в _search
        self.base_url = 'https://api.vk.com/method/'
        self.common_params = {'access_token': user_token, 'v': 5.131}
        self.city = city
        self.gender = 2 if gender == 1 else 1
        self.age = age

    def _get_photos_list(self, user_id: int) -> list:

        params = self.common_params
        params.update({
            'access_token': user_token,
            'v': 5.131,
            'owner_id': user_id,
            'album_id': 'profile',
            'extended': 1
        })
        response = requests.get(f'{self.base_url}/photos.get', params=params)

        return response.json().get('response', {}).get('items', [])

    def _get_needed_photos(self, user_id: int) -> list or str:

        photos_list = self._get_photos_list(user_id)
        if not photos_list:
            return "There's no profile photo"
        photos_list.sort(key=lambda dictionary: dictionary['likes']['count'], reverse=True)
        link_list = []
        for item in photos_list[:3]:
            link_list.append(item.get('sizes')[-1].get('url'))

        return link_list

    def _send_message(self, id: int, message: str, keyboard=None):

        self.vk_session.method('messages.send', {'chat_id': id,
                                                 'message': message,
                                                 'random_id': 0,
                                                 'keyboard': keyboard})

    # поиск по параметрам: город, возраст, пол
    def _search(self, offset=0) -> list:
        method = "users.search"
        params = {
            "offset": offset,
            "hometown": self.city,
            "sex": self.gender,
            "age_from": self.age - 3,
            "age_to": self.age + 3
        }
        response = self.session.method(method, values=params)
        return list(filter(lambda x: x.get("is_closed", "") == False, response.get("items", "")))

    # возвращает количество найденных людей
    def find_count(self) -> int:
        return len(self._search())

    # создает готовый список словарей с полным именем, ссылкой на страничку и списком ссылок на фото
    def filter_search(self, offset=0) -> list:
        list_to_bot = []
        for user in self._search(offset=0):
            dictionary = {"fullname": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                          "link": f"https://vk.com/id{user.get('id', '')}",
                          "photos": self._get_needed_photos(user.get('id', ''))}
            list_to_bot.append(dictionary)
        return list_to_bot

# забирает каждые 20 людей, сдвигая offset
class BotIter:

    def __init__(self, users):
        self.users = users
        self.inner_cursor = -1
        self.offset = 0
        self.stop_offset = 200

    def __iter__(self):
        return self

    def __next__(self):
        self.inner_cursor += 1
        if self.inner_cursor >= len(self.users):
            self.inner_cursor = 0
            self.offset += 20
            self.users = user_1.filter_search(self.offset)
        if self.offset >= self.stop_offset:
            raise StopIteration
        return self.users[self.inner_cursor]


user_1 = VKinderBot("Орел", 1, 25)
users = user_1.filter_search()

for j, element in enumerate(BotIter(users)):
    print(j, element)





