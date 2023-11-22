from dotenv import load_dotenv
from bd.vkinder_bd_models import create_table
from sqlalchemy.orm import sessionmaker
from bot.bot import VKinderBot
from pprint import pprint


import sqlalchemy
import os


if __name__ == '__main__':

    load_dotenv()
    user = os.getenv('user')
    password = os.getenv('password')
    database = os.getenv('database')
    engine = sqlalchemy.create_engine(f'postgresql://{user}:{password}@localhost:5432/{database}')
    create_table(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    bot = VKinderBot('Орел', 1, 25, session)
    # print(bot._user_data(182085643))
    # bot.run_bot(session)
    # response = bot._get_needed_photos(620520542)
    # pprint(response)
    # print(bot._search())
    bot._send_message2(620520542, 'test')

    session.close()
