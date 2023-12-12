from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
from Simulation.scenario import Scenario
from Generators.locationGenerator import LocationGenerator

class ScenarioGenerator:

    def Generate(self, description, llm = None):
        if llm is None:
            llm = ChatOpenAI()
        messages = [
            SystemMessage(content="Expand the following description of a scenario."),
            HumanMessage(content=description),]
        result = llm.invoke(messages)
        return Scenario(description, result.content)
    
    def GenerateLocations(self, scenario, llm= None):
        locationGen = LocationGenerator()
        self.locations = locationGen.Generate(scenario.name)