import json
from Simulation.location import Location
from openai import OpenAI
from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
from Generators.itemGenerator import ItemGenerator

class LocationGenerator():

    generateLocationsFunctionDef = {
            'name': 'generate_locations',
            'description': 'Create a list of locations',
            'parameters': {
                "type": "object",
                "properties": {
                    "locations": {
                        'type': 'array',
                        "description": "A list of locations",
                        "items": {
                            "type": "object",
                            "description": "A single location",
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Name of the location'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': "A description of the location."
                                },
                                "canBeSubdivided" :{
                                    "type": "boolean",
                                    "description": "True if the description describes a location that can be subdivided, False otherwise"
                                }
                            },
                            "required": ["name", "description"]
                        },
                    },
                },
                "required": ["locations",]
            }
    }
    
    canSubdivideFunctionDef = {
            'name': 'can_subdivide',
            'description': 'Given the description of a location, determine whether it can be further subdivided',
            'parameters': {
                "type": "object",
                "properties": {
                    "canBeSubdivided" :{
                        "type": "boolean",
                        "description": "True if the description describes a location that can be subdivided, otherwise false"
                    }
                },
                "required": ["canBeSubdivided",]
            }
        }

    def _generate_locations(self, locations):
        response = []
        for location in locations:
            response.append(self._generate_location(**location))
        return response

    def _generate_location(self, name, description, canBeSubdivided = False):
        return Location(name, description, canSubdivide=canBeSubdivided)
    
    def _can_subdivide(self, canSubdivide):
        return canSubdivide

    def _parseResponse(self, response_message):
        if response_message.function_call and response_message.function_call.arguments:
            #Which function call was invoked?
            function_called = response_message.function_call.name
            
            #Extract the arguments from the AI payload
            try:
                function_args  = json.loads(response_message.function_call.arguments)
            except:
                #TODO: some sort of json error occurred
                return None
            
            #Create a list of all the available functions
            available_functions = {
                "generate_locations": self._generate_locations,
                "can_subdivide": self._can_subdivide,
                #TODO add more functions here?
            }
            
            fuction_to_call = available_functions[function_called]

            #Call the function with the provided arguments
            return fuction_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None

    def Generate(self, scenario, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following scenario, generate a list of physical locations"},
            {'role': 'user', 'content': scenario.name}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ LocationGenerator.generateLocationsFunctionDef ]

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.2, #Use a really high temp so the LLM can get creative
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        locations = self._parseResponse(response.choices[0].message)
        if locations is None:
            return [] #if it gets here, there was a problem with the description
        else:
            return locations
    
    def CanSubdivide(self, location, llm):

        #Create our list of messages for creating locations
        messages = [
            {'role': 'system', 'content': "Based on the following description of a location, can the location be further decomposed into a list of sub-locations?"},
            {'role': 'user', 'content': location.describe()}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ LocationGenerator.canSubdivideFunctionDef ]

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        canSubdivide = self._parseResponse(response.choices[0].message)
        if canSubdivide is None:
            return False #don't recurse if the LLM returns text
        else:
            return canSubdivide

    def _generateChildLocations(self, location, llm):
        
        #Create our list of messages for creating locations
        messages = [
            {'role': 'system', 'content': """Based on the following description of a location, decompose it into a list of sub-locations.
             Do not return any areas that match the same name and description that was provided."""},
            {'role': 'user', 'content': location.name}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ LocationGenerator.generateLocationsFunctionDef ]

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1, #Use a really low temp so the LLM doesn't go crazy
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto',)
        locations = self._parseResponse(response.choices[0].message)
        if locations is None:
            return [] #return an empty list if the LLM didn't call a function (returned a text message)
        else:
            return locations

    def GenerateChildLocations(self, location, level = 0, maxLevel = 2, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        #stop recursing at some point
        if level >= maxLevel:
            return

        #is the location a single discrete location?
        if location.canSubdivide:

            #increment the level
            level = level + 1

            #Generate the child locations from the LLM
            location.locations = []
            childLocations = self._generateChildLocations(location, llm)
            for child in childLocations:
                if location.name != child.name: #The OpenAI api has a tendency to return the same thing we just fed it :/
                    location.locations.append(child)
                    #Recurse into child locations
                    self.GenerateChildLocations(location=child, level=level, maxLevel=maxLevel, llm=llm)

    def GenerateItems(self, location, llm = None):
        itemGen = ItemGenerator()
        location.items = itemGen.GenerateItems(location, llm)