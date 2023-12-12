from mongoengine import *
from Models.scenarioModel import ScenarioModel
from Models.userAccessModel import UserAccessModel
from Simulation.scenario import Scenario
from Repository.userAccessRepository import UserAccessRepository
from py_linq import *

class ScenarioRepository():

    """
    Given a scenario, store it in the database
    """
    @staticmethod
    def Create(userId, scenario):
        #create the model object
        model = ScenarioModel(name=scenario.name, description=scenario.description)

        #store the model in the database
        ScenarioModel.objects.insert(model)

        #update the object with the id so we can update it later
        scenario._id = model.id

        #give the user access to the scenario
        UserAccessRepository.GiveAccess(userId, scenario._id)

    """
    Given a scenario, update it in the database.
    """
    @staticmethod
    def CreateOrUpdate(userId, scenario):
        #check if the scenario has already been saved
        if not hasattr(scenario, "_id"):
            ScenarioRepository.Create(userId, scenario)
        elif UserAccessRepository.HasAccess(userId, scenario._id):
            #check if the user has access
            model = ScenarioModel(id=scenario._id, name=scenario.name, description=scenario.description)
            #TODO: get all the location IDs
            model.save()
        else:
            #TODO: throw an error
            pass

    """
    """
    @staticmethod
    def Get(userId, scenarioId):
        if UserAccessRepository.HasAccess(userId, scenarioId):
            model = ScenarioModel.objects.get(id=scenarioId)
            scenario = Scenario(model.name, model.description, _id = model.id)
            #TODO: get all the locations and add to the scenario
            return scenario

    """
    Given a user id, get a list of scenarios that user has access to
    """
    @staticmethod
    def GetScenarios(userId):
        try:
            #get the scenarios for the user
            models = UserAccessModel.objects(userId=userId)

            #get the scenarios that match
            scenarioModels = []
            for model in models:
                scenarioModels.append(ScenarioModel.objects.get(id=model.scenarioId))

            #convert to enumerable list of models
            modelCollection = Enumerable(scenarioModels)

            #convert each model to the simulation object
            return modelCollection.select(lambda x: Scenario(x.name, x.description, _id = x.id))
        except InvalidQueryError as e:
            return []