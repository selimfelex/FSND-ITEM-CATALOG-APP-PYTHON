from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Item, Base, Category, User

engine = create_engine('sqlite:///itemcatalog.db')
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
User1 = User(name="Selim Felex", email="selim.felex@gmail.com",
             picture='')
session.add(User1)
session.commit()

# Menu for UrbanBurger
category1 = Category(user_id=1, name="Networks")

session.add(category1)
session.commit()

category2 = Category(user_id=1, name="Laptops")

session.add(category2)
session.commit()

category3 = Category(user_id=1, name="Computers")

session.add(category3)
session.commit()

catITem1 = Item(user_id=1, name="CYBEROAM CR35ING", description="Next-Generation network security appliances that include UTM security features and performance required for future networks",
                     price="$500.99", category_id = "1")

session.add(catITem1)
session.commit()

catITem2 = Item(user_id=1, name="ASUS FX504GD-DM364T", description="TUF GAMING LAPTOP - INTEL CORE I7-8750H, 15.6-INCH FHD, 1TB + 128GB SSD, 16GB",
                     price="$300.99", category_id = "2")
session.add(catITem2)
session.commit()

catITem3 = Item(user_id=1, name="ASUS GAMING 2TB M.2", description="Windows 10 Pro CPU: Intel Core i5 8600 MEMORY: DDR4 2400MHz 8GB MOTHERBOARD: ASUS PRIME Z370-A",
                     price="$566.99", category_id = "3")

session.add(catITem3)
session.commit()



print "added menu items!"