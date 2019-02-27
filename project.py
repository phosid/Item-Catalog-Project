from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    url_for,
    flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
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
        response = make_response(
                    json.dumps('Current user is already connected.'), 200)
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
    output += ' " style = "width: 300px;'\
              'height: 300px;'\
              'border-radius: 150px;'\
              '-webkit-border-radius: 150px;'\
              '-moz-border-radius: 150px;"> '
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
    except NoResultFound:
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
        response = make_response(
                    json.dumps('Failed to revoke token for given user.', 400))
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

""" Creates a new game in the database.

Returns:
    on GET: Page with fields to make a new game
    on POST: redirect to main page with all games
    shown with the new game just made.

"""


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

""" Edit a game in the database.

Returns:
    on GET: Goes to page with fields to edit the current game.
    on POST: submits the edits to the old game and
    redirects to show all games.

"""


@app.route('/game/<int:game_id>/edit/', methods=['GET', 'POST'])
def editGame(game_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedGame = session.query(
        Game).filter_by(id=game_id).one()
    if editedGame.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               " {alert('You are not authorized to edit this game. " \
               " Please create your own game in order to edit.');}" \
               "</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedGame.name = request.form['name']
            flash('Game Successfully Edited %s' % editedGame.name)
            return redirect(url_for('showGames'))
    else:
        return render_template('editGame.html', game=editedGame)


""" Deletes a game in the database.

Returns:
    on GET: Goes to page with fields to edit the current game.
    on POST: submits the edits to the old game and
    redirects to show all games.

"""


@app.route('/game/<int:game_id>/delete/', methods=['GET', 'POST'])
def deleteGame(game_id):
    gameToDelete = session.query(
        Game).filter_by(id=game_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if gameToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() " \
               " {alert('You are not authorized to delete this game. " \
               " Please create your own game in order to delete.');} " \
               "</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(gameToDelete)
        flash('%s Successfully Deleted' % gameToDelete.name)
        session.commit()
        return redirect(url_for('showGames', game_id=game_id))
    else:
        return render_template('deleteGame.html', game=gameToDelete)

""" Shows game items depending on the game.

    If user is not logged in: the page will not
    have edit, delete, or create capabilities.
    If user is logged in: page will have items
    where they can edit or delete if they are the creator.

"""


@app.route('/game/<int:game_id>/')
@app.route('/game/<int:game_id>/items/')
def showGameItems(game_id):
    game = session.query(Game).filter_by(id=game_id).one()
    creator = getUserInfo(game.user_id)
    items = session.query(GameItem).filter_by(
        game_id=game_id).all()
    if ('username' not in login_session or 
    creator.id != login_session['user_id']):
        return render_template('publicgameitem.html',
                               items=items,
                               game=game,
                               creator=creator)
    else:
        return render_template('gameitem.html',
                               items=items,
                               game=game,
                               creator=creator)


""" Creates a game item under the specific game.

    Returns:
        on GET: page will show fields where user
        can create new game items.
        on POST: page will show all game items
        under that game, including the new game item
        just created.

"""


@app.route('/game/<int:game_id>/item/new/', methods=['GET', 'POST'])
def newGameItem(game_id):
    if 'username' not in login_session:
        return redirect('/login')
    game = session.query(Game).filter_by(id=game_id).one()
    if login_session['user_id'] != game.user_id:
        return "<script>function myFunction() " \
               " {alert('You are not authorized to " \
               "add game items to this game. " \
               "Please create your own game in order to add items.');}" \
               "</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newItem = GameItem(name=request.form['name'],
                           description=request.form['description'],
                           price=request.form['price'],
                           game_id=game_id,
                           user_id=game.user_id)
        session.add(newItem)
        session.commit()
        flash('%s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showGameItems', game_id=game_id))
    else:
        return render_template('newgameitem.html', game_id=game_id)

""" Edits a game item.

    Returns:
        on GET: page will show fields where user
        can edit game items.
        on POST: page will show all game items
        under that game, including the new edited
        game item.

"""


@app.route('/game/<int:game_id>/item/<int:gameitem_id>/edit',
           methods=['GET', 'POST'])
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
        return render_template('editgameitem.html',
                               game_id=game_id,
                               gameitem_id=gameitem_id,
                               item=editedItem)


""" Deletes a game item from the database.

    Returns:
        on GET: page will ask to confirm if user
        wants to delete game item from database.
        on POST: game item will be deleted and
        will show updated game items for the game.

"""


@app.route('/game/<int:game_id>/item/<int:gameitem_id>/delete',
           methods=['GET', 'POST'])
def deleteGameItem(game_id, gameitem_id):
    if 'username' not in login_session:
        return redirect('/login')
    game = session.query(Game).filter_by(id=game_id).one()
    itemToDelete = session.query(GameItem).filter_by(id=gameitem_id).one()
    if login_session['user_id'] != game.user_id:
        return "<script>function myFunction() " \
               "{alert('You are not authorized to" \
               " delete game items to this game." \
               " Please create your own game in order to delete items.');}" \
               "</script><body onload='myFunction()'>"
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
