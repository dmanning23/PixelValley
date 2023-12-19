
#This object represents a single memory for an agent.
class Memory():

    _timeWeight = 3.0
    _timeDecay = 0.005

    def __init__(self, _id = None, agentId = None, description = None, time = 0, importance = 0.0, embedding=0.0, relevance=None):

        if _id is not None:
            self._id = _id

        #The agent that had this memory
        self.agentId = agentId
        
        #the text of the memory
        self.description = description
        #The agent's time that the memory was recorded
        self.time = time
        #How important the agent finds this memory. Must be between 0.0 - 1.0
        self.importance = importance

        #The vector embedding of this memory. Must be between 0.0 - 1.0
        self.embedding = embedding

        if relevance is not None:
            self.relevance = relevance

    def score(self, currentTime):
        #normalize the time
        timeScore = (self._timeWeight - ((currentTime - self.time) * self._timeDecay)) / self._timeWeight

        #Add the time, importance, and relevance to get the final score
        return timeScore + self.importance + self.relevance
