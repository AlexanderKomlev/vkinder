
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from bd.vkinder_bd_main import write_users, write_black_list, check_black, check_favorite, check_user_bot, show_favorites, get_offset, write_parametr_offset, write_favorite, change_offset
from config import app_token, bot_token
import requests

from datetime import datetime as dt
import time

class VKinderBot:
    base_url = "https://api.vk.com/method/"

    def __init__(self, app_token):
        self.base_url = "https://api.vk.com/method"
        self.vk_group_session = vk_api.VkApi(token=bot_token)
        self.longpoll = VkLongPoll(self.vk_group_session)
        self.session = vk_api.VkApi(token=app_token)
        self.common_params = {'access_token': bot_token, 'v': 5.131}
        self.offset = 0

    def _get_photos_list(self, user_id: int) -> list:
        params = self.common_params
        params.update({
            'access_token': app_token,
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
        photo_id_list = []
        for item in photos_list[:3]:
            photo_id_list.append(f'photo{item.get("owner_id")}_{item.get("id")}')
        return ",".join(photo_id_list)
    def _user_data(self, user_id) -> dict:

        params = self.common_params
        params.update({
            'user_ids': user_id,
            'fields': 'city,sex'
        })
        response = requests.get(f'{self.base_url}/users.get', params=params)
        response = response.json().get('response', {})[0]
        user = {
            'user_id': response.get('id'),
            'fullname': response.get('first_name') + ' ' + response.get('last_name'),
            'gender': response.get('sex'),
            'age': None,
            'city': None
        }
        try:
            age = (dt.date(dt.today()) - dt.date(dt.strptime(response.get('bdate'), '%d.%m.%Y'))).days / 365
        except TypeError:
            age = None
        try:
            city = response.get('city').get('title')
        except AttributeError:
            city = None
        user.update({"age": age, "city": city})
        return user

    def _search(self, params: dict, offset: int) -> list:
        method = "users.search"
        age = params.get("age")
        params = {
            "count": 20,
            "offset": offset,
            "hometown": params.get("city"),
            "sex": 1 if params.get("gender") == 2 else 2,
            "age_from": age - 3 if age else "",
            "age_to": age + 3 if age else "",
            "fields": "status"
        }
        response = self.session.method(method, values=params)
        return list(filter(lambda x: x.get("is_closed", "") == False, response.get("items", "")))

    def get_name(self, user_id):
        method = "users.get"
        params = {
                'user_ids': user_id
            }
        result = self.session.method(method, params)[0]
        return result.get("first_name")

    def filter_search(self, params: dict, offset: int) -> list:
        list_to_iter = []
        people = self._search(params, offset)
        for user in people:
            dictionary = {"fullname": f"{user.get('first_name')} {user.get('last_name')}",
                          "user_id": user.get('id'),
                          "link": f"https://vk.com/id{user.get('id')}",
                          "photos": self._get_needed_photos(user.get('id', ''))}
            list_to_iter.append(dictionary)
        return list_to_iter
    def _send_message(self, id: int, message: str, keyboard=None, attachment=None):

        self.vk_group_session.method('messages.send', {'user_id': id,
                                                       'message': message,
                                                       'random_id': get_random_id(),
                                                       'keyboard': keyboard,
                                                       'attachment': attachment})
    def send_start_keyboard(self):
        keyboard = VkKeyboard(inline=False, one_time=True)
        keyboard.add_button("начать", color=VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()
    def send_full_keyboard(self, favorite_flag):
        if favorite_flag:
            keyboard = VkKeyboard(inline=True)
            keyboard.add_button("назад", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("вперед", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("в избранное", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("в черный список", color=VkKeyboardColor.SECONDARY)
            keyboard.add_button("завершить", color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button("просмотреть избранное", color=VkKeyboardColor.POSITIVE)
        else:
            keyboard = VkKeyboard(inline=True)
            keyboard.add_button("назад", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("вперед", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("в избранное", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("в черный список", color=VkKeyboardColor.SECONDARY)
            keyboard.add_button("завершить", color=VkKeyboardColor.SECONDARY)

        return keyboard.get_keyboard()

    def send_continue_complete_keyboard(self):
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button("продолжить", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("завершить", color=VkKeyboardColor.SECONDARY)
        return keyboard.get_keyboard()

    def run_bot(self):
        favorite_flag = False
        for event in self.longpoll.listen():

            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:

                if event.text.lower() == 'start':
                    params_of_user = self._user_data(event.user_id)
                    if not check_user_bot(event.user_id):
                        write_users(**params_of_user)
                    current_iter = BotIter(params_of_user, get_offset(event.user_id))
                    self._send_message(event.user_id,
                                       message=f'Привет, {self.get_name(event.user_id)}! Мы подобрали для тебя пары. Жми начать 👇',
                                       keyboard=self.send_start_keyboard())

                if event.text.lower() == 'начать':
                    person = next(current_iter)
                    self._send_message(event.user_id,
                                       message=f"{person.get('fullname')}\n{person.get('link')}",
                                       attachment=person.get("photos"),
                                       keyboard=self.send_full_keyboard(favorite_flag))

                if event.text.lower() in ["вперед", "продолжить", "в избранное", "в черный список"]:

                    if event.text.lower() == "в черный список":
                        if not check_black(person.get("user_id")):
                            data_for_table = {
                                "fullname": person.get("fullname"),
                                "black_id": person.get("user_id"),
                                "link": person.get("link"),
                                "photos": person.get("photos"),
                                "user_id": event.user_id
                            }
                            write_black_list(**data_for_table)
                        self._send_message(event.user_id,
                                           message=f"Добавлено в черный список {person.get('fullname')}")
                        time.sleep(2)

                    if event.text.lower() == "в избранное":
                        if not check_favorite(person.get("user_id")):
                            favorite_flag = True
                            data_for_table = {
                                "fullname": person.get("fullname"),
                                "favorite_id": person.get("user_id"),
                                "link": person.get("link"),
                                "photos": person.get("photos"),
                                "user_id": event.user_id
                            }
                            write_favorite(**data_for_table)
                        self._send_message(event.user_id,
                                           message=f"Добавлено в избранное {person.get('fullname')}")
                        time.sleep(2)

                    person = next(current_iter)
                    self._send_message(event.user_id,
                                       message=f"{person.get('fullname')}\n{person.get('link')}",
                                       attachment=person.get("photos"), keyboard=self.send_full_keyboard(favorite_flag))


                if  event.text.lower() == 'назад':
                    person = current_iter.prev()
                    self._send_message(event.user_id,
                                       message=f"{person.get('fullname')}\n{person.get('link')}",
                                       attachment=person.get("photos"), keyboard=self.send_full_keyboard(favorite_flag))


                if event.text.lower() == "просмотреть избранное":
                    self._send_message(event.user_id,
                                       message=f"Вы находитесь в избранном")
                    for user in show_favorites(event.user_id):
                        self._send_message(event.user_id,
                                           message=f"{user[0]}\n{user[1]}",
                                           attachment=user[2])
                    self._send_message(event.user_id,
                                       message="нажмите, чтобы продолжить поиск или завершить",
                                       keyboard=self.send_continue_complete_keyboard())


                if event.text.lower() == "завершить":
                    self._send_message(event.user_id,
                                       message=f"До новых встреч!")
                    self.offset = current_iter.inner_cursor + current_iter.offset
                    if get_offset(event.user_id):
                        change_offset(event.user_id, self.offset)
                    else:
                        data_for_table = {
                            "offset": self.offset,
                            "user_id": event.user_id
                        }
                        write_parametr_offset(**data_for_table)
                    break

class BotIter:

    def __init__(self, params_of_user, offset):
        self.params = params_of_user
        self.bot = VKinderBot(app_token)
        self.offset = offset
        self.users = self.bot.filter_search(self.params, self.offset)
        self.stop_offset = 1000
        self.inner_cursor = -1

    def __iter__(self):
        return self

    def __next__(self):
        self.inner_cursor += 1
        if self.inner_cursor >= len(self.users):
            self.inner_cursor = 0
            self.offset += len(self.users)
            self.users = self.bot.filter_search(self.params, self.offset)
        if self.offset >= self.stop_offset:
            raise StopIteration
        return self.users[self.inner_cursor]

    def prev(self):
        self.inner_cursor -= 1
        if self.inner_cursor < 0:
            return "Предыдущих элементов нет"
        return self.users[self.inner_cursor]