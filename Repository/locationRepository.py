from Models.locationModel import LocationModel
from Simulation.location import Location
from py_linq import *

class LocationRepository:
    @staticmethod
    def Create(location, scenarioId, parentLocationId=None):
        model = LocationModel()
        model.Set(location, scenarioId, parentLocationId)
        LocationModel.objects.insert(model)
        
        #update the object with the id so we can update it later
        location._id = model.id

    @staticmethod
    def CreateOrUpdate(location, scenarioId, parentLocationId=None):
        if not hasattr(location, "_id"):
            LocationRepository.Create(location, scenarioId, parentLocationId)
        else:
            model = LocationModel()
            model.Set(location, scenarioId, parentLocationId)
            model.save()
        
    @staticmethod
    def Get(locationId):
        model = LocationModel.objects.get(id=locationId)
        return model.Hydrate()

    @staticmethod
    def GetLocations(scenarioId, parentLocationId=None):
        models = LocationModel.objects(scenarioId=scenarioId, parentLocationId=parentLocationId)

        #convert to enumerable list of models
        modelCollection = Enumerable(models)

        #convert each model to the simulation object
        return modelCollection.select(lambda x: x.Hydrate())
    
    @staticmethod
    def FetchScenario(scenarioId, parentLocationId=None):
        #get the locations at this level
        locations = LocationRepository.GetLocations(scenarioId, parentLocationId)

        #get the child locations
        for location in locations:
            location.locations = LocationRepository.FetchScenario(scenarioId, location._id)

        #return the locations at this level
        return locations
    
    def CreateOrUpdateLocations(location, scenarioId, parentLocationId=None):
        LocationRepository.CreateOrUpdate(location, scenarioId, parentLocationId)
        if location.locations is not None:
            for childLocation in location.locations:
                LocationRepository.CreateOrUpdateLocations(childLocation, scenarioId, location._id)