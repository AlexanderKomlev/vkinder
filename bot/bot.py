
from vk_api.longpoll import VkLongPoll, VkEventType
from config import main_token, user_token, user_vk_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import datetime as dt
from bd.vkinder_bd_models import Users
from pprint import pprint


import requests
import vk_api
import sqlalchemy


class VKinderBot:

    def __init__(self, city, gender, age, session):

        self.session = session
        self.vk_session = vk_api.VkApi(token=main_token)
        self.longpoll = VkLongPoll(self.vk_session)
        self.session = vk_api.VkApi(token=user_token)  # использовала в _search
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

    def _user_data(self, user_id: int) -> dict:

        params = self.common_params
        params.update({
            'user_ids': user_id,
            'fields': 'city, bdate, sex'
        })
        response = requests.get(f'{self.base_url}/users.get', params=params)
        response = response.json().get('response', {})[0]
        age = (dt.date(dt.today()) - dt.date(dt.strptime(response.get('bdate'), '%d.%m.%Y'))).days / 365
        user = {
            'user_id': response.get('id'),
            'fullname': response.get('first_name') + ' ' + response.get('last_name'),
            'age': int(age),
            'gender': response.get('sex'),
            'city': response.get('city').get('title'),
        }

        return user

    def _search(self, offset=0) -> list:
        method = "users.search"
        params = {
            "offset": offset,
            "hometown": self.city,
            "sex": self.gender,
            "age_from": self.age - 3,
            "age_to": self.age + 3,
            "count": 1
        }
        response = self.session.method(method, values=params)
        return list(filter(lambda x: x.get("is_closed", "") is False, response.get("items", "")))

    def find_count(self) -> int:
        return len(self._search())

    def filter_search(self, offset=0) -> list:
        list_to_bot = []
        for user in self._search(offset=0):
            dictionary = {"fullname": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                          "link": f"https://vk.com/id{user.get('id', '')}",
                          "photos": self._get_needed_photos(user.get("id", ""))}
            list_to_bot.append(dictionary)
        return list_to_bot

    def run_bot(self, session):

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                if event.text.lower() == 'start':
                    user = self._user_data(event.user_id)
                    session.add(Users(**user))
                    session.commit()
                    next_person = BotIter(self.filter_search)



                    keyboard = VkKeyboard(inline=True)
                    keyboard.add_button('В черный список', color=VkKeyboardColor.NEGATIVE)
                    keyboard.add_button('В избранное', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_line()
                    keyboard.add_button('Назад', color=VkKeyboardColor.SECONDARY)
                    keyboard.add_button('Пропустить', color=VkKeyboardColor.PRIMARY)
                    keyboard.add_line()
                    keyboard.add_button('Показать избранное', color=VkKeyboardColor.POSITIVE)

                    self._send_message(event.chat_id, 'Выберите действие:', keyboard.get_keyboard())

                    # if event.text == '[club223509501|@club223509501] Пропустить' and event.user_id == id:








# забирает каждые 20 людей, сдвигая offset
# двунаправленный итератор
class BotIter:

    def __init__(self, search_func):
        self.search_func = search_func
        self.users = search_func()
        self.inner_cursor = -1
        self.offset = 0
        self.stop_offset = 1000

    def __iter__(self):
        return self

    def __next__(self):
        self.inner_cursor += 1
        if self.inner_cursor >= len(self.users):
            self.inner_cursor = 0
            self.offset += 20
            self.users = self.search_func(self.offset)
        if self.offset >= self.stop_offset:
            raise StopIteration
        return self.users[self.inner_cursor]

    def prev(self):
        self.inner_cursor -= 1
        if self.inner_cursor < 0:
            return "Предыдущих элементов нет"
        return self.users[self.inner_cursor]


# user_1 = VKinderBot("Орел", 1, 25)
# users = user_1.filter_search()
#
# for j, element in enumerate(BotIter(users)):
#     print(j, element)


user_1 = VKinderBot("Орел", 1, 30)
users_search = BotIter(user_1.filter_search())

while True:
    answer = input()
    if answer == "вперед":
        print(next(users_search))
    elif answer == "назад":
        print(users_search.prev())
    else:
        break





