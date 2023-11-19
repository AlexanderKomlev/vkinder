from vk_api.longpoll import VkLongPoll, VkEventType
from config import main_token, user_token, user_vk_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


import requests
import vk_api


class VKinderBot:

    def __init__(self):

        self.vk_session = vk_api.VkApi(token=main_token)
        self.longpoll = VkLongPoll(self.vk_session)
        self.base_url = 'https://api.vk.com/method/'
        self.common_params = {'access_token': user_token, 'v': 5.131}

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

    def run_bot(self, session):

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                if event.text.lower() == 'start':
                    keyboard = VkKeyboard(inline=True)
                    keyboard.add_button('В черный список', color=VkKeyboardColor.NEGATIVE)
                    keyboard.add_button('В избранное', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_line()
                    keyboard.add_button('Назад', color=VkKeyboardColor.SECONDARY)
                    keyboard.add_button('Пропустить', color=VkKeyboardColor.PRIMARY)
                    keyboard.add_line()
                    keyboard.add_button('Показать избранное', color=VkKeyboardColor.POSITIVE)

                    self._send_message(event.chat_id, 'Выберите действие:', keyboard.get_keyboard())
                id = event.user_id
                # if event.text == '[club223509501|@club223509501] 1' and event.user_id == id:
                #     print(id)




