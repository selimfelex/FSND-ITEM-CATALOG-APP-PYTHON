# Python 2.7.12
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from database_setup import Base, Category, Item, User

# NEW import for step 2
from flask import session as login_session
import random
import string

# import of step 5 gconnect
# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from pprint import pprint

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
# Create a state token to prevent request forgery.
# Store it in the session for later validation
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))  # noqa
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)  # noqa
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exist, if if doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)  # noqa
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))  # noqa
        response.headers['Content-Type'] = 'application/json'
        return response

# @app.route('/categories/JSON')
# def categoryJSON():
#    categories = session.query(Category).all()
#    items = session.query(Item).all()
#    return jsonify(category= [r.serialize for r in categories])


# Add JSON API to view all categories along with their items
@app.route('/allcategories/JSON')
def getCatalog():
    categories = session.query(Category).options(joinedload(Category.items)).all()  # noqa
    return jsonify(Catalog=[dict(c.serialize, items=[i.serialize
                                                     for i in c.items])
                   for c in categories])
    pprint(getCatalog())


# Add JSON API to view specific item in a specific category
@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def catItemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


# show all categories with recently added items (main page)
@app.route('/')
@app.route('/categories')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(Item.category_id.desc())
    # return "this page will show all categories"
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories, items=items)  # noqa
    else:
        return render_template('categories.html', categories=categories, items=items)  # noqa


# this will be for making a new categories
@app.route('/category/newcategory', methods=['GET', 'POST'])
def newCategory():
    # return "this page will be for making a new categories"
    # check if the user is logged in or not if not redirect to login
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'], user_id=login_session['user_id'])  # noqa
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# this will be for editting category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    # return "this page will be for editting category %s"   %category_id
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', category=editedCategory)


# this will be for deleting category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    # return "this page will be for deleting category %s"   %category_id
    # check if the user is logged in or not if not redirect to login
    if 'username' not in login_session:
        return redirect('/login')
    categorytoDelete = session.query(Category).filter_by(id=category_id).one()
    if categorytoDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('you are not authorized to delete this restaurant. please create your own category in order to delete .');}</script><body onload='myFunction()''>"  # noqa
    if request.method == 'POST':
        session.delete(categorytoDelete)
        flash('%s Successfully Deleted' % categorytoDelete.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html', category=categorytoDelete)  # noqa


# this will show all items in selected (clicked ) category
@app.route('/category/<int:category_id>/items')
def showCategoryItems(category_id):
    # return "this page will show all category %s items" % category_id
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(category_id=category_id).all()
    itemsCount = len(items)
    if 'username' not in login_session or creator.id != login_session['user_id']:  # noqa
        return render_template('publiccategoryItems.html', items=items, category=category, itemscount=itemsCount, categories=categories, creator=creator)  # noqa
    else:
        return render_template('categoryItems.html', items=items, category=category, itemscount=itemsCount, categories=categories)  # noqa


# this will show  specific item details
@app.route('/category/<int:category_id>/item/<int:item_id>')
def showItemDetails(category_id, item_id):
    item = session.query(Item).filter_by(category_id=category_id, id=item_id).one()  # noqa
    category = session.query(Category).filter_by(id=category_id)
    creator = getUserInfo(item.user_id)
    # return "this page will show  specific item in a specific category
    if 'username' not in login_session or creator.id != login_session['user_id']:  # noqa
        return render_template('publicshowItemDetails.html', category=Category, item=item)  # noqa
    else:
        return render_template('showItemDetails.html', category=Category, item=item)  # noqa


# this will be for making a new Item
@app.route('/category/item/new', methods=['GET', 'POST'])
def newItem():
    # return "this page will be for making a new item"
    # check if the user is logged in or not if not redirect to login
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    if request.method == 'POST':
        # catselected = request.form.get('catf')
        # catselectd-id= session.query()
        newItem = Item(name=request.form['name'], description=request.form['description'], user_id=login_session['user_id'], price=request.form['price'], category_id=request.form.get('catf'))  # noqa
        # chek if the user is the creator of the category or not
        if login_session['user_id'] != newItem.user_id:
            return "<script>function myFunction() {alert('You are not authorized to add menu items to this category. Please create your own category in order to add items.');}</script><body onload='myFunction()''>"  # noqa
        else:
            session.add(newItem)
            flash('New Item %s Successfully Created' % newItem.name)
            session.commit()
            return redirect(url_for('showCategories'))
    else:
        return render_template('newCategoryItem.html', categories=categories)


# this will be for editing specific item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])  # noqa
def editItem(category_id, item_id):
    # return "this page will be for editing Item  inside category
    # check if the user is logged in or not if not redirect to login
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != editedItem.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit this  items in this category. Please create your own category in order to add items.');}</script><body onload='myFunction()''>"  # noqa
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']

        if request.form['description']:

            editedItem.description = request.form['name']

        if request.form['price']:

            editedItem.price = request.form['price']

        if request.form['catf']:

            editedItem.category_id = request.form.get('catf')

        session.add(editedItem)

        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editCategoryItem.html', item=editedItem, category=category, categories=categories, category_id=category_id, item_id=item_id)  # noqa


# this will be for deleting specific item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])  # noqa
def deleteItem(category_id, item_id):
    # check if the user is logged in or not if not redirect to login
    if 'username' not in login_session:
        return redirect('/login')
    # return "this page will be for deleting Item inside category
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete this  items in this category. Please create your own category in order to delete items.');}</script><body onload='myFunction()''>"  # noqa
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategoryItem.html', item=itemToDelete)


# Fake category
# category = {'name': 'Networks', 'id': '1'}
# categories = [{'name': 'Networks', 'id': '1'}, {'name':'Laptops', 'id':'2'},{'name':'Computers', 'id':'3'}]  # noqa
# Fake Menu Items
# items = [ {'name':'CYBEROAM CR35ING', 'description':'Next-Generation network security appliances that include UTM security features and performance required for future networks', 'price':'$500.99','category_id':'1', 'id':'1'}, {'name':'ASUS FX504GD-DM364T','description':'TUF GAMING LAPTOP - INTEL CORE I7-8750H, 15.6-INCH FHD, 1TB + 128GB SSD, 16GB', 'price':'$300.99', 'category_id':'2','id':'2'},{'name':'ASUS GAMING 2TB M.2', 'description':'Windows 10 Pro CPU: Intel Core i5 8600 MEMORY: DDR4 2400MHz 8GB MOTHERBOARD: ASUS PRIME Z370-A','price':'$566.99', 'category_id':'3','id':'3'}]  # noqa
# item =  {'name':'CYBEROAM CR35ING', 'description':'Next-Generation network security appliances that include UTM security features and performance required for future networks', 'price':'$5.99','category_id':'1', 'id':'1'}  # noqa


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
