import re
import numpy as np
from py_linq import *
from keys import mongoUri
import pymongo

from langchain.vectorstores import MongoDBAtlasVectorSearch
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings

from Memory.memory import Memory

class MemoryRepository:

    DB_NAME = "pixelValley"
    COLLECTION_NAME = "memoryStream"
    ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"

    def __init__(self, client = None, embeddings = None, llm=None):
        #set up the pymongo connection
        if client is None:
            client = pymongo.MongoClient(mongoUri) #connect for pymongo
        db = client.pixelValley
        self.collection = db[MemoryRepository.COLLECTION_NAME]

        #setup the OpenAI connection for creating embeddings
        if embeddings is None:
            embeddings = OpenAIEmbeddings()
        self.embeddings = embeddings

        #setup the connection for doing vector search on the embeddings
        self.vectorIndex = MongoDBAtlasVectorSearch.from_connection_string(
            mongoUri,
            MemoryRepository.DB_NAME + "." + MemoryRepository.COLLECTION_NAME,
            OpenAIEmbeddings(disallowed_special=()),
            index_name=MemoryRepository.ATLAS_VECTOR_SEARCH_INDEX_NAME)
        
        #setup the llm for retriecing memory importance
        if llm is None:
            llm = ChatOpenAI()
        self.llm = llm

        #setup the prompt for memory importance
        prompt = ChatPromptTemplate.from_template("You are: {agent}\n On a scale of 1.0 to 10.0, where 1 is pureliy mundane(e.g. brushing teeth, making bed) and 10 is a life-altering core memory (e.g. a breakup, college acceptance), rate the likely poignancy of the following peice of memory.\nMemory: {memory}\nRating: <fill in>")
        self.chain = prompt | self.llm

    def CreateMemory(self, agent, description):
        #Check if that memory already exists
        result = self.collection.find_one({"agentId": agent._id, "description": description})
        if result is None:
            memory = Memory(agentId = agent._id,
                            description = description,
                            time = agent.currentTime)
            #set the importance of the memory
            memory.importance = self._getMemoryImportance(agent, memory)

            #set the embedding for the memory
            memory.embedding = self._getMemoryEmbedding(memory)

            #Save the memory
            self.collection.insert_one(memory.__dict__)
        else:
            memory = Memory(**result)
            #update the time
            self.UpdateMemoryTime(agent, memory)

    #update the time of a single memory
    def UpdateMemoryTime(self, agent, memory):
        memory.time = agent.currentTime
        self.collection.update_one({"_id": memory._id}, {"$set": {"time": memory.time}})

    def _getMemoryImportance(self, agent, memory):
        try:
            #ask the LLM how important it thinks this memory is
            response = self.chain.invoke({"agent": agent, "memory": memory.description})

            numbers = re.findall( r'\d+\.*\d*', response.content)
            if len(numbers) > 0:
                #don't forget to normalize this data
                return np.clip(float(numbers[0]) / 10.0, 0.0, 1.0)
            else:
                #the llm screwed up somehow
                return 0.1
        except:
            #llm problems, floating point conversion problems, etc?
            return 0.1

    def _getMemoryEmbedding(self, memory):
        return self.embeddings.embed_query(memory.description)
    
    def GetRecentMemories(self, agent, numMemories):
        #get the most recent X number of memories for an agent
        result = self.collection.find({"agentId": agent._id}).sort("time", -1).limit(numMemories)

        #parse into Memory objects
        memories = Enumerable(result).select(lambda x: Memory(**x))
        return memories.to_list()

    def GetImportantMemories(self, agent, numMemories):
        #get the most important X number of memories for an agent
        result = self.collection.find({"agentId": agent._id}).sort("importance", -1).limit(numMemories)
        memories = Enumerable(result).select(lambda x: Memory(**x))
        return memories.to_list()

    def GetRelevantMemories(self, agent, numMemories, query):
        #Get the embedding vector of the query
        queryEmbedding = self.embeddings.embed_query(query)

        #yall ready for this? Fire up the mongoDB aggregate pipeline to search the memoryStream database
        agg = [ 
            {
                #Get the most relevant memories based on the query embedding
                '$vectorSearch':
                {
                    'index': 'vector_index',
                    'path': 'embedding',
                    'queryVector': queryEmbedding,
                    'numCandidates': 150,
                    'limit': numMemories
                }
            },
            {
                #Only get memories for this agent!!!
                '$match':
                {
                    'agentId': agent._id
                }
            },
            {
                #Return the whole memory and add the relevance
                '$project':
                {
                    '_id': 1, 
                    'agentId': 1,
                    'description': 1,
                    'time': 1, 
                    'importance': 1, 
                    'embedding': 1,
                    'relevance': { '$meta': 'vectorSearchScore' }
                }
            }
        ]

        documents = self.collection.aggregate(pipeline=agg)

        #given a query, get the most relevant X number of memores for an agent
        #documents = self.vectorIndex.similarity_search_with_score(query=query, k=numMemories)
        memories = []
        for document in documents:
            #convert to a memory object
            memory = Memory(**document)
            #set the relevence
            memories.append(memory)
        return memories
    
    #Save an agents goals to the memory stream
    def CreateGoalMemories(self, agent, goals):
       
        for goal in goals:
            self.CreateGoalMemory(agent, goal)

    def CreateGoalMemory(self, agent, goal):
        self.CreateMemory(agent, f"{goal}")