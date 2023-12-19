
#This object represents a long or short goal for a character
class Goal():

    def __init__(self, agentId = None, title=None, timeframe=None, description = None, _id = None):

        if _id is not None:
            self._id = _id

        #The agent that has this goal
        self.agentId = agentId
        
        self.title = title
        self.timeframe = timeframe
        self.description = description

    def __str__(self) -> str:
        return f"{self.title}\nTimeframe: {self.timeframe}\n{self.description}"