import random

from flask import Flask, render_template

app = Flask(__name__)

character_types = {"Empire Builder", "Merchant", "Pirate", "Artifact Collector", "Berserker"}

player_commands = {"Transfer", "Build", "Move", "Fire", "Ambush", "Gift", "Trade", "Diplomacy", "Research", "End Turn"}


class Player:
    def __init__(self, name, character_type, home_world, diplomacy, worlds, fleets):
        self.name = name
        self.character_type = character_type
        self.home_world = home_world
        self.diplomacy = diplomacy
        self.worlds = worlds
        self.fleets = fleets
        self.character = self.create_character()

    def create_character(self):
        if self.character_type == "Empire Builder":
            return EmpireBuilder(self.name)
        elif self.character_type == "Merchant":
            return Merchant(self.name)
        elif self.character_type == "Pirate":
            return Pirate(self.name)
        elif self.character_type == "Artifact Collector":
            return ArtifactCollector(self.name)
        elif self.character_type == "Berserker":
            return Berserker(self.name)
        else:
            return None


class EmpireBuilder: Player


def __init__(self, name):
    self.name = name


class Merchant: Player


def __init__(self, name):
    self.name = name


class Pirate: Player


def __init__(self, name):
    self.name = name


class ArtifactCollector: Player


def __init__(self, name):
    self.name = name


class Berserker: Player


def __init__(self, name):
    self.name = name


class StarWeb:
    """This is a docstring for the StarWeb class"""

    """This is a docstring for the index method"""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)


class World:
    """This is a docstring for the World class"""

    def __init__(self, id, name, owner, connections, iships, pships, population, max_population, industry, mines,
                 stockpile,
                 artifacts):
        self.id = id
        self.name = name
        self.owner = owner
        self.connections = connections
        self.iships = iships
        self.pships = pships
        self.population = population
        self.max_population = max_population
        self.industry = industry
        self.mines = mines
        self.stockpile = stockpile
        self.artifacts = artifacts


class Fleet:
    """This is a docstring for the Fleet class"""

    def __init__(self, id, name, ships, location: World, owner, cargo, artifacts):
        self.id = id
        self.name = name
        self.ships = ships
        self.location = location
        self.owner = owner
        self.cargo = cargo
        self.artifacts = artifacts


# string that renders a fleet object using jinja2
def stream_fleet(fleet):
    return render_template('fleet.html', fleet=fleet)


# string that renders a world object using jinja2
def stream_world(world):
    return render_template('world.html', world=world)


# string that renders a player object using jinja2
def stream_player(player):
    return render_template('player.html', player=player)


artifact_first_names = ["Platinum", "Ancient", "Vegan", "Blessed", "Arcturian", "Silver", "Titanium", "Gold", "Radiant",
                        "Plastic"]
artifact_second_names = ["Lodestar", "Pyramid", "Stardust", "Shekel", "Crown", "Sword", "Moonstone", "Sepulchre",
                         "Sphinx"]
artifact_list = [[first + " " + second for first in artifact_first_names for second in artifact_second_names]]


def create_worlds():
    worlds = []
    for i in range(1, 11):
        worlds.append(
            World(i, "World " + str(i), None, [], random.randint(1, 10), random.randint(1, 10), random.randint(1, 10),
                  random.randint(1, 10), random.randint(1, 10), random.randint(1, 10), random.randint(1, 10), []))
    return worlds


def connect_worlds(worlds: []):
    max_worlds = len(worlds)
    for i in range(0, max_worlds - 1):
        connection_number = 1 + random.randint(1, 3)
        for c in range(0, connection_number):

            j = random.randint(0, max_worlds - 1)
            if i != j:
                worlds[i].connections.append(worlds[j])
                worlds[j].connections.append(worlds[i])


def create_fleets():
    fleets = []
    for i in range(1, 11):
        fleets.append(Fleet(i, "Fleet " + str(i), 0, None, None, 0, 0))
    return fleets


def input_worlds(worlds):
    for world in worlds:
        print(stream_world(world))


def input_fleets(fleets):
    for fleet in fleets:
        print(stream_fleet(fleet))


def input_players(players):
    for player in players:
        print(stream_player(player))


def input_game(game):
    return stream_game(game)


def is_valid_command(command):
    if command in player_commands:
        return True
    else:
        return False


def transfer_ships_to_fleet(fleet1, fleet2, ships):
    if fleet1.ships >= ships:
        fleet1.ships -= ships
        fleet2.ships += ships
        return True
    else:
        return False


def transfer_ships_to_pships(fleet, world, ships):
    if fleet.ships >= ships:
        fleet.ships -= ships
        world.pships += ships
        return True
    else:
        return False


def transfer_ships_to_iships(fleet, world, ships):
    if fleet.ships >= ships:
        fleet.ships -= ships
        world.iships += ships
        return True
    else:
        return False


def transfer_iships_to_fleet(fleet, world, ships):
    if world.iships >= ships:
        world.iships -= ships
        fleet.ships += ships
        return True
    else:
        return False


def transfer_pships_to_fleet(fleet, world, ships):
    if world.pships >= ships:
        world.pships -= ships
        fleet.ships += ships
        return True
    else:
        return False


def stream_world(world):
    return world.name + " " + str(world.owner) + " " + str(world.connections) + " " + str(world.iships) + " " + str(
        world.pships) + " " + str(world.population) + " " + str(world.max_population) + " " + str(
        world.industry) + " " + str(
        world.mines) + " " + str(world.stockpile) + " " + str(world.artifact_list)


def process_command(command, game):
    if is_valid_command(command):
        command_function = getattr(game, command);
        command_function(game)
    else:
        print("Invalid Command")


def stream_fleet(fleet):
    return fleet.name + " " + str(fleet.ships) + " " + str(fleet.location) + " " + str(fleet.owner) + " " + str(
        fleet.cargo) + " " + str(fleet.artifact_list)


def stream_player(player):
    return player.name + " " + player.character_type + " " + str(player.home_world) + " " + str(
        player.diplomacy) + " " + str(
        player.worlds) + " " + str(player.fleets) + " " + str(player.character)


def stream_game(game):
    return str(game.worlds) + " " + str(game.fleets) + " " + str(game.players)


class Game:
    """This is a docstring for the Game class"""

    def __init__(self, worlds, fleets, players):
        self.worlds = worlds
        self.fleets = fleets
        self.players = players

    def BuildCommand(self):
        print("Build")

    def MoveCommand(self):
        print("Move")

    def AttackCommand(self):
        print("Attack")

    def TradeCommand(self):
        print("Trade")

    def ColonizeCommand(self):
        print("Colonize")

    def ResearchCommand(self):
        print("Research")

    def EndTurnCommand(self):
        print("End Turn")

    def create_worlds(self):
        self.worlds = create_worlds()

    def connect_worlds(self):
        connect_worlds(self.worlds)

    def create_fleets(self):
        self.fleets = create_fleets()

    def input_worlds(self):
        input_worlds(self.worlds)

    def input_fleets(self):
        input_fleets(self.fleets)

    def input_players(self):
        input_players(self.players)

    def input_game(self):
        return input_game(self)

    def transfer_ships_to_fleet(self, fleet1, fleet2, ships):
        return transfer_ships_to_fleet(fleet1, fleet2, ships)

    def transfer_ships_to_pships(self, fleet, world, ships):
        return transfer_ships_to_pships(fleet, world, ships)

    def transfer_ships_to_iships(self, fleet, world, ships):
        return transfer_ships_to_iships(fleet, world, ships)

    def transfer_iships_to_fleet(self, fleet, world, ships):
        return transfer_iships_to_fleet(fleet, world, ships)

    def transfer_pships_to_fleet(self, fleet, world, ships):
        return transfer_pships_to_fleet(fleet, world, ships)

    def stream_world(self, world):
        return stream_world(world)

    def process_command(self, command):
        process_command(command, self)

    def stream_fleet(self, fleet):
        return stream_fleet(fleet)

    def stream_player(self, player):
        return stream_player(player)

    def stream_game(self):
        return stream_game(self)


def create_game():
    worlds = create_worlds()
    connect_worlds(worlds)
    fleets = create_fleets()
    return Game(worlds, fleets, [])


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/game')
def display_game():
    game = create_game()
    return render_template('game.html', game=game)


if __name__ == '__main__':
    app.wsgi_app = StarWeb(app.wsgi_app)
    app.run()
