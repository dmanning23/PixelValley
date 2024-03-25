from Models.agentDescriptionModel import AgentDescriptionModel
from Repository.simulationRepository import SimulationRepository
from Repository.locationRepository import LocationRepository
from AssetCreation.s3Uploader import *
from keys import s3Bucket

class AssetManager:

    async def PopulateMissingCharacterDescriptions(self, scenario, characterDescriptionGenerator):
        for agent in scenario.GetAgents():
            #get a character description
            description = None
            try:
                description = AgentDescriptionModel.objects.get(agentId=agent._id)
            except:
                pass
            if description is None:
                description = await characterDescriptionGenerator.DescribeCharacter(agent)
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
                    upload_file(description.portraitFilename, s3Bucket)
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
                    upload_file(description.iconFilename, s3Bucket)
                    upload_file(description.resizedIconFilename, s3Bucket)
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
                    upload_file(description.chibiFilename, s3Bucket)
                    upload_file(description.resizedChibiFilename, s3Bucket)
                except:
                    #TODO: log errors?
                    pass

    def CreateScenarioBackground(self, userId, scenario, backgroundGenerator):
        try:
            if not scenario.imageFilename:
                scenario.imageFilename = backgroundGenerator.CreateScenarioBackground(scenario)
                simulationRepository = SimulationRepository()
                simulationRepository.SaveScenario(userId, scenario)
                upload_file(scenario.imageFilename, s3Bucket)
        except:
            pass

    def PopulateMissingBuildingExteriors(self, scenario, buildingExteriorGenerator):
        locationRepository = LocationRepository()
        for location in scenario.locations:
            if not location.imageFilename or not location.resizedImageFilename:
                try:
                    location.imageFilename, location.resizedImageFilename = buildingExteriorGenerator.CreateLocation(location, scenario)
                    locationRepository.CreateOrUpdate(location, scenario._id)
                    upload_file(location.imageFilename, s3Bucket)
                    upload_file(location.resizedImageFilename, s3Bucket)
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
                upload_file(location.imageInteriorFilename, s3Bucket)
                upload_file(location.resizedImageInteriorFilename, s3Bucket)
            except:
                pass
        if location.locations is not None:
            for childLocation in location.locations:
                self._populateMissingBuildingInteriors(childLocation, scenario, buildingInteriorGenerator, locationRepository, location._id)

    def UploadToS3(self, scenario):
        try:
            if scenario.imageFilename:
                upload_file(scenario.imageFilename, s3Bucket)
            agents = scenario.GetAgents()
            for agent in agents:
                description = AgentDescriptionModel.objects.get(agentId=agent._id)
                if description.portraitFilename:
                    upload_file(description.portraitFilename, s3Bucket)

                if description.iconFilename:
                    upload_file(description.iconFilename, s3Bucket)
                if description.resizedIconFilename:
                    upload_file(description.resizedIconFilename, s3Bucket)

                if description.chibiFilename:
                    upload_file(description.chibiFilename, s3Bucket)
                if description.resizedChibiFilename:
                    upload_file(description.resizedChibiFilename, s3Bucket)

            for location in scenario.locations:
                if location.imageFilename:
                    upload_file(location.imageFilename, s3Bucket)
                if location.resizedImageFilename:
                    upload_file(location.resizedImageFilename, s3Bucket)

                if location.imageInteriorFilename:
                    upload_file(location.imageInteriorFilename, s3Bucket)
                if location.resizedImageInteriorFilename:
                    upload_file(location.resizedImageInteriorFilename, s3Bucket)

                for childLocation in location.locations:
                    if childLocation.imageInteriorFilename:
                        upload_file(childLocation.imageInteriorFilename, s3Bucket)
                    if childLocation.resizedImageInteriorFilename:
                        upload_file(childLocation.resizedImageInteriorFilename, s3Bucket)
        except:
            pass
