from bot.bot import VKinderBot
from db.vkinder_db_models import create_table
from db.vkinder_db_main import engine


if __name__ == '__main__':

    create_table(engine)
    bot = VKinderBot()
    bot.run_bot()
