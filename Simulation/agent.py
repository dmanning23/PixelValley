
class Agent:
    """
    An agent in the simulation.

    Attributes:
    name: string
        name of the character
    age: integer
        age of the character
    gender: string
        chosen gender of the character
    description:
        a short description of the character's personality
    currentTime:
        this is an integer that is used to age the agent's memories.
        It is stored here rather than in the simulation because agents will 
        eventually be allowed to move between simulations.
    """

    def __init__(self, name, age, gender, description, _id = None, currentTime = 0, currentItem = None, usingItem = None, status = "Idle"):
        if _id is not None:
            self._id = _id
        self.name = name
        self.age = age
        self.gender = gender
        self.description = description
        self.currentTime = currentTime

        #TODO: currentItem storage
        #is the agent holding an item?
        self.currentItem = currentItem

        #TODO: i don't love this method of keeping track who is using what item >:(
        #TODO: usingItem storage
        #is the agent interacting with an item?
        self.usingItem = usingItem

        #TODO: set the agent's emoji
        #TODO: store the agent's emoji

        #what is the agent doing?
        self.status = status

    def __str__(self) -> str:
        return f"{self.name} is a {self.age} year old {self.gender}. {self.description}"
    
    def IncrementTime(self):
        self.currentTime = self.currentTime + 1