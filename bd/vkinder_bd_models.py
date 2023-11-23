from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    fullname = Column(String(40), nullable=False)
    gender = Column(Integer, nullable=False)  # 1 - женщина, 2 - мужчина
    age = Column(Integer, nullable=False)
    city = Column(String(20), nullable=False)

    def __str__(self):
        return f"{self.id}: ({self.user_id}, {self.fullname}, {self.age}, {self.gender}, {self.city})"


class Viewed(Base):
    __tablename__ = "viewed"

    id = Column(Integer, primary_key=True)
    fullname = Column(String(40), nullable=False)
    viewed_user_id = Column(Integer, nullable=False)
    photos = Column(String)
    status = Column(Integer, nullable=False)  # 0 просмотрено, 1 избранное
    user_id = Column(Integer, ForeignKey(Users.user_id, ondelete="CASCADE"), nullable=False)

    user = relationship(Users, backref=__tablename__)

    def __str__(self):
        return f"{self.id}: ({self.favorite_user_id}, {self.fullname}, {self.user_id})"


class BlackList(Base):
    __tablename__ = "black_list"

    id = Column(Integer, primary_key=True)
    black_user_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey(Users.user_id, ondelete="CASCADE"), nullable=False)

    user = relationship(Users, backref=__tablename__)

    def __str__(self):
        return f"{self.id}: ({self.black_user_id}, {self.user_id})"


def create_table(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
