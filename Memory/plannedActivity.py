
class PlannedActivity():

    def __init__(self, agentId, description, starttime, timeframe, _id = None):

        if _id is not None:
            self._id = _id

        #The agent that has this goal
        self.agentId = agentId
        
        self.description = description
        self.starttime = starttime
        self.timeframe = timeframe

    def __str__(self) -> str:
        return f"{self.starttime}\n{self.description}\n{self.timeframe}"
        