from Memory.memory import Memory
from langchain.embeddings.openai import OpenAIEmbeddings
from keys import mongoUri
import pymongo
from langchain.vectorstores import MongoDBAtlasVectorSearch
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import re
import numpy as np

DB_NAME = "pixelValley"
COLLECTION_NAME = "memoryStream"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"

class MemoryRepository:

    def __init__(self, client = None, embeddings = None, llm=None):
        #set up the pymongo connection
        if client is None:
            client = pymongo.MongoClient(mongoUri) #connect for pymongo
        db = client.pixelValley
        self.collection = db["memoryStream"]

        #setup the OpenAI connection for creating embeddings
        if embeddings is None:
            embeddings = OpenAIEmbeddings()
        self.embeddings = embeddings

        #setup the connection for doing vector search on the embeddings
        vectorIndex = MongoDBAtlasVectorSearch.from_connection_string(
            mongoUri,
            DB_NAME + "." + COLLECTION_NAME,
            OpenAIEmbeddings(disallowed_special=()),
            index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME)
        
        #setup the llm for retriecing memory importance
        if llm is None:
            llm = ChatOpenAI()
        self.llm = llm

        #setup the prompt for memory importance
        prompt = ChatPromptTemplate.from_template("You are: {agent}\n On a scale of 1.0 to 10.0, where 1 is pureliy mundane(e.g. brushing teeth, making bed) and 10 is extremely poignant (e.g. a breakup, college acceptance), rate the likely poignancy of the following peice of memory.\nMemory: {memory}\nRating: <fill in>")
        self.chain = prompt | self.llm

    def CreateMemory(self, agent, description):
        #Check if that memory already exists
        result = self.collection.find_one({"agentId": agent._id, "description": description})
        if result is None:
            memory = Memory(agentId = agent._id,
                            description = description,
                            time = agent.currentTime)
            #set the importance of the memory
            memory.importance = self.GetMemoryImportance(agent, memory)

            #set the embedding for the memory
            memory.embedding = self.GetMemoryEmbedding(memory)

            #Save the memory
            self.collection.insert_one(memory.__dict__)
        else:
            memory = Memory(**result)
            #update the time
            memory.time = agent.currentTime
            self.collection.update_one({"_id": memory._id}, {"$set": {"time": memory.time}})

    def GetMemoryImportance(self, agent, memory):
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

    def GetMemoryEmbedding(self, memory):
        return self.embeddings.embed_query(memory.description)
