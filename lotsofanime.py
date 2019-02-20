from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Genre, Base, AnimeShow, User

engine = create_engine('sqlite:///animecatalogwithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1= User(name="Admin", email="admin@udacity.com", picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Sports genre
genre1 = Genre(user_id=1, name="Sports")

session.add(genre1)
session.commit()

animeshow1 = AnimeShow(user_id=1, name="Haikyu!!", description="This underdog story revolves around a volleyball team that gains young talent who are determined to be the best in Japan.",
                     year="2014", genre=genre1)

session.add(animeshow1)
session.commit()

animeshow2 = AnimeShow(user_id=1, name="Run with the Wind", description="A former elite runner is put in an odd situation where he joins a prominent university running tournament with a team of novices.",
                     year="2018-2019", genre=genre1)

session.add(animeshow2)
session.commit()


# Horror/Psychological Thriller genre
genre2 = Genre(user_id=1, name="Horror/Psychological Thriller")

session.add(genre2)
session.commit()


animeshow3 = AnimeShow(user_id=1, name="Death Note", description="When a genius student discovers a book that can kill people by simply writing their name in the book, he sets out to .",
                     year="2006-2007", genre=genre2)

session.add(animeshow3)
session.commit()

animeshow4 = AnimeShow(user_id=1, 
    name="Erased", description="A 29-year-old artist soon discovers that he is experiencing a mysterious power that lets him travel back in time. He uses this power to go back to his childhood days where an unsolved murder occurred.", year="2016", genre=genre2)

session.add(animeshow4)
session.commit()


# Comedy genre
genre3 = Genre(user_id=1, name="Comedy")

session.add(genre3)
session.commit()


animeshow5 = AnimeShow(user_id=1, name="Nichijou", description="Nichijou is a hilarious slice-of-life story about three childhood friends who are now navigating the stresses of highschool life together.",
                     year="2011", genre=genre3)

session.add(animeshow5)
session.commit()

animeshow6 = AnimeShow(user_id=1, name="One-Punch Man", description="The story revolves around Saitama, a guy who lives a rather unimpressive, ordinary life in a universe with villains and heroes. One day, while defending a child from a villain, he gets beat up in the process. Undergoing intensive training, he now becomes the strongest man ever: being able to take out anything with only one punch.",
                     year="2015", genre=genre3)

session.add(animeshow6)
session.commit()

# Action/Adventure genre
genre4 = Genre(user_id=1, name="Action/Adventure")

session.add(genre4)
session.commit()

animeshow7 = AnimeShow(user_id=1, name="Full Metal Alchemist: Brotherhood", description="The series follows the story of two alchemist brothers, Edward and Alphonse Elric, who want to restore their bodies after a disastrous failed attempt to bring their mother back to life through alchemy.",
                     year="2009-2010", genre=genre4)

session.add(animeshow7)
session.commit()

# Fantasy/Magic genre
genre5 = Genre(user_id=1, name="Fantasy/Magic")

session.add(genre5)
session.commit()

animeshow8 = AnimeShow(user_id=1, name="No Game No Life", description="Sora and Shiro are two hikikomori step-siblings who are known in the online gaming world as Blank, an undefeated group of gamers. One day, they are challenged to a game of chess by Tet, a god from another reality. The two are victorious and are offered to live in a world that centers around games.",
                     year="2014", genre=genre5)

session.add(animeshow8)
session.commit()


print "added items!"
