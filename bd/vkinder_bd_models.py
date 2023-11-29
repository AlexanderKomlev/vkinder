from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship


import logging


logging.basicConfig(level=logging.DEBUG,
                    filename='logfile.log',
                    encoding='utf-8',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


Base = declarative_base()


class Users(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    fullname = Column(String(40), nullable=False)
    gender = Column(Integer, nullable=False)  # 1 - женщина, 2 - мужчина
    age = Column(Integer)
    city = Column(String(20))

    def __str__(self):
        return f"{self.id}: ({self.user_id}, {self.fullname}, {self.age}, {self.gender}, {self.city})"


class ParametrOffset(Base):

    __tablename__ = "parametr_offest"

    id = Column(Integer, primary_key=True)
    offset = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey(Users.user_id, ondelete="CASCADE"), nullable=False)

    user = relationship(Users, backref=__tablename__)

    def __str__(self):
        return f"{self.id}: ({self.offset}, {self.user_id})"


class Favorite(Base):

    __tablename__ = "favorite"

    id = Column(Integer, primary_key=True)
    fullname = Column(String(40), nullable=False)
    favorite_id = Column(Integer, nullable=False)
    link = Column(String)
    photos = Column(String)
    user_id = Column(Integer, ForeignKey(Users.user_id, ondelete="CASCADE"), nullable=False)

    user = relationship(Users, backref=__tablename__)

    def __str__(self):
        return f"{self.id}: ({self.fullname}, {self.favorite_id}, {self.link}, {self.photos}, {self.user_id})"


class BlackList(Base):

    __tablename__ = "black_list"

    id = Column(Integer, primary_key=True)
    fullname = Column(String(40), nullable=False)
    black_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey(Users.user_id, ondelete="CASCADE"), nullable=False)

    user = relationship(Users, backref=__tablename__)

    def __str__(self):
        return f"{self.id}: ({self.fullname}, {self.black_id}, {self.user_id})"


def create_table(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    logging.debug('В БД созданы таблицы "users", "parametr_offset", "favorite", "black_list"')
