from Models.agentDescriptionModel import AgentDescriptionModel
from Repository.simulationRepository import SimulationRepository
from Repository.locationRepository import LocationRepository
from AssetCreation.s3Uploader import *

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
                try:
                    description.portraitFilename = characterPortraitGenerator.CreatePortrait(agent, scenario, description)
                    description.save()
                except:
                    pass

    def PopulateMissingCharacterIcons(self, scenario, characterIconGenerator):
        agents = scenario.GetAgents()
        for agent in agents:
            description = AgentDescriptionModel.objects.get(agentId=agent._id)
            if not description.iconFilename or not description.resizedIconFilename:
                try:
                    description.iconFilename, description.resizedIconFilename = characterIconGenerator.CreateIcon(agent, scenario, description)
                    description.save()
                except:
                    pass

    def PopulateMissingCharacterChibis(self, scenario, characterChibiGenerator):
        agents = scenario.GetAgents()
        for agent in agents:
            description = AgentDescriptionModel.objects.get(agentId=agent._id)
            if not description.chibiFilename or not description.resizedChibiFilename:
                try:
                    description.chibiFilename, description.resizedChibiFilename = characterChibiGenerator.CreateChibi(agent, scenario, description)
                    description.save()
                except:
                    #TODO: log errors?
                    pass

    def CreateScenarioBackground(self, userId, scenario, backgroundGenerator):
        try:
            if not scenario.imageFilename:
                scenario.imageFilename = backgroundGenerator.CreateScenarioBackground(scenario)
            simulationRepository = SimulationRepository()
            simulationRepository.SaveScenario(userId, scenario)
        except:
            pass

    def PopulateMissingBuildingExteriors(self, scenario, buildingExteriorGenerator):
        locationRepository = LocationRepository()
        for location in scenario.locations:
            if not location.imageFilename or not location.resizedImageFilename:
                try:
                    location.imageFilename, location.resizedImageFilename = buildingExteriorGenerator.CreateLocation(location, scenario)
                    locationRepository.CreateOrUpdate(location, scenario._id)
                except:
                    pass

    def PopulateMissingBuildingInteriors(self, scenario, buildingInteriorGenerator):
        locationRepository = LocationRepository()
        for location in scenario.locations:
            self._populateMissingBuildingInteriors(location, scenario, buildingInteriorGenerator, locationRepository)

    def _populateMissingBuildingInteriors(self, location, scenario, buildingInteriorGenerator, locationRepository, parentLocationId=None):
        if not location.imageInteriorFilename:
            try:
                location.imageInteriorFilename, location.resizedImageInteriorFilename = buildingInteriorGenerator.CreateLocation(location, scenario)
                locationRepository.CreateOrUpdate(location, scenario._id, parentLocationId)
            except:
                pass
        for childLocation in location.locations:
            self._populateMissingBuildingInteriors(childLocation, scenario, buildingInteriorGenerator, locationRepository, location._id)

    def UploadToS3(self, scenario):
        try:
            if scenario.imageFilename:
                upload_file(scenario.imageFilename, "pixelvalley")
            agents = scenario.GetAgents()
            for agent in agents:
                description = AgentDescriptionModel.objects.get(agentId=agent._id)
                if description.portraitFilename:
                    upload_file(description.portraitFilename, "pixelvalley")

                if description.iconFilename:
                    upload_file(description.iconFilename, "pixelvalley")
                if description.resizedIconFilename:
                    upload_file(description.resizedIconFilename, "pixelvalley")

                if description.chibiFilename:
                    upload_file(description.chibiFilename, "pixelvalley")
                if description.resizedChibiFilename:
                    upload_file(description.resizedChibiFilename, "pixelvalley")

            for location in scenario.locations:
                if location.imageFilename:
                    upload_file(location.imageFilename, "pixelvalley")
                if location.resizedImageFilename:
                    upload_file(location.resizedImageFilename, "pixelvalley")

                if location.imageInteriorFilename:
                    upload_file(location.imageInteriorFilename, "pixelvalley")
                if location.resizedImageInteriorFilename:
                    upload_file(location.resizedImageInteriorFilename, "pixelvalley")

                for childLocation in location.locations:
                    if childLocation.imageInteriorFilename:
                        upload_file(childLocation.imageInteriorFilename, "pixelvalley")
                    if childLocation.resizedImageInteriorFilename:
                        upload_file(childLocation.resizedImageInteriorFilename, "pixelvalley")
        except:
            pass
