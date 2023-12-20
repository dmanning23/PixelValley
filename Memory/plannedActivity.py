from mongoengine import *
class PlannedActivity(Document):

    agentId = ObjectIdField()
    date = DateField()
    description = StringField()
    starttime = StringField()
    timeframe = StringField()

    def Set(self, agentId=None, description=None, starttime=None, timeframe=None):
        self.agentId = agentId
        self.description = description
        self.starttime = starttime
        self.timeframe = timeframe

    def __str__(self) -> str:
        return f"{self.description} at {self.starttime} for {self.timeframe}"