from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Genre, Base, AnimeShow

engine = create_engine('sqlite:///animecatalog.db')
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

# Sports genre
genre1 = Genre(name="Sports")

session.add(genre1)
session.commit()

animeshow1 = AnimeShow(name="Haikyu!!", description="This underdog story revolves around a volleyball team that gains young talent who are determined to be the best in Japan.",
                     year="2014", genre=genre1)

session.add(animeshow1)
session.commit()

animeshow2 = AnimeShow(name="Run with the Wind", description="A former elite runner is put in an odd situation where he joins a prominent university running tournament with a team of novices.",
                     year="2018-2019", genre=genre1)

session.add(animeshow2)
session.commit()


# Horror/Psychological Thriller genre
genre2 = Genre(name="Horror/Psychological Thriller")

session.add(genre2)
session.commit()


animeshow3 = AnimeShow(name="Death Note", description="When a genius student discovers a book that can kill people by simply writing their name in the book, he sets out to .",
                     year="2006-2007", genre=genre2)

session.add(animeshow3)
session.commit()

animeshow4 = AnimeShow(
    name="Erased", description="A 29-year-old artist soon discovers that he is experiencing a mysterious power that lets him travel back in time. He uses this power to go back to his childhood days where an unsolved murder occurred.", year="2016", genre=genre2)

session.add(animeshow4)
session.commit()


# Comedy genre
genre3 = Genre(name="Comedy")

session.add(genre3)
session.commit()


animeshow5 = AnimeShow(name="Nichijou", description="Nichijou is a hilarious slice-of-life story about three childhood friends who are now navigating the stresses of highschool life together.",
                     year="2011", genre=genre3)

session.add(animeshow5)
session.commit()

animeshow6 = AnimeShow(name="One-Punch Man", description="The story revolves around Saitama, a guy who lives a rather unimpressive, ordinary life in a universe with villains and heroes. One day, while defending a child from a villain, he gets beat up in the process. Undergoing intensive training, he now becomes the strongest man ever: being able to take out anything with only one punch.",
                     year="2015", genre=genre3)

session.add(animeshow6)
session.commit()


print "added items!"
