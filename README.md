# FSND Catalog App Project

## Project Description
 this project will implement electronics items catalog application by utilizing the technologies of 
SQLAlchemy, Flask Framework, OAuth 2.0 Protocol, APIs.

## Project_Specification
the main page of the application can be accessed by opening the URI http://localhost:800 
the main page will contain two lists to  show all categories with recently added items  (main page)
- Clickable categories are listed in the navigation bar,
whenever a category is clicked showCategoryItems  function will be executed to view all items in that category
- Clickable list of recent items (last added items) are shown along with the category name
they belong to, whenever an item is clicked, Browse Item function will be executed
- JSON API is used to provide JSON format for items and thier categories and for a speciefic item

## Project_security
the pages are secured with google OAuth 2.0 API , so in order to be able to add ,delete ,update categories or items
of you own you should login to the app with your google account . 



## Requirements
Python 2.7.12
sqlalchemy
flask
json


## Software	Installation 
* in order to run this projects you need to download the and install the fowlling 	
a. Vagrant:	https://www.vagrantup.com/downloads.html ( which is a program used to customize and 	run pr-econfigured virtual machines)
b. Virtual Machine:	https://www.virtualbox.org/wiki/Downloads
c. Download	a	FSND	virtual	machine:	https://github.com/udacity/fullstack-nanodegree-vm
d. unzip the files and open the vm folder using git-bash terminal 
e. run the follwing to get the vm running and up so you can load the db to it and run the program
```
cd vagrant
vagrant up
vagrant ssh
cd /vagrant
mkdir catalog
cd catalog
```
Note:	Files in the VM's /vagrant directory are shared	with the vagrant folder	on your	
computer. But other data inside the VM is not.
f. download all files form this repository inside catalog folder
g. creat the database by runing the command python database_setup.py 
h. you can use the seeder.py file to load some test data to the database

## How to run

* create  database with script
```
python database_setup.py
```
* load the initial data onto the database
```
python seeder.py
```
* run the python file 
```
python application.py
```