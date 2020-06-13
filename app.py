#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=True)
    seeking_description = db.Column(db.String)
    website = db.Column(db.String)
    shows = db.relationship('Show', backref='venues', lazy=True)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=True)
    seeking_description = db.Column(db.String)
    website = db.Column(db.String)
    shows = db.relationship('Show', backref='artists', lazy=True)

class Show(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime(), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  venues = Venue.query.all()
  group = {}
  for venue in venues:
    key = venue.city + venue.state
    group[key] = group.get(key, []) + [venue]
  for val in group.values():
    area = {}
    area['city'] = val[0].city
    area['state'] = val[0].state
    area['venues'] = val
    data.append(area)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  text = request.form['text']
  venues = Venue.query.with_entities(Venue.id, Venue.name).filter(func.lower(Venue.name).contains(func.lower(text))).all()
  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  data = Venue.query.get(venue_id)
  shows = data.shows
  past = list(filter(lambda x : x.start_time <= datetime.today(), shows))
  data.past_shows = []
  data.past_shows_count = len(past)
  for p in past:
    artist = Artist.query.get(p.artist_id)
    cur = {}
    cur['artist_id'] = p.artist_id
    cur['artist_name'] = artist.name
    cur['artist_image_link'] = artist.image_link
    cur['start_time'] = p.start_time.strftime("%Y-%m-%d %H:%M:%S")
    data.past_shows.append(cur)
  upcoming = list(filter(lambda x : x.start_time > datetime.today(), shows))
  data.upcoming_shows = []
  data.upcoming_shows_count = len(upcoming)
  for u in upcoming:
    artist = Artist.query.get(u.artist_id)
    cur = {}
    cur['arstist_id'] = u.artist_id
    cur['artist_name'] = artist.name
    cur['artist_image_link'] = artist.image_link
    cur['start_time'] = u.start_time.strftime("%Y-%m-%d %H:%M:%S")
    data.upcoming_shows.append(cur)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # called upon submitting the new venue listing form
  error = False
  form = VenueForm(request.form)
  try:
    if form.validate_on_submit():
      venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, 
      address=form.address.data, phone=form.phone.data, genres=form.genres.data, 
      image_link=form.image_link.data, facebook_link=form.facebook_link.data)
      
      db.session.add(venue)
      db.session.commit()
      flash('Venue added!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    # on successful db insert, flash success
    flash('Venue ' + form.name.data + ' was successfully listed!')
    return render_template('pages/home.html')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    
@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('venue deleted!')
  except:
    db.session.rollback()
    flash('error')
  finally:
    db.session.close()
  # return redirect(url_for('index'))
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  text = request.form['text']
  artists = Artist.query.with_entities(Artist.id, Artist.name).filter(func.lower(Artist.name).contains(func.lower(text))).all()
  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  data = Artist.query.get(artist_id)
  shows = data.shows
  past = list(filter(lambda x : x.start_time <= datetime.today(), shows))
  data.past_shows = []
  data.past_shows_count = len(past)
  for p in past:
    venue = Venue.query.get(p.venue_id)
    cur = {}
    cur['venue_id'] = p.venue_id
    cur['venue_name'] = venue.name
    cur['venue_image_link'] = venue.image_link
    cur['start_time'] = p.start_time.strftime("%Y-%m-%d %H:%M:%S")
    data.past_shows.append(cur)
  upcoming = list(filter(lambda x : x.start_time > datetime.today(), shows))
  data.upcoming_shows = []
  data.upcoming_shows_count = len(upcoming)
  for u in upcoming:
    venue = Venue.query.get(p.venue_id)
    cur = {}
    cur['venue_id'] = u.venue_id
    cur['venue_name'] = venue.name
    cur['venue_image_link'] = venue.image_link
    cur['start_time'] = u.start_time.strftime("%Y-%m-%d %H:%M:%S")
    data.upcoming_shows.append(cur)
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  try:
    if form.validate_on_submit():
      artist = Artist.query.get(artist_id)
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.image_link = form.image_link.data
      artist.seeking_description = form.seeking_description.data
      artist.facebook_link = form.facebook_link.data
      
      db.session.commit()
      flash("artist updated")
  except:
    flash(form.errors)
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  try:
    if form.validate_on_submit():
      venue = Venue.query.get(artist_id)
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.image_link = form.image_link.data
      venue.seeking_description = form.seeking_description.data
      venue.facebook_link = form.facebook_link.data
      
      db.session.commit()
      flash("venue updated")
    flash(form.errors)
  except:
    flash(form.errors)
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  form = ArtistForm(request.form)
  try:
    if form.validate_on_submit():
      artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, 
      phone=form.phone.data, genres=form.genres.data, seeking_description=form.seeking_description.data, 
      image_link=form.image_link.data, facebook_link=form.facebook_link.data)
      
      db.session.add(artist)
      db.session.commit()
      flash('Artist added!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    # on successful db insert, flash success
    flash('Artist ' + form.name.data + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = Show.query.all()
  for d in data:
    d.venue_name = Venue.query.get(d.venue_id).name
    artist = Artist.query.get(d.artist_id)
    d.artist_name = artist.name
    d.artist_image_link = artist.image_link
    d.start_time = d.start_time.strftime("%Y-%m-%d %H:%M:%S")
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  form = ShowForm(request.form)
  try:
    if form.validate_on_submit():
      show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data)
      
      db.session.add(show)
      db.session.commit()
      flash('Show added!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
