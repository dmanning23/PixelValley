from datetime import datetime
from Memory.plannedActivity import PlannedActivity

class PlannedActivityStream:

    def __init__(self, memoryRepository, plannedActivityGenerator, goalRepository, retrieval):
        self.memoryRepository = memoryRepository
        self.plannedActivityGenerator = plannedActivityGenerator
        self.goalRepository = goalRepository
        self.retrieval = retrieval

    async def CreatePlannedActivities(self, agent, scenario):
        goals = self.goalRepository.GetGoals(agent)
        memories = await self.retrieval.RetrieveMemories(agent, f"What are important things to remember while planning my schedule for today?")
        plans = await self.plannedActivityGenerator.GenerateDailyPlans(agent, goals, memories)

        for plan in plans:
            #Store this planned item
            self._planStorage(plan, agent, scenario)

            #Break down planned activities into smllaer chunks
            subPlans = self.plannedActivityGenerator.BreakDownPlannedActivity(agent, plan)
            for subPlan in subPlans:
                #Increase the priority of sub plans
                subPlan.priority = subPlan.priority + 1
                self._planStorage(subPlan, agent, scenario)

    def _planStorage(self, activity, agent, scenario):
        #set date of all the plans
        activity.date = scenario.currentDateTime.date()

        #try to set the datetime objects of the activity
        activity.SetDateTimes(scenario)

        #tore plans
        PlannedActivity.objects.insert(activity)
        
        #TODO: does this need to be remembered?
        #create planned activity memories
        #self.memoryRepository.CreateMemory(agent, f'On {activity.date.strftime("%d %B, %Y")}, I plan to {activity.description} at {activity.starttime} for {activity.timeframe}')

    def GetCurrentPlannedActivity(self, agent, currentTime):
        #Get all the planned activities, sorted by priority:
        activities = PlannedActivity.objects(agentId = agent._id, day = currentTime.date()).order_by("-priority", "+startdatetime")
        for activity in activities:
            if activity.startdatetime <= currentTime <= activity.enddatetime:
                return activity
        
        #This character is not busy right now!
        result = PlannedActivity()
        result.description = "Idle"
        return result