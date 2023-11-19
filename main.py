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

    bot = VKinderBot()
    bot.run_bot(session)
    # response = bot._get_needed_photos(620520542)
    # pprint(response)


