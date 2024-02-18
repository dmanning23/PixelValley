import json
from Simulation.location import Location
from openai import OpenAI
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
                            "isBuilding" :{
                                "type": "boolean",
                                "description": "Whether or not if this location is a building"
                            }
                        },
                        "required": ["name", "description"]
                    },
                },
            },
            "required": ["locations",]
        }
    }

    def _generate_locations(self, locations):
        response = []
        for location in locations:
            response.append(self._generate_location(**location))
        return response

    def _generate_location(self, name, description, isBuilding = False):
        return Location(name, description, canSubdivide=isBuilding)

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
            }
            
            function_to_call = available_functions[function_called]

            #Call the function with the provided arguments
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None

    def Generate(self, scenario, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following scenario, generate a list of 6 or more buildings"},
            {'role': 'user', 'content': f"{scenario.name} in the year {scenario.currentDateTime.year}: {scenario.seed}"}
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

    def _generateChildLocations(self, location, llm):
        
        #Create our list of messages for creating locations
        messages = [
            {'role': 'system', 'content': """Based on the following description of a building, create a list of rooms that would be found inside.
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