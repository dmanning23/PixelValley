from mongoengine import *
from parsedatetime import *
import datetime as dt
import pytimeparse

class PlannedActivity(Document):

    agentId = ObjectIdField()
    day = DateField()
    startdatetime = DateTimeField()
    enddatetime = DateTimeField()
    description = StringField()
    starttime = StringField()
    timeframe = StringField()
    priority = IntField()

    def Set(self, agentId=None, description=None, starttime=None, timeframe=None, priority=0):
        self.agentId = agentId
        self.description = description
        self.starttime = starttime
        self.timeframe = timeframe
        self.priority = priority

    def SetDateTimes(self, scenario):
        
        #grab the date
        self.day = scenario.currentDateTime.date()

        #set the start time
        #parse the starttime created from the llm
        cal = Calendar()
        parsedStart, parse_status = cal.parse(self.starttime) 
        self.startdatetime = scenario.currentDateTime.replace(hour=parsedStart.tm_hour,
                                                              minute=parsedStart.tm_min,
                                                              second=parsedStart.tm_sec,
                                                              microsecond=0)

        #parse the time delta from the LLM
        parsedTimeDelta = pytimeparse.parse(self.timeframe)
        myDelta = dt.timedelta(seconds=parsedTimeDelta)

        #set the endtime
        self.enddatetime = self.startdatetime + myDelta

    def __str__(self) -> str:
        return f"{self.description} at {self.starttime} for {self.timeframe}"