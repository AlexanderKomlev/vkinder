from vk_api.longpoll import VkLongPoll, VkEventType
from config import bot_token, app_token, user_vk_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import datetime as dt
from bd.vkinder_bd_models import Users, Favorites, BlackList
from pprint import pprint



import requests
import vk_api
import sqlalchemy


class VKinderBot:

    def __init__(self, city, gender, age, session=None):

        self.session = session
        self.vk_group_session = vk_api.VkApi(token=bot_token)
        self.longpoll = VkLongPoll(self.vk_group_session)
        self.vk_app_session = vk_api.VkApi(token=app_token)  # использовала в _search
        self.base_url = 'https://api.vk.com/method/'
        self.common_params = {'access_token': app_token, 'v': 5.131}
        self.city = None
        self.gender = None
        self.age = None
        self.next_person = None
        self.buffer = None

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
        photo_id_list = []
        for item in photos_list[:3]:
            photo_id_list.append(f'photo{item.get("owner_id")}_{item.get("id")}')
        return photo_id_list

    def _send_message(self, id: int, message: str, keyboard=None, attachment=None):

        self.vk_group_session.method('messages.send', {'chat_id': id,
                                                       'message': message,
                                                       'random_id': 0,
                                                       'keyboard': keyboard,
                                                       'attachment': attachment})

    def _user_data(self, event) -> dict:

        params = self.common_params
        params.update({
            'user_ids': event.user_id,
            'fields': 'city, bdate, sex'
        })
        response = requests.get(f'{self.base_url}/users.get', params=params)
        response = response.json().get('response', {})[0]

        user = {
            'user_id': response.get('id'),
            'fullname': response.get('first_name') + ' ' + response.get('last_name'),
            'gender': response.get('sex')
        }
        try:
            age = (dt.date(dt.today()) - dt.date(dt.strptime(response.get('bdate'), '%d.%m.%Y'))).days / 365
            user.update({'age': int(age)})
        except KeyError:
            self._send_message(event.chat_id, 'Введите ваш возраст')
        finally:
            try:
                user.update({'city': response.get('city').get('title')})
            except KeyError:
                self._send_message(event.chat_id, 'Введите ваш город')
            finally:
                return user

    def _search(self, offset=0) -> list:
        method = "users.search"
        params = {
            "offset": offset,
            "hometown": self.city,
            "sex": 1 if self.gender == 2 else 2,
            "age_from": self.age - 3,
            "age_to": self.age + 3,
            "count": 20
        }
        response = self.vk_app_session.method(method, values=params)
        return list(filter(lambda x: x.get("is_closed", "") is False, response.get("items", "")))

    def find_count(self) -> int:
        return len(self._search())

    def filter_search(self, offset=0) -> list:
        list_to_bot = []
        for user in self._search(offset=0):
            dictionary = {"fullname": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                          "user_id": user.get('id', ''),
                          "photos": self._get_needed_photos(user.get('id', ''))}
            list_to_bot.append(dictionary)
        return list_to_bot

    def _get_full_keyboard(self):
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button('В_черный_список', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_button('В_избранное', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.SECONDARY)
        keyboard.add_button('Пропустить', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Показать_избранное', color=VkKeyboardColor.POSITIVE)

        return keyboard.get_keyboard()

    def _get_keyboard(self):
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button('Дальше', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Показать_избранное', color=VkKeyboardColor.POSITIVE)

        return keyboard.get_keyboard()

    def show_bd(self):
        for item in self.session.query(Users).all():
            print(type(item))
            print(item)

    def show_bd2(self):
        for item in self.session.query(Favorites).all():
            print(item)

    def run_bot(self):

        for event in self.longpoll.listen():
            user = {}
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                print(event.text)
                user_id = event.user_id

                if event.text.lower() == 'start':
                    print('ветка старт')

                    self.next_person = BotIter(self.filter_search)
                    user = self._user_data(event)
                    if 'age' not in user:
                        self._send_message(event.chat_id, 'Введите ваш возраст')
                        continue
                    if 'city' not in user:
                        self._send_message(event.chat_id, 'Введите ваш город')
                        continue
                    self.city = user.get('city')
                    self.gender = user.get('gender')
                    self.age = user.get('age')
                    self.session.add(Users(**user))
                    self.session.commit()
                    person = self.next_person.__next__()
                    self.buffer = person
                    photos = str(person.get('photos')).strip("'[]'").replace(' ', '').replace("'", "")
                    self._send_message(event.chat_id,
                                       message=f"{person.get('fullname')}\nhttps://vk.com/{person.get('link')}",
                                       attachment=photos, )
                    self._send_message(event.chat_id, 'Выберите действие:', self._get_full_keyboard())

                elif event.text.isdigit() and event.user_id == user_id:

                    age = int(event.text)
                    user.update({'age': age})
                    self._send_message(event.chat_id, 'Напишите: начать')

                elif ((event.text.split(' ')[-1] == 'Пропустить' or event.text.split(' ')[-1] == 'Дальше')
                      and event.user_id == user_id):
                    print('ветка далее')

                    person = self.next_person.__next__()
                    self.buffer = person
                    photos = str(person.get('photos')).strip("'[]'").replace(' ', '').replace("'", "")
                    self._send_message(event.chat_id,
                                       message=f"{person.get('fullname')}\nhttps://vk.com/{person.get('link')}",
                                       attachment=photos, )
                    self._send_message(event.chat_id, 'Выберите действие:', self._get_full_keyboard())

                elif event.text.split(' ')[-1] == 'В_избранное' and event.user_id == user_id:
                    print('ветка избранное')

                    self.session.add(Favorites(
                        fullname=self.buffer.get('fullname'),
                        favorite_user_id=self.buffer.get('user_id'),
                        user_id=user_id,
                        photos=self.buffer.get('photos'),
                    ))
                    self.session.commit()
                    self._send_message(event.chat_id, 'Добавлено в избранное')
                    self._send_message(event.chat_id, 'Выберите действие:', self._get_keyboard())

                elif event.text.split(' ')[-1] == 'В_черный_список' and event.user_id == user_id:
                    print('ветка черный список')

                    self.session.add(BlackList(
                        black_user_id=self.buffer.get('user_id'),
                        user_id=user_id,
                    ))
                    self.session.commit()
                    self._send_message(event.chat_id, 'Добавлено в черный список')
                    self._send_message(event.chat_id, 'Выберите действие:', self._get_keyboard())

                elif event.text.split(' ')[-1] == 'Показать_избранное' and event.user_id == user_id:
                    print('ветка показать избранное')

                    for item in self.session.query(Favorites).filter(Favorites.user_id == user_id).all():
                        photos = item.photos.strip("'{}'").replace(' ', '').replace("'", "")
                        print(photos)
                        self._send_message(event.chat_id,
                                           message=f"{item.fullname}\nhttps://vk.com/{item.favorite_user_id}",
                                           attachment=photos)
                    keyboard = VkKeyboard(inline=True)
                    keyboard.add_button('Дальше', color=VkKeyboardColor.PRIMARY)
                    self._send_message(event.chat_id, 'Выберите действие:', keyboard.get_keyboard())















# забирает каждые 20 людей, сдвигая offset
# двунаправленный итератор
class BotIter:

    def __init__(self, search_func):
        self.search_func = search_func
        self.users = search_func()
        self.offset = 0
        self.stop_offset = 1000
        self.inner_cursor = -1

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


# user_1 = VKinderBot("Орел", 1, 30)
# users_search = BotIter(user_1.filter_search())
#
# while True:
#     answer = input()
#     if answer == "вперед":
#         print(next(users_search))
#     elif answer == "назад":
#         print(users_search.prev())
#     else:
#         break





