from mongoengine import *
from Simulation.scenario import Scenario

"""
This is the main scenario object that is stored in MongoDB
"""
class ScenarioModel(Document):
    name = StringField()
    description = StringField()
    currentDateTime = DateTimeField()
    seed = StringField()
    imageFilename = StringField()

    def Set(self, scenario):
        if hasattr(scenario, "_id"):
            self.id=scenario._id
        self.name = scenario.name
        self.description = scenario.description
        self.currentDateTime = scenario.currentDateTime 
        self.seed = scenario.seed
        self.imageFilename = scenario.imageFilename

    def Hydrate(self):
        return Scenario(self.name,
                        self.description,
                        _id = self.id,
                        currentDateTime = self.currentDateTime,
                        seed = self.seed,
                        imageFilename = self.imageFilename)