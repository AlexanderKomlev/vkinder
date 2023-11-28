from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from config import app_token, bot_token
from datetime import datetime as dt
from bd.vkinder_bd_main import (write_users, write_black_list, check_black, check_favorite, check_user_bot,
                                show_favorites, get_offset, write_parametr_offset, write_favorite, change_offset)


import vk_api
import requests
import logging


logging.basicConfig(level=logging.DEBUG,
                    filename='logfile.log',
                    encoding='utf-8',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


class VKinderBot:

    def __init__(self):

        self.base_url = "https://api.vk.com/method"
        self.vk_group_session = vk_api.VkApi(token=bot_token)
        self.longpoll = VkLongPoll(self.vk_group_session)
        self.session = vk_api.VkApi(token=app_token)
        self.common_params = {'access_token': bot_token, 'v': 5.131}
        self.offset = 0
        logging.info('Инициализация класса VKinderBot')

    def _get_photos_list(self, user_id: int) -> list:

        params = self.common_params
        params.update({
            'access_token': app_token,
            'owner_id': user_id,
            'album_id': 'profile',
            'extended': 1
        })
        response = requests.get(f'{self.base_url}/photos.get', params=params)
        logging.info('Завершен запрос на получение фотографий')

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
        logging.info('Поиск профилей завершен успешно')

        return list(filter(lambda x: x.get("is_closed", "") is False, response.get("items", "")))

    def _get_name(self, user_id):

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
        logging.info(f'Пользователю отправлено сообщение: {message}')

    def _send_start_keyboard(self):

        keyboard = VkKeyboard(inline=False, one_time=True)
        keyboard.add_button("начать", color=VkKeyboardColor.PRIMARY)

        return keyboard.get_keyboard()

    def _send_full_keyboard(self, favorite_flag):

        if favorite_flag:
            keyboard = VkKeyboard(inline=False)
            keyboard.add_button("назад", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("вперед", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("в избранное", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("в черный список", color=VkKeyboardColor.SECONDARY)
            keyboard.add_button("завершить", color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button("просмотреть избранное", color=VkKeyboardColor.POSITIVE)
        else:
            keyboard = VkKeyboard(inline=False)
            keyboard.add_button("назад", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("вперед", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("в избранное", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("в черный список", color=VkKeyboardColor.SECONDARY)
            keyboard.add_button("завершить", color=VkKeyboardColor.SECONDARY)

        return keyboard.get_keyboard()

    def _send_continue_complete_keyboard(self):

        keyboard = VkKeyboard(inline=False)
        keyboard.add_button("продолжить", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("завершить", color=VkKeyboardColor.SECONDARY)

        return keyboard.get_keyboard()

    def run_bot(self):

        logging.debug('Запуск бота')

        favorite_flag = False
        welcome_flag = True
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                if event.text.lower():

                    if welcome_flag:
                        params_of_user = self._user_data(event.user_id)
                        if not check_user_bot(event.user_id):
                            write_users(**params_of_user)
                            logging.info('Данные пользователя внесены в базу данных')
                        current_iter = BotIter(params_of_user, get_offset(event.user_id), self.filter_search)
                        self._send_message(event.user_id,
                                           message=f'Привет, {self._get_name(event.user_id)}! Мы подобрали для тебя пары. Жми начать 👇',
                                           keyboard=self._send_start_keyboard())
                        welcome_flag = False
                    else:
                        pass

                if event.text.lower() == 'начать':

                    logging.info('Пользователь перешел по ветке "начать"')
                    if welcome_flag is False:
                        person = next(current_iter)
                        self._send_message(event.user_id,
                                           message=f"{person.get('fullname')}\n{person.get('link')}",
                                           attachment=person.get("photos"),
                                           keyboard=self._send_full_keyboard(favorite_flag))

                if event.text.lower() in ["вперед", "продолжить", "в избранное", "в черный список"]:

                    if welcome_flag is False:
                        if event.text.lower() == "в черный список":

                            logging.info('Пользователь перешел по ветке "в черный список"')
                            if not check_black(person.get("user_id")):
                                data_for_table = {
                                    "fullname": person.get("fullname"),
                                    "black_id": person.get("user_id"),
                                    "link": person.get("link"),
                                    "photos": person.get("photos"),
                                    "user_id": event.user_id
                                }
                                write_black_list(**data_for_table)
                                logging.info('Информация о пользователе добавлена в БД в таблицу "black_list"')
                            self._send_message(event.user_id,
                                               message=f"Добавлено в черный список {person.get('fullname')}")

                        if event.text.lower() == "в избранное":

                            logging.info('Пользователь перешел по ветке "в избранное"')
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
                                logging.info('Информация о пользователе добавлена в БД в таблицу "favorite"')
                            self._send_message(event.user_id,
                                               message=f"Добавлено в избранное {person.get('fullname')}")

                        person = next(current_iter)
                        self._send_message(event.user_id,
                                           message=f"{person.get('fullname')}\n{person.get('link')}",
                                           attachment=person.get("photos"),
                                           keyboard=self._send_full_keyboard(favorite_flag))

                if event.text.lower() == 'назад':

                    logging.info('Пользователь перешел по ветке "назад"')
                    if welcome_flag is False:
                        person = current_iter.prev()
                        self._send_message(event.user_id,
                                           message=f"{person.get('fullname')}\n{person.get('link')}",
                                           attachment=person.get("photos"),
                                           keyboard=self._send_full_keyboard(favorite_flag))

                if event.text.lower() == "просмотреть избранное":

                    logging.info('Пользователь перешел по ветке "просмотреть избранное"')
                    if welcome_flag is False:
                        self._send_message(event.user_id,
                                           message=f"Вы находитесь в избранном")
                        for user in show_favorites(event.user_id):
                            self._send_message(event.user_id,
                                               message=f"{user[0]}\n{user[1]}",
                                               attachment=user[2])
                        logging.info('Выведена информация из таблицы "favorite"')
                        self._send_message(event.user_id,
                                           message="нажмите, чтобы продолжить поиск или завершить",
                                           keyboard=self._send_continue_complete_keyboard())

                if event.text.lower() == "завершить":

                    logging.info('Пользователь перешел по ветке "завершить"')
                    if welcome_flag is False:
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

    def __init__(self, params_of_user, offset, search_func):

        self.search_func = search_func
        self.params = params_of_user
        self.offset = offset
        self.users = self.search_func(self.params, self.offset)
        self.stop_offset = 1000
        self.inner_cursor = -1
        logging.info('Инициализация итератора')

    def __iter__(self):
        return self

    def __next__(self):

        self.inner_cursor += 1
        if self.inner_cursor >= len(self.users):
            self.inner_cursor = 0
            self.offset += len(self.users)
            self.users = self.search_func(self.params, self.offset)
        if self.offset >= self.stop_offset:
            raise StopIteration
        return self.users[self.inner_cursor]

    def prev(self):

        self.inner_cursor -= 1
        if self.inner_cursor < 0:
            return "Предыдущих элементов нет"
        return self.users[self.inner_cursor]
