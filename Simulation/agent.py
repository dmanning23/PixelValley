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
        a short decription of the character's personality
    """

    def __init__(self, name, age, gender, description):
        self.name = name
        self.age = age
        self.gender = gender
        self.description = description

    def __str__(self) -> str:
        return f"{self.name} is a {self.age} year old {self.gender}. {self.description}"