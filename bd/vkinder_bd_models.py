from sqlalchemy import Column, String, Integer, CheckConstraint, func, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, deferred

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    fullname = Column(String(40), nullable=False)
    age = deferred(Column(String, nullable=False))
    gender = deferred(Column(String, nullable=False))
    city = Column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint(func.length(age.expression) == 2),
        CheckConstraint(func.length(gender.expression) == 1)
    )

    def __str__(self):
        return f"{self.user_id}: ({self.fullname}, {self.age}, {self.gender}, {self.city})"


class Favorites(Base):
    __tablename__ = "favorites"

    favorite_user_id = Column(Integer, primary_key=True)
    fullname = Column(String(40), nullable=False)
    user_id = Column(Integer, ForeignKey(Users.user_id), nullable=False)

    user = relationship(Users, backref=__tablename__)

    def __str__(self):
        return f"{self.favorite_user_id}: ({self.fullname}, {self.user_id})"

class BlackList(Base):
    __tablename__ = "black_list"

    black_user_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(Users.user_id), nullable=False)

    user = relationship(Users, backref=__tablename__)

    def __str__(self):
        return f"{self.blist_user_id}: {self.user_id}"

class Photos(Base):
    __tablename__ = "photos"

    photo_id = Column(Integer, primary_key=True)
    link = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey(Favorites.favorite_user_id), nullable=False)

    favorite_user = relationship(Favorites, backref=__tablename__)

    def __str__(self):
        return f"{self.photo_id}: ({self.link}, {self.user_id})"


def create_table(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
