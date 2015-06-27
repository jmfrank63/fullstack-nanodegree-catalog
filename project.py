
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request, redirect, \
                  url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

app = Flask(__name__)

# Making an api endpoint GET request
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def menu_restaurant_JSON(restaurant_id):
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id)
    return jsonify(MenuItems=[item.serialize for item in items])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menu_restaurant_menu_JSON(restaurant_id, menu_id):
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=menuItem.serialize)

@app.route('/')
@app.route('/restaurants/')
def restaurants():
    restaurants = session.query(Restaurant)
    return render_template('restaurants.html', restaurants=restaurants)

@app.route('/new/', methods=['GET','POST'])
def new_restaurant():
    if request.method == 'POST':
        if request.form['name']:
            newRestaurant = Restaurant(name=request.form['name'])
            session.add(newRestaurant)
            session.commit()
            flash('new Restaurant created!')
        return redirect(url_for('restaurants'))
    else:
        return render_template('newRestaurant.html')

@app.route('/edit/<int:restaurant_id>/', methods=['GET', 'POST'])
def edit_restaurant(restaurant_id):
    edited_restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            edited_restaurant.name = request.form['name']
        session.add(edited_restaurant)
        session.commit()
        flash('Restaurant edited!')
        return redirect(url_for('restaurants'))
    else:
        return render_template('editRestaurant.html',
                                restaurant_id=restaurant_id,
                                restaurant=edited_restaurant)

@app.route('/delete/<int:restaurant_id>/')
def delete_restaurant(restaurant_id):
    return "TODO: page to delete restaurant"

@app.route('/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/')
def restaurant_menu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id)
    # output = '<br><br>'.join(['<br>'.join([item.name,item.price,item.description]) for item in items])
    return render_template('menu.html', restaurant = restaurant, items = items)

# Task 1: Create route for newMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        if request.form['name']:
            newItem = MenuItem(name=request.form['name'],restaurant_id=restaurant_id)
            session.add(newItem)
            session.commit()
            flash('new menu item created!')
        return redirect(url_for('restaurant_menu', restaurant_id=restaurant_id))
    else:
        return render_template('newMenuItem.html', restaurant_id=restaurant_id)

# Task 2: Create route for editMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/edit/<int:menu_id>/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        flash('Menu item edited!')
        return redirect(url_for('restaurant_menu', restaurant_id=restaurant_id))
    else:
        # USE THE RENDER_TEMPLATE FUNCTION BELOW TO SEE THE VARIABLES YOU
        # SHOULD USE IN YOUR EDITMENUITEM TEMPLATE
        return render_template(
            'editMenuItem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=editedItem)

# Task 3: Create a route for deleteMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/delete/<int:menu_id>/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    deleteMenuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(deleteMenuItem)
        session.commit()
        flash('Menu item deleted!')
        return redirect(url_for('restaurant_menu', restaurant_id=restaurant_id))
    return render_template('deleteMenuItem.html', restaurant_id=restaurant_id, item=deleteMenuItem)


if __name__ == '__main__':
    app.secret_key = 'development_super_secret_key!'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8080)

