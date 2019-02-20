from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, AnimeShow, Genre

# New imports for this step
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
APPLICATION_NAME = "Anime Website"

# Connect to Database and create database session
engine = create_engine('sqlite:///animecatalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE = state)

"""

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data
	print "access token received %s " % access_token


	app_id = json.loads(open('fb_client_secrets.json'), 'r').read()
	['web']['app_id']
	app_secret = json.loads(
		open('fb_client_secrets.json', 'r'),read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	# Use token to get user info from API
	userinfo_url = "https://graph.facebook.com/v2.8/me"
	'''
		Due to the formatting for the result from the server token exchange we have to
		split the token first on commas and select the first index which gives us the key : value
		for the server access token then we split it on colons to pull out the actual token value
		and replace the remaining quotes with nothing so that it can be used directly in the graph api calls
	'''

	token = result.split(',')[0].split[':'][1].replace('"', '')

	url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	# print "url sent for API access: %s" % url
	# print "API JSON result: %s" % result
	data = json.loads(result)
	login_session['provider'] = facebook
	login_session['username'] = data["name"]
	login_session['email'] = data["email"]
	login_session['facebook_id'] = data["id"]

	# The token must be stored in the login_session  in order to properly logout
	login_session['access_token'] = token

	# Get user picture
	url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
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
	output += ' " style ="width: 300px; height: 300px; border-radius: 150px; -webkit-border-radius: 150px; -moz-border-radius: 150px;"> '

	flash("Now logged in as %s" % login_session['username'])
	return output

"""

"""
@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	# The access token must be included to successfully logout
	access_token = login_session['access_token']
	url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	return "you have been logged out"
"""

@app.route('/gconnect', methods=['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope= '')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
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
			json.dumps("Token's user ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check to see if user is already logged in
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
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output

# User Helper Functions

def createUser(login_session):
	newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
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
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	print 'In gdisconnect access token is %s', access_token
	print 'User name is: '
	print login_session['username']
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
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
		response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response

# JSON APIs to view Anime Show Information
@app.route('/catalog/<int:genre_id>/show/JSON')
def animeCatalogJSON(genre_id):
	genre = session.query(Genre).filter_by(id=genre_id).one()
	shows = session.query(AnimeShow).filter_by(genre_id = genre.id).all()
	return jsonify(AnimeShows=[i.serialize for i in shows])

@app.route('/catalog/<int:genre_id>/show/<int:animeshow_id>/JSON')
def animeShowJSON(genre_id, animeshow_id):
	Anime_Show = session.query(AnimeShow).filter_by(id=animeshow_id).one()
	return jsonify(Anime_Show=Anime_Show.serialize)

@app.route('/catalog/JSON')
def genreJSON():
	genre = session.query(Genre).all()
	return jsonify(genre=[r.serialize for r in genre])


# Show all shows in catalog

@app.route('/')
@app.route('/catalog/')
def homepage():
	genre = session.query(Genre).order_by(asc(Genre.name))
	if 'username' not in login_session:
		return render_template('publichomepage.html', genre = genre)
	else:
		return render_template('homepage.html', genre = genre)

# View shows in the genre

@app.route('/catalog/<int:genre_id>/')
def animeCatalog(genre_id):
	genre = session.query(Genre).filter_by(id = genre_id).one()
	creator = getUserInfo(genre.user_id)
	shows = session.query(AnimeShow).filter_by(genre_id = genre.id).all()
	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicanimeshow.html', shows= shows, genre = genre, creator=creator)
	else:
		return render_template('animeshow.html', genre = genre, shows = shows, creator = creator)

# Create a new anime show

@app.route('/catalog/<int:genre_id>/new/', methods=['GET','POST'])
def newAnimeShow(genre_id):
	if 'username' not in login_session:
		return redirect('/login')
	genre = session.query(Genre).filter_by(id=genre_id).one()
	if request.method == 'POST':
		newItem = AnimeShow(name = request.form['name'], year = request.form['year'], description = request.form['description'], genre_id = genre_id, user_id=login_session['user_id'])
		session.add(newItem)
		session.commit()
		flash('New Anime Show %s Successfully Created' % (newItem.name))
		return redirect(url_for('animeCatalog', genre_id = genre_id))
	else:
		return render_template('newanimeshow.html', genre_id = genre_id)

# Edit an anime show

@app.route('/catalog/<int:genre_id>/<int:animeshow_id>/edit/', methods = ['GET', 'POST'])
def editAnimeShow(genre_id, animeshow_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedShow = session.query(AnimeShow).filter_by(id = animeshow_id).one()
	genre = session.query(Genre).filter_by(id=genre_id).one()
	if request.method == 'POST':
		if request.form['name']:
			editedShow.name = request.form['name']
		if request.form['year']:
			editedShow.year = request.form['year']
		if request.form['description']:
			editedShow.description = request.form['description']
		session.add(editedShow)
		session.commit()
		flash('Anime show successfully edited')
		return redirect(url_for('animeCatalog', genre_id = genre_id))
	else:
		return render_template('editanimeshow.html', genre_id = genre_id, animeshow_id = animeshow_id, item = editedShow)


# Delete an anime show

@app.route('/catalog/<int:genre_id>/<int:animeshow_id>/delete/', methods = ['GET', 'POST'])
def deleteAnimeShow(genre_id, animeshow_id):
	if 'username' not in login_session:
		return redirect('/login')
	genre = session.query(Genre).filter_by(id=genre_id).one()
	showToDelete = session.query(AnimeShow).filter_by(id = animeshow_id).one()
	if request.method == 'POST':
		session.delete(showToDelete)
		session.commit()
		flash('Anime show successfully deleted')
		return redirect(url_for('animeCatalog', genre_id = genre_id))
	else:
		return render_template('deleteanimeshow.html', item = showToDelete)


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)