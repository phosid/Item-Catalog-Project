from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Game, Base, GameItem, User

engine = create_engine('sqlite:///gameitemswithusers.db')
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


# Create user
User1 = User(name="Sidney Pho", email="phosidney@gmail.com")
session.add(User1)
session.commit()

# Game Items for League of Legends
game1 = Game(user_id=1, name="League of Legends")

session.add(game1)
session.commit()

gameItem1 = GameItem(user_id=1, name="Infinity Edge", description="+80 atk, +25% crit chance; critical strikes deal 225% damage instead of 200%",
                     price="3400 gold", game=game1)

session.add(gameItem1)
session.commit()


gameItem2 = GameItem(user_id=1, name="Essence Reaver", description="+60 atk, +20% cooldown reduction, +25% crit chance; basic attks refund 1.5% of your missing mana",
                     price="3200 gold", game=game1)

session.add(gameItem2)
session.commit()

gameItem3 = GameItem(user_id=1, name="Runaan's Hurricane", description="+40% atk speed, +25% crit chance, +7% movement speed; UNIQUE Passive - Wind's Fury: When basic attacking, bolts are fired at up to 2 enemies near the target, each dealing (40% of atk dmg) physical damage. Bolts can critically strike and apply on hit effects",
                     price="2600 gold", game=game1)

session.add(gameItem3)
session.commit()

gameItem4 = GameItem(user_id=1, name="Trinity Force", description="+250 health, +250 mana, +25 atk dmg, +40% atk speed, +20% cooldown reduction, +5% movement speed; TONS OF DAMAGE",
                     price="3733 gold", game=game1)

session.add(gameItem4)
session.commit()

gameItem5 = GameItem(user_id=1, name="Morellonomicon", description="+70 ability power, +300 health; UNIQUE Passive - Touch of Death: +15 magic penetration; UNIQUE Passive - Cursed Strike: Magic damage dealth to champions inflicts them with Grievous Wounds for 3 seconds",
                     price="3000 gold", game=game1)

session.add(gameItem5)
session.commit()

gameItem6 = GameItem(user_id=1, name="Mercurial Scimitar", description="+50 atk dmg, +35 magic resist, +10% life steal; UNIQUE Active - Quicksilver: Removes all debuffs and also grants +50 bonus movement speed for 1 second",
                     price="3400 gold", game=game1)

session.add(gameItem6)
session.commit()



# Game Items for Maple Story
game2 = Game(user_id=1, name="Maple Story")

session.add(game2)
session.commit()


gameItem1 = GameItem(user_id=1, name="Zakum Helmet", description="Weapon Def: 150/Magic Def: 150, Effects: STR+15, DEX+15, INT+15, LUK+15, Accuracy+20, Avoidability+20",
                     price="500,000 mesos", game=game2)

session.add(gameItem1)
session.commit()

gameItem2 = GameItem(user_id=1, name="Infinite Magic Arrows",
                     description="Magic arrows blessed by the spirits. Equip them with the Dual Bowguns to gain infinite ammo. Potential can be added with a Potential Scroll", price="580,000 mesos", game=game2)

session.add(gameItem2)
session.commit()

gameItem3 = GameItem(user_id=1, name="Elemental Staff 8", description="Weapon atk: 108, Magic atk: 178, LUK+3",
                     price="190,000 mesos", game=game2)

session.add(gameItem3)
session.commit()


# Game Items for World of Warcraft
game3 = Game(user_id=1, name="World of Warcraft")

session.add(game3)
session.commit()


gameItem1 = GameItem(user_id=1, name="Big Love Rocket", description="Mount- Apotehcary Hummel painted this masterpiece bright pink for an unrequited love",
                     price="2000 gold", game=game3)

session.add(gameItem1)
session.commit()

gameItem2 = GameItem(user_id=1, name="Reins of Poseidus", description="Mount- One has not truly lived until they have felt the tidal current rushing through their hair while atop a majestic seahorse, said no one. Ever.",
                     price="15,000 gold", game=game3)

session.add(gameItem2)
session.commit()


print "added game items!"
