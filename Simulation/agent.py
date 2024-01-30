
class Agent:
    def __init__(self,
                 name,
                 age,
                 gender,
                 description,
                 _id = None,
                 currentTime = 0,
                 currentItem = None,
                 usingItem = None,
                 status = "Idle",
                 emoji = "",
                 timeOfLastReflection = 0):
        if _id is not None:
            self._id = _id
        self.name = name
        self.age = age
        self.gender = gender
        self.description = description
        self.currentTime = currentTime

        #is the agent holding an item?
        self.currentItem = currentItem

        #is the agent interacting with an item?
        self.usingItem = usingItem

        #set the agent's emoji
        self.emoji = emoji

        #what is the agent doing?
        self.status = status

        #Time of last reflection
        self.timeOfLastReflection = timeOfLastReflection

    def __str__(self) -> str:
        return f"{self.name} is a {self.age} year old {self.gender}. {self.description}"
    
    def IncrementTime(self):
        self.currentTime = self.currentTime + 1

    def IsUsingHeldItem(self):
        return ((self.currentItem is not None) and (self.usingItem is not None) and (self.currentItem.name == self.usingItem.name))