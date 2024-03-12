from Memory.plannedActivity import PlannedActivity
import json
from openai import AsyncOpenAI

class PlannedActivityGenerator():

    createPlansFunctionDef = {
        'name': 'create_planned_activities',
        'description': 'Create a list of planned activities for a character',
        'parameters': {
            "type": "object",
            "properties": {
                "plannedActivities": {
                    'type': 'array',
                    "description": "A list of activities for the character to complete",
                    "items": {
                        "type": "object",
                        "description": "A single planned activity",
                        'properties': {
                            'description': {
                                'type': 'string',
                                'description': 'A description of the activity'
                            },
                            'starttime': {
                                'type': 'string',
                                'description': "The time to start the activity"
                            },
                            'timeframe': {
                                'type': 'string',
                                'description': "The time frame of the activity"
                            },
                        },
                        "required": ["description", "starttime", "timeframe" ]
                    },
                },
            },
            "required": ["plans"]
        }
    }

    def __init__(self):
        pass

    def _create_planned_activities(self, agent, activities):
        response = []
        for activity in activities:
            response.append(self._create_activity(agent, **activity))
        return response

    def _create_activity(self, agent, description, starttime, timeframe):
        activity = PlannedActivity()
        activity.Set(agentId=agent._id,
                     description=description,
                     starttime=starttime,
                     timeframe=timeframe)
        return activity

    def _parseResponse(self, agent, response_message):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            available_functions = {
                "create_planned_activities": self._create_planned_activities,
            }
            function_to_call = available_functions[function_called]

            return function_to_call(agent, *list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None

    async def GenerateDailyPlans(self, agent, goals, importantMemories, llm = None):
        if not llm:
            llm = AsyncOpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following description of a character, their short and long term goals, and a list of important things to remember for today, create a daily plan of activities for the entire day."},
            {'role': 'user', 'content': f"{agent}"}
        ]

        #Add the agents goals to their plans
        for goal in goals:
            messages.append({'role': 'user', 'content': f"Goal: {goal}"})

        #Make sure the agent takes into account any important things to remember for today
        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"Important thing to remember for today: {memory}"})

        #Create the list of function definitions that are available to the LLM
        functions = [ PlannedActivityGenerator.createPlansFunctionDef ]

        #Call the LLM...
        response = await llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        plannedActivities = self._parseResponse(agent, response.choices[0].message)
        if plannedActivities is None:
            plannedActivities = []
        return plannedActivities
    
    async def BreakDownPlannedActivity(self, agent, plannedActivity, llm = None):
        if not llm:
            llm = AsyncOpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following itinerary item, break it down into a list of finer-grained actions of 15-30 minute chunks."},
            {'role': 'user', 'content': f"{plannedActivity}"}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ PlannedActivityGenerator.createPlansFunctionDef ]

        #Call the LLM...
        response = await llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        plannedActivities = self._parseResponse(agent, response.choices[0].message)
        if plannedActivities is None:
            plannedActivities = []
        return plannedActivities