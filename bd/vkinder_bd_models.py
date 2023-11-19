import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    user_id = sq.Column(sq.Integer, primary_key=True)
    fullname = sq.Column(sq.String(length=40), nullable=False)
    age = sq.Column(sq.String(length=2), nullable=False)
    gender = sq.Column(sq.String(1), nullable=False)
    city = sq.Column(sq.String(15), nullable=False)

    def __str__(self):
        return f'{self.user_id}|{self.fullname}|{self.age}|{self.gender}|{self.city}'


class Favorites(Base):
    __tablename__ = 'favorites'

    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'), primary_key=True)
    favorite_user_id = sq.Column(sq.Integer, nullable=False)

    user = relationship(Users, backref='favorites')


def create_table(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
