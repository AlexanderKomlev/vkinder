from config import app_token
from bot.bot import VKinderBot
from bd.vkinder_bd_models import create_table
from bd.vkinder_bd_main import engine


if __name__ == '__main__':

    create_table(engine)
    bot = VKinderBot()
    bot.run_bot()
