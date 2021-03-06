
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request, redirect, \
                  url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from werkzeug.contrib.fixers import ProxyFix
from flask import session as login_session
from flask import make_response
import random, string
import os

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

CLIENT_ID = json.loads(
    open('secrets/client_secret.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

app = Flask(__name__)

def create_user(login_session):
    new_user = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('secrets/fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('secrets/fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]
    print result
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?fields=email,name,id&{0}'.format(token)
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    print data
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?{0}&redirect=0&height=200&width=200'.format(token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/{0}/permissions {1}'.format(facebook_id,access_token)
    http = httplib2.Http()
    result = http.request(url, 'DELETE')[1]
    try:
        del login_session['credentials']
        del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
    except:
        pass
    flash('Successfully disconnected.')
    return redirect('/restaurants')

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('secrets/client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        print response
        return response

    access_token = credentials.access_token
    print access_token
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={0}'.format(access_token)
    http = httplib2.Http()
    result = json.loads(http.request(url, 'GET')[1])

    # if there was an error in the access token info and abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    # check if id is the same and abort on mismatch
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # check if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'gplus'

    # Get user info

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # check if user already exists in database
    user_id = get_user_id(data['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as {0}".format(login_session['username']))
    return output

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('credentials')

    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/restaurants')
    url = 'https://accounts.google.com/o/oauth2/revoke?token={0}'.format(access_token)
    http = httplib2.Http()
    result = http.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash('Successfully disconnected.')
        return redirect('/restaurants')
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        # Reset the user's session anyway.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
        return response

# create a state token to prevent request forgery
# store it in the session for later validation
@app.route('/login')
def show_login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# create a logout url
@app.route('/logout')
def logout():
    if login_session['provider'] == 'gplus':
        return redirect('/gdisconnect')
    if login_session['provider'] == 'facebook':
        return redirect('/fbdisconnect')

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
    if 'username' not in login_session:
        return render_template('publicrestaurants.html', restaurants=restaurants)
    return render_template('restaurants.html', restaurants=restaurants)

# create a new restaurant
@app.route('/new/', methods=['GET','POST'])
def new_restaurant():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            new_restaurant = Restaurant(name=request.form['name'],
                user_id = login_session['user_id'])
            session.add(new_restaurant)
            session.commit()
            flash('new Restaurant created for ' + login_session['username'] + '.' )
        return redirect(url_for('restaurants'))
    else:
        return render_template('newRestaurant.html')

# edit a restaurant
@app.route('/edit/<int:restaurant_id>/', methods=['GET', 'POST'])
def edit_restaurant(restaurant_id):
    edited_restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    creator = get_user_info(Restaurant.user_id)
    if 'username' not in login_session  or creator != login_session['user_id']:
        flash('You are not allowed to edit this restaurant')
        return redirect('/restaurants')
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

# delete a restaurant
@app.route('/delete/<int:restaurant_id>/', methods=['GET', 'POST'])
def delete_restaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    delete_restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        session.delete(delete_restaurant)
        session.commit()
        flash('Restaurant deleted!')
        return redirect(url_for('restaurants', restaurant_id=restaurant_id))
    return render_template('deleteRestaurant.html', restaurant=delete_restaurant)

# show a restaurant menu
@app.route('/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/')
def restaurant_menu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    creator = get_user_info(Restaurant.user_id)
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id)
    if 'username' not in login_session or creator != login_session['user_id']:
        return render_template('publicmenu.html', restaurant=restaurant, items=items, creator=creator)
    # output = '<br><br>'.join(['<br>'.join([item.name,item.price,item.description]) for item in items])
    return render_template('menu.html', restaurant=restaurant, items=items)


# create a new menu item for a restaurant
@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    creator = restaurant.user_id
    if 'username' not in login_session or creator != login_session['user_id']:
        return render_template('publicmenu.html', restaurant_id=restaurant_id)
    if request.method == 'POST':
        if request.form['name']:
            newItem = MenuItem(name=request.form['name'],
                               restaurant_id=restaurant_id,
                               user_id=restaurant.user_id)
            session.add(newItem)
            session.commit()
            flash('new menu item created!')
        return redirect(url_for('restaurant_menu', restaurant_id=restaurant_id))
    else:
        return render_template('newMenuItem.html', restaurant_id=restaurant_id)

# edit a menu item for a restaurant
@app.route('/restaurants/<int:restaurant_id>/edit/<int:menu_id>/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
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

# delete a menu item for a restaurant
@app.route('/restaurants/<int:restaurant_id>/delete/<int:menu_id>/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteMenuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(deleteMenuItem)
        session.commit()
        flash('Menu item deleted!')
        return redirect(url_for('restaurant_menu', restaurant_id=restaurant_id))
    return render_template('deleteMenuItem.html', restaurant_id=restaurant_id, item=deleteMenuItem)

if __name__ == '__main__':
    app.secret_key = '7YNBNTKR828881KVX59IBF1HMN3S16KR'
    app.debug = True
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host=os.getenv('IP','0.0.0.0'), port=int(os.getenv('PORT', '8080')))
