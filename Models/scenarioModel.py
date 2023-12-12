from mongoengine import *

"""
This is the main scenario object that is stored in MongoDB
"""
class ScenarioModel(Document):
    name = StringField()
    description = StringField()
