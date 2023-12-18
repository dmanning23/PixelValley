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
        model = ScenarioModel()
        model.Set(scenario)

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
            model = ScenarioModel()
            model.Set(scenario)

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
            scenario = model.Hydrate()
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
            return modelCollection.select(lambda x: x.Hydrate()).to_list()
        except InvalidQueryError as e:
            return []