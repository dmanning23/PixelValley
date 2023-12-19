from keys import mongoUri
import pymongo
from Memory.goal import Goal
from py_linq import *

class GoalsRepository:

    DB_NAME = "pixelValley"
    COLLECTION_NAME = "goalsStream"

    def __init__(self, client = None):
        #set up the pymongo connection
        if client is None:
            client = pymongo.MongoClient(mongoUri) #connect for pymongo
        db = client.pixelValley
        self.collection = db[GoalsRepository.COLLECTION_NAME]

    def CreateGoal(self, goal):
        self.collection.insert_one(goal.__dict__)

    #create or update a goal

    def CreateOrUpdateGoal(self, goal):
        if hasattr(goal, "_id"):
            #update the goal!
            pass
        else:
            self.CreateGoal(goal)

    #TODO: update a goal? What fields in a goal would ever need to be updated?

    #TODO: need the ability to set goals to completed

    #get all the goals for the agent
    def GetGoals(self, agent):
        result = self.collection.find({"agentId": agent._id})

        #parse into Goal objects
        memories = Enumerable(result).select(lambda x: Goal(**x))
        return memories.to_list()
