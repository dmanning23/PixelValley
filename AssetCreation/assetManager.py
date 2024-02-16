from Models.agentDescriptionModel import AgentDescriptionModel
from Repository.simulationRepository import SimulationRepository

class AssetManager:

    def PopulateMissingCharacterDescriptions(self, scenario, characterDescriptionGenerator):
        for agent in scenario.GetAgents():
            #get a character description
            description = None
            try:
                description = AgentDescriptionModel.objects.get(agentId=agent._id)
            except:
                pass
            if description is None:
                description = characterDescriptionGenerator.DescribeCharacter(agent)
                if description is not None:
                    description.agentId = agent._id
                    AgentDescriptionModel.objects.insert(description)
            else:
                if hasattr(agent, "portraitFilename") and agent.portraitFilename:
                    description.portraitFilename = agent.portraitFilename
                if hasattr(agent, "iconFilename") and agent.iconFilename:
                    description.iconFilename = agent.iconFilename
                if hasattr(agent, "resizedIconFilename") and agent.resizedIconFilename:
                    description.resizedIconFilename = agent.resizedIconFilename
                if hasattr(agent, "chibiFilename") and agent.chibiFilename:
                    description.chibiFilename = agent.chibiFilename
                if hasattr(agent, "resizedChibiFilename") and agent.resizedChibiFilename:
                    description.resizedChibiFilename = agent.resizedChibiFilename
                description.save()

    def PopulateMissingCharacterProfile(self, scenario, characterPortraitGenerator):
        agents = scenario.GetAgents()
        for agent in agents:
            description = AgentDescriptionModel.objects.get(agentId=agent._id)
            if not description.portraitFilename:
                description.portraitFilename = characterPortraitGenerator.CreatePortrait(agent, description)
                description.save()

    def PopulateMissingCharacterIcons(self, scenario, characterIconGenerator):
        agents = scenario.GetAgents()
        for agent in agents:
            description = AgentDescriptionModel.objects.get(agentId=agent._id)
            if not description.iconFilename or not description.resizedIconFilename:
                description.iconFilename, description.resizedIconFilename = characterIconGenerator.CreateIcon(agent, description)
                description.save()

    def PopulateMissingCharacterChibis(self, scenario, characterChibiGenerator):
        agents = scenario.GetAgents()
        for agent in agents:
            description = AgentDescriptionModel.objects.get(agentId=agent._id)
            if not description.chibiFilename or not description.resizedChibiFilename:
                description.chibiFilename, description.resizedChibiFilename = characterChibiGenerator.CreateChibi(agent, description)
                description.save()

    def CreateScenarioBackground(self, userId, scenario, backgroundGenerator):
        if not scenario.imageFilename:
            scenario.imageFilename = backgroundGenerator.CreateScenarioBackground(scenario)

        simulationRepository = SimulationRepository()
        simulationRepository.SaveScenario(userId, scenario)

    def PopulateMissingBuildingExteriors(self, scenario, buildingExteriorGenerator):
        for location in scenario.locations:
            if not location.imageFilename or not location.resizedImageFilename:
                location.imageFilename, location.resizedImageFilename = buildingExteriorGenerator.CreateLocation(location, scenario)
        simulationRepository = SimulationRepository()
        simulationRepository.SaveLocations(scenario)