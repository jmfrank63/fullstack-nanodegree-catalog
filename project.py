
# A very simple Flask Hello World app for you to get started with...

from flask import Flask

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

def create_session():
    engine = create_engine('sqlite:///restaurantmenu.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind = engine)
    return DBSession()

app = Flask(__name__)

@app.route('/')
@app.route('/hello')
def hello_world():
    session = create_session()
    restaurant = session.query(Restaurant).first()
    output = restaurant.name
    return output

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 8080)

