import sys

from sqlalchemy import Column, ForeignKey, Integer, String, BLOB

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

######################################################
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(80), nullable=False)
    picture = Column(BLOB)

    @property
    def serialize(self):
        ''' Returns object data in an easy serializable format
        '''
        return { 'id' : self.id,
                 'name' : self.name,
                 'email' : self.email,
                 'picture' : self.picture, }


class Restaurant(Base):
    __tablename__ = 'restaurant'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        ''' Returns object data in an easy serializable format
        '''
        return { 'name': self.name,
                 'id': self.id,
                 'user_id': self.user_id, }


class MenuItem(Base):
    __tablename__ = 'menu_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    course = Column(String(250))
    description = Column(String(250))
    price = Column(String(8))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(Restaurant)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        ''' Returns object data in an easy serializable format
        '''
        return { 'name' : self.name,
                 'description' : self.description,
                 'id' : self.id,
                 'price' : self.price,
                 'course' : self.course,
                 'restaurant_id' : self.restaurant_id,
                 'user_id' : self.user_id }

################### insert at end of file ############

engine = create_engine('sqlite:///restaurantmenuwithusers.db')

Base.metadata.create_all(engine)
