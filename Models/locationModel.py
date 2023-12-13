from mongoengine import *
from Simulation.location import Location

class LocationModel(Document):
    scenarioId = ObjectIdField()
    parentLocationId = ObjectIdField()
    name = StringField()
    description = StringField()

    def Set(self, location, scenarioId, parentLocationId=None):
        if hasattr(location, "_id"):
            self.id=location._id
        self.scenarioId = scenarioId
        self.parentLocationId = parentLocationId
        self.name = location.name
        self.description = location.description

    def Hydrate(self):
        return Location(self.name,
                        self.description,
                        _id = self.id)
