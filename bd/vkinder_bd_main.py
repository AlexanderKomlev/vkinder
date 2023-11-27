from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from bd.vkinder_bd_models import *
from config import name_driver, local_host, user, password, db


engine = create_engine(f"{name_driver}://"
                       f"{user}:"
                       f"{password}@"
                       f"localhost:{local_host}/"
                       f"{db}")
def write_users(**data):
    with Session(engine) as session:
        session.add(Users(**data))
        session.commit()

def write_favorite(**data):
    with Session(engine) as session:
        session.add(Favorite(**data))
        session.commit()

def write_black_list(**data):
    with Session(engine) as session:
        session.add(BlackList(**data))
        session.commit()

def write_parametr_offset(**data):
    with Session(engine) as session:
        session.add(ParametrOffset(**data))
        session.commit()

def check_user_bot(user_id):
    with Session(engine) as session:
        user = session.query(Users).filter(Users.user_id == user_id).first()
        return user
def check_favorite(user_id):
    with Session(engine) as session:
        user = session.query(Favorite).filter(Favorite.favorite_id == user_id).first()
        return user

def check_black(user_id):
    with Session(engine) as session:
        user = session.query(BlackList).filter(BlackList.black_id == user_id).first()
        return user
def show_favorites(user_id):
    with Session(engine) as session:
        result = session.query(Favorite).filter(Favorite.user_id == user_id).all()
        for row in result:
            yield row.fullname, row.link, row.photos

def get_offset(user_id):
    with Session(engine) as session:
        result = session.query(ParametrOffset).filter(ParametrOffset.user_id == user_id).first()
        if result:
            return result.offset
        return 0


def change_offset(user_id, offset):
    with Session(engine) as session:
        result = session.query(ParametrOffset).filter(ParametrOffset.user_id == user_id).first()
        result.offset = offset
        session.commit()