from mongoengine import *
from Simulation.location import Location

class LocationModel(Document):
    scenarioId = ObjectIdField()
    parentLocationId = ObjectIdField()
    canSubdivide = BooleanField()
    name = StringField()
    description = StringField()

    def Set(self, location, scenarioId, parentLocationId=None):
        if hasattr(location, "_id"):
            self.id=location._id
        self.scenarioId = scenarioId
        self.parentLocationId = parentLocationId
        self.name = location.name
        self.description = location.description
        self.canSubdivide = location.canSubdivide 

    def Hydrate(self):
        return Location(self.name,
                        self.description,
                        canSubdivide=self.canSubdivide,
                        _id = self.id)
