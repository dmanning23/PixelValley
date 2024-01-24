import json
from openai import OpenAI

class ReflectionGenerator():

    askQuestionsFunctionDef = {
        'name': 'ask_questions',
        'description': 'Ask a list of high level questions',
        'parameters': {
            "type": "object",
            "properties": {
                "questions": {
                    'type': 'array',
                    "description": "A list of questions",
                    "items": {
                        "type": "string",
                        "description": "A single question",
                    },
                },
            },
            "required": ["questions"]
        }
    }

    createInsightFunctionDef = {
        'name': 'create_insight',
        'description': 'Create a high level insight',
        'parameters': {
            "type": "object",
            "properties": {
                "insights": {
                    'type': 'array',
                    "description": "A list of high level insights",
                    "items": {
                        "type": "string",
                        "description": "A single high level insight",
                    },
                },
            },
            "required": ["insights"]
        }
    }

    def __init__(self, memoryRepository, retrievalStream, llm=None):
        if not llm:
            #create the client API
            self.llm = OpenAI()

        self.memoryRepository = memoryRepository
        self.retrievalStream = retrievalStream

    def _ask_questions(self, agent, questions):
        for question in questions:
            self.AskQuestion(agent, question)
    
    def _create_insight(self, agent, insights):
        for insight in insights:
            self.memoryRepository.CreateMemory(agent, insight)

    def _parseResponse(self, agent, response_message):
        if response_message.function_call and response_message.function_call.arguments:
            #Which function call was invoked?
            function_called = response_message.function_call.name
            
            #Extract the arguments from the AI payload
            function_args  = json.loads(response_message.function_call.arguments)
            
            #Create a list of all the available functions
            available_functions = {
                "ask_questions": self._ask_questions,
                "create_insight": self._create_insight
            }
            
            function_to_call = available_functions[function_called]

            #Call the function with the provided arguments
            function_to_call(agent, *list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            #TODO: tweak the function calls so they always get called. It should never return text!
            pass

    def CreateReflections(self, agent):
        #Get the 100 most recent memories for the agent
        recentMemories = self.memoryRepository.GetRecentMemories(agent, 100)

        messages = [
            {'role': 'system', 'content': "Given only the following information, what are three salient high-level questions we can answer about the subjects in the statements?"},
        ]
        for recentMemory in recentMemories:
            messages.append({'role': 'user', 'content': recentMemory.description})

        functions = [ ReflectionGenerator.askQuestionsFunctionDef ]

        response = self.llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        self._parseResponse(agent, response.choices[0].message)
        
    def AskQuestion(self, agent, question):
        #get the relevant memories of the question
        memories = self.retrievalStream.RetrieveMemories(agent, question)

        messages = [
            {'role': 'system', 'content': f"Given the following statements about {agent.name}, what are three high-level insights that we can infer?"},
        ]

        for memory in memories:
            messages.append({'role': 'user', 'content': memory.description})

        functions = [ ReflectionGenerator.createInsightFunctionDef ]

        #Call the LLM...
        response = self.llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        self._parseResponse(agent, response.choices[0].message)
