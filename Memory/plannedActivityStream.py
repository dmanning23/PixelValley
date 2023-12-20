from datetime import datetime
from Memory.plannedActivity import PlannedActivity

class PlannedActivityStream:

    def __init__(self, memoryRepository, plannedActivityGenerator, goalRepository, retrieval):
        self.memoryRepository = memoryRepository
        self.plannedActivityGenerator = plannedActivityGenerator
        self.goalRepository = goalRepository
        self.retrieval = retrieval

    def CreatePlannedActivities(self, agent, scenario):
        goals = self.goalRepository.GetGoals(agent)
        memories = self.retrieval.RetrieveMemories(agent, f"What are important things for {agent.name} to remember while making a list of planned activites for today?")
        plans = self.plannedActivityGenerator.GenerateDailyPlans(agent, goals, memories)

        for plan in plans:
            #Store this planned item
            self._planStorage(plan, agent, scenario)

            #Break down planned activities into smllaer chunks
            subPlans = self.plannedActivityGenerator.BreakDownPlannedActivity(agent, plan)
            for subPlan in subPlans:
                self._planStorage(subPlan, agent, scenario)

    def _planStorage(self, activity, agent, scenario):
        #set date of all the plans
        activity.date = scenario.currentDateTime.date()

        #tore plans
        PlannedActivity.objects.insert(activity)
        
        #create planned activity memories
        self.memoryRepository.CreateMemory(agent, f'On {activity.date.strftime("%d %B, %Y")}, I plan to {activity.description} at {activity.starttime} for {activity.timeframe}')
