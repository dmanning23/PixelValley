from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
from Simulation.scenario import Scenario
from Generators.locationGenerator import LocationGenerator
import json
from openai import OpenAI

class ScenarioGenerator:

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
                    'description': 'An appropriate name for the location, based on the description'
                },
                'time': {
                    'type': 'integer',
                    'description': "A year to be used as the start date of this scenario. It should be appropriate to the time period of the scenario."
                },
            },
            "required": ["description", "name", "time"]
        }
    }

    def _generate_scenario(self, seed, description, name, time=None):
        return Scenario(name=name, description=description, currentDateTime=time, seed=seed)

    def _parseResponse(self, seed, response_message):
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
            return function_to_call(seed, *list(function_args.values()))
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
        item = self._parseResponse(shortDescription, response.choices[0].message)
        if item is None:
            return Scenario(shortDescription)
        else:
            return item