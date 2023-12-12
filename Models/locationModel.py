from mongoengine import *

class LocationModel(Document):
    scenarioId = ObjectIdField()
    parentLocationId = ObjectIdField()
    name = StringField()
    description = StringField()
