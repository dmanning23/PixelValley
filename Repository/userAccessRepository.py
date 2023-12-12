from mongoengine import *
from Models.userAccessModel import UserAccessModel

class UserAccessRepository:
    
    #Give a user access to a scenario
    #TODO: this currently doesn't support sharing between multiple users
    @staticmethod
    def GiveAccess(userId, scenarioId):
        #create the user object
        access = UserAccessModel(userId=userId, scenarioId=scenarioId)
        
        #store the user object
        UserAccessModel.objects.insert(access)

    #Check if a user has access to a scenario
    @staticmethod
    def HasAccess(userId, scenarioId):
        access =  UserAccessModel.objects(userId=userId, scenarioId=scenarioId)
        return access is not None