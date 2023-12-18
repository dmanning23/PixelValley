from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
from Simulation.scenario import Scenario
from Generators.locationGenerator import LocationGenerator
import json
from openai import OpenAI

class ScenarioGenerator:

    def GenerateLocations(self, scenario, llm= None):
        locationGen = LocationGenerator()
        self.locations = locationGen.Generate(scenario.name, llm)

    generateScenarioFunctionDef = {
        'name': 'generate_scenario',
        'description': 'Create a scenario',
        'parameters': {
            "type": "object",
            "properties": {
                'description': {
                    'type': 'string',
                    'description': "An expanded description of the scenario",
                },
                'name': {
                    'type': 'string',
                    'description': 'A name for the location, based on the description'
                },
                'time': {
                    'type': 'string',
                    'description': "The start date of the scenario in ISO format"
                },
            },
            "required": ["title", "time", "description"]
        }
    }

    def _generate_scenario(self, description, name, time):
        return Scenario(name=name, description=description, currentDateTime=time)

    def _parseResponse(self, response_message):
        if response_message.function_call and response_message.function_call.arguments:
            #Which function call was invoked?
            function_called = response_message.function_call.name
            
            #Extract the arguments from the AI payload
            function_args  = json.loads(response_message.function_call.arguments)
            
            #Create a list of all the available functions
            available_functions = {
                "generate_scenario": self._generate_scenario,
            }
            
            function_to_call = available_functions[function_called]

            #Call the function with the provided arguments
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None
    
    def GenerateScenario(self, shortDescription, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': "Expand the following description of a scenario."},
            {'role': 'user', 'content': shortDescription}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ ScenarioGenerator.generateScenarioFunctionDef ]

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        items = self._parseResponse(response.choices[0].message)
        if items is None:
            return [] #if it gets here, there was a problem with the description
        else:
            return items