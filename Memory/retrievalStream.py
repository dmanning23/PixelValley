from Memory.memoryRepository import MemoryRepository
from py_linq import * 

class RetrievalStream():

    def __init__(self, memoryRepository):
        self.memoryRepository = memoryRepository

    async def RetrieveMemories(self, agent, query, numMemories=30):
        #TODO: calculate embedding vector relevance for recent and important memories?
        #Get the most recent memories
        #recent = self.memoryRepository.GetRecentMemories(agent, 30)

        #Get the most important memories
        #important = self.memoryRepository.GetImportantMemories(agent, 30)

        #Get the most relevent memories
        relevant = await self.memoryRepository.GetRelevantMemories(agent, numMemories * 4, query)

        #TODO: append timestamp to beginning of each memory
        #sort by score and return the top 10 memories
        #memories = Enumerable(recent + important + relevant)
        memories = Enumerable(relevant)
        bestMemories = memories.distinct(lambda x: x._id).order_by_descending(lambda x: x.score(agent.currentTime)).take(numMemories)
        return bestMemories.to_list()