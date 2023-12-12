from mongoengine import *

class UserAccessModel(Document):
    userId = IntField() #TODO: this needs to be changed to ObjectIDField when users are properly stored in MongoDB
    scenarioId = ObjectIdField()