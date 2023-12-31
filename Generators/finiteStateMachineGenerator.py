import json
from openai import OpenAI
from Simulation.finiteStateMachine import FiniteStateMachine

class FiniteStateMachineGenerator():

    generateFiniteStateMachineFunctionDef = {
        'name': 'generate_finite_state_machine',
        'description': 'Create a finite state machine for an object',
        'parameters': {
            "type": "object",
            "properties": {
                "states": {
                    'type': 'array',
                    "description": "A list of states that the object can be in",
                    "items": {
                        'type': 'string',
                        'description': 'Name of the state'
                    },
                },
                "initialState": {
                    'type': 'string',
                    'description': 'The initial state of the finite state machine. This must come from the list of states'
                },
                "actions": {
                    'type': 'array',
                    "description": "A list of actions that can be performed on the object",
                    "items": {
                        'type': 'string',
                        'description': 'Name of the action'
                    },
                },
                "transitions": {
                    'type': 'array',
                    "description": "A list of state transitions of the object",
                    "items": {
                        "type": "object",
                        "description": "A single transtion, consisting of a start state, an action, and the target state that the object changes to.",
                        'properties': {
                            'startState': {
                                'type': 'string',
                                'description': 'The starting state of the object. This must come from the list of states'
                            },
                            'action': {
                                'type': 'string',
                                'description': 'The action that when applied to the startState, results in the targetState. This must be from the list of actions'
                            },
                            'targetState': {
                                'type': 'string',
                                'description': 'The target state of the object that is the result of the action being applied while the object is in the start state. This must come from the list of states'
                            },
                        },
                        "required": ["startingState", "action", "targetState"]
                    },
                },
            },
            "required": ["states","initialState","actions","transitions"]
        }
    }
    
    def _generate_finite_state_machine(self, states, initialState, actions, transitions):
        return FiniteStateMachine(states, initialState, actions, transitions)

    def _parseResponse(self, response_message):
        if response_message.function_call and response_message.function_call.arguments:
            #Which function call was invoked?
            function_called = response_message.function_call.name
            
            #Extract the arguments from the AI payload
            function_args  = json.loads(response_message.function_call.arguments)
            
            #Create a list of all the available functions
            available_functions = {
                "generate_finite_state_machine": self._generate_finite_state_machine,
            }
            
            function_to_call = available_functions[function_called]

            #Call the function with the provided arguments
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None
    
    def GenerateStateMachine(self, item, llm=None):
        if llm is None:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': """Given the following item, generate a finite state machine."
             The finite state machine consists of a list of states the item can be in, the initial defaul state of the item, 
             a list of actions that result in state changes of the item, and a list of state transitions.
             A state transition consists of an start state, the action that occurs, and the resulting target state.
             """},
            {'role': 'user', 'content': item}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ FiniteStateMachineGenerator.generateFiniteStateMachineFunctionDef ]

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(response.choices[0].message)