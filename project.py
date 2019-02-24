from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Game, GameItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "GameCatalog"


# Connect to Database and create database session
engine = create_engine('sqlite:///gameitemswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

"""
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=' +
    'fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s'
        % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange
        we have to split the token first on commas and select the
        first index which gives us the key : value for the server
        access token then we split it on colons to pull out the
        actual token value and replace the remaining
        quotes with nothing so that it can be used
        directly in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=' +
    '%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?' +
    'access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px; height: 300px;"
    output += "border-radius: 150px;-webkit-border-
    output += "radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions' +
    '?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out"
"""


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
        response = make_response(json.dumps('Current user is already connected.'), 200)
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

    login_session['username'] = data.get('', 'name')
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in!")

    return output

# User Helper Functions


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
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Game Information
@app.route('/game/<int:game_id>/item/JSON')
def gameItemJSON(game_id):
    game = session.query(Game).filter_by(id=game_id).one()
    items = session.query(GameItem).filter_by(
        game_id=game_id).all()
    return jsonify(GameItems=[i.serialize for i in items])


@app.route('/game/<int:game_id>/item/<int:gameitem_id>/JSON')
def gameItemsJSON(game_id, gameitem_id):
    Game_Item = session.query(GameItem).filter_by(id=gameitem_id).one()
    return jsonify(Game_Item=Game_Item.serialize)


@app.route('/game/JSON')
def gamesJSON():
    games = session.query(Game).all()
    return jsonify(games=[r.serialize for r in games])


# Show all games
@app.route('/')
@app.route('/game/')
def showGames():
    games = session.query(Game).order_by(asc(Game.name))
    if 'username' not in login_session:
        return render_template('publicgames.html', games=games)
    else:
        return render_template('games.html', games=games)

# Create a new game


@app.route('/game/new/', methods=['GET', 'POST'])
def newGame():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newGame = Game(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newGame)
        flash('New Game %s Successfully Created' % newGame.name)
        session.commit()
        return redirect(url_for('showGames'))
    else:
        return render_template('newGame.html')

# Edit a game


@app.route('/game/<int:game_id>/edit/', methods=['GET', 'POST'])
def editGame(game_id):
    editedGame = session.query(
        Game).filter_by(id=game_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedGame.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this game. Please create your own game in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedGame.name = request.form['name']
            flash('Game Successfully Edited %s' % editedGame.name)
            return redirect(url_for('showGames'))
    else:
        return render_template('editGame.html', game=editedGame)


# Delete a game
@app.route('/game/<int:game_id>/delete/', methods=['GET', 'POST'])
def deleteGame(game_id):
    gameToDelete = session.query(
        Game).filter_by(id=game_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if gameToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this game. Please create your own game in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(gameToDelete)
        flash('%s Successfully Deleted' % gameToDelete.name)
        session.commit()
        return redirect(url_for('showGames', game_id=game_id))
    else:
        return render_template('deleteGame.html', game=gameToDelete)

# Show items within a game


@app.route('/game/<int:game_id>/')
@app.route('/game/<int:game_id>/items/')
def showGameItems(game_id):
    game = session.query(Game).filter_by(id=game_id).one()
    creator = getUserInfo(game.user_id)
    items = session.query(GameItem).filter_by(
        game_id=game_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicgameitem.html', items=items, game=game, creator=creator)
    else:
        return render_template('gameitem.html', items=items, game=game, creator=creator)


# Create a new game item
@app.route('/game/<int:game_id>/item/new/', methods=['GET', 'POST'])
def newGameItem(game_id):
    if 'username' not in login_session:
        return redirect('/login')
    game = session.query(Game).filter_by(id=game_id).one()
    if login_session['user_id'] != game.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add game items to this game. Please create your own game in order to add items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newItem = GameItem(name=request.form['name'], description=request.form['description'], price=request.form[
                               'price'], game_id=game_id, user_id=game.user_id)
        session.add(newItem)
        session.commit()
        flash('%s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showGameItems', game_id=game_id))
    else:
        return render_template('newgameitem.html', game_id=game_id)

# Edit a game item


@app.route('/game/<int:game_id>/item/<int:gameitem_id>/edit', methods=['GET', 'POST'])
def editGameItem(game_id, gameitem_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(GameItem).filter_by(id=gameitem_id).one()
    game = session.query(Game).filter_by(id=game_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        session.add(editedItem)
        session.commit()
        flash('Game Item Successfully Edited')
        return redirect(url_for('showGameItems', game_id=game_id))
    else:
        return render_template('editgameitem.html', game_id=game_id, gameitem_id=gameitem_id, item=editedItem)


# Delete a game item
@app.route('/game/<int:game_id>/item/<int:gameitem_id>/delete', methods=['GET', 'POST'])
def deleteGameItem(game_id, gameitem_id):
    if 'username' not in login_session:
        return redirect('/login')
    game = session.query(Game).filter_by(id=game_id).one()
    itemToDelete = session.query(GameItem).filter_by(id=gameitem_id).one()
    if login_session['user_id'] != game.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete game items to this game. Please create your own game in order to delete items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Game Item Successfully Deleted')
        return redirect(url_for('showGameItems', game_id=game_id))
    else:
        return render_template('deleteGameItem.html', item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showGames'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showGames'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
