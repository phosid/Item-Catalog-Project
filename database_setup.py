# Configuration code used to import all necessary modules.
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# Make instance of declarative base
Base = declarative_base()

# Class code used to represent the data in python.
# Table represents a specific table in our database.
# Mapper connects the columns of our table to the class that represents it.

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	email = Column(String(250), nullable=False)
	picture = Column(String(250))


class Genre(Base):
	__tablename__ = 'genre'
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)


	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
			'name': self.name,
			'id': self.id,
		}
	

class AnimeShow(Base):
	__tablename__ = 'anime_show'
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	year = Column(String(4))
	description = Column(String(250))
	genre_id = Column(Integer, ForeignKey('genre.id'))
	genre = relationship(Genre)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return {
			'name': self.name,
			'year': self.year,
			'description': self.description,
			'id': self.id,
		}
	

# Add configuration to create or connect the database and adds tables and columns.
engine = create_engine('sqlite:///animecatalogwithusers.db')
Base.metadata.create_all(engine)