import random

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

game = None  # Global game instance

character_types = {"Empire Builder", "Merchant", "Pirate", "Artifact Collector", "Berserker"}

player_commands = {"Transfer", "Build", "Move", "Fire", "Ambush", "Gift", "Trade", "Diplomacy", "Research", "End Turn"}


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


class EmpireBuilder:
    """This is a docstring for the EmpireBuilder class"""

    def __init__(self, id, name, world, fleets, artifacts, ships):
        self.id = id
        self.name = name
        self.world = world
        self.fleets = fleets
        self.artifacts = artifacts
        self.ships = ships


class Merchant:
    """This is a docstring for the Merchant class"""

    def __init__(self, id, name, world, fleets, artifacts, ships):
        self.id = id
        self.name = name
        self.world = world
        self.fleets = fleets
        self.artifacts = artifacts
        self.ships = ships


class Pirate:
    """This is a docstring for the Pirate class"""

    def __init__(self, id, name, world, fleets, artifacts, ships):
        self.id = id
        self.name = name
        self.world = world
        self.fleets = fleets
        self.artifacts = artifacts
        self.ships = ships


class ArtifactCollector:
    """This is a docstring for the ArtifactCollector class"""

    def __init__(self, id, name, world, fleets, artifacts, ships):
        self.id = id
        self.name = name
        self.world = world
        self.fleets = fleets
        self.artifacts = artifacts
        self.ships = ships


class Berserker:
    """This is a docstring for the Berserker class"""

    def __init__(self, id, name, world, fleets, artifacts, ships):
        self.id = id
        self.name = name
        self.world = world
        self.fleets = fleets
        self.artifacts = artifacts
        self.ships = ships


class Player:
    def __init__(self, name, character_type, home_world: World, diplomacy, worlds: [], fleets: []):
        self.name = name
        self.character_type = character_type
        self.home_world = home_world
        self.diplomacy = diplomacy
        self.worlds = worlds
        self.fleets = fleets
        self.character = self.create_character()

    def create_character(self):
        if self.character_type == "Empire Builder":
            return EmpireBuilder(self)
        elif self.character_type == "Merchant":
            return Merchant(self)
        elif self.character_type == "Pirate":
            return Pirate(self)
        elif self.character_type == "Artifact Collector":
            return ArtifactCollector(self)
        elif self.character_type == "Berserker":
            return Berserker(self)
        else:
            return None


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

    def MoveCommand(self, fleet_id, target_world_ids):
        # Retrieve the fleet object
        fleet_to_move = next((f for f in self.fleets if f.id == fleet_id), None)

        if not fleet_to_move:
            print(f"Error: Fleet with ID {fleet_id} not found.")
            return False

        if fleet_to_move.ships <= 0:
            print(f"Error: Fleet {fleet_to_move.name} has no ships and cannot move.")
            return False

        if len(target_world_ids) > 2:
            print("Error: Fleet can move at most 2 segments (current -> world1 -> world2).")
            return False

        current_location = fleet_to_move.location
        path = [current_location] + target_world_ids

        # Validate path
        for i in range(len(path) - 1):
            world1 = path[i]
            world2 = path[i+1]

            # Ensure world1 and world2 are actual World objects if IDs were passed
            if not isinstance(world1, World):
                world1_obj = next((w for w in self.worlds if w.id == world1), None)
                if not world1_obj:
                    print(f"Error: World with ID {world1} not found in path.")
                    return False
                world1 = world1_obj
            
            if not isinstance(world2, World):
                world2_obj = next((w for w in self.worlds if w.id == world2), None)
                if not world2_obj:
                    print(f"Error: World with ID {world2} not found in path.")
                    return False
                world2 = world2_obj
            
            # Check connection
            if world2 not in world1.connections and world1 not in world2.connections: # Assuming connections are two-way
                print(f"Error: World {world1.name} is not connected to {world2.name}.")
                return False
        
        # Movement Logic
        final_destination_world_id = target_world_ids[-1]
        final_destination_world = next((w for w in self.worlds if w.id == final_destination_world_id), None)
        if isinstance(target_world_ids[-1], World): # if it's already an object
            final_destination_world = target_world_ids[-1]


        if not final_destination_world:
            # This should ideally be caught by path validation earlier if IDs are used
            print(f"Error: Final destination world {final_destination_world_id} not found.")
            return False

        for i in range(len(target_world_ids)):
            intermediate_world_id = target_world_ids[i]
            intermediate_world = next((w for w in self.worlds if w.id == intermediate_world_id), None)
            if isinstance(target_world_ids[i], World): # if it's already an object
                intermediate_world = target_world_ids[i]

            if not intermediate_world:
                 print(f"Error: Intermediate world {intermediate_world_id} not found during movement.")
                 return False # Should not happen if path validation is correct

            if i < len(target_world_ids) - 1:
                # This is an intermediate world
                # TODO: Implement logic for hostile fleets at this intermediate world to fire upon the moving fleet.
                print(f"Fleet {fleet_to_move.name} passing through {intermediate_world.name}...") # Optional: for tracing
            
        fleet_to_move.location = final_destination_world
        print(f"Fleet {fleet_to_move.name} moved to {final_destination_world.name}.")
        return True

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
    # Initialize fleets with some ships and a starting location for testing
    if worlds: # Ensure worlds exist
        for i, fleet in enumerate(fleets):
            fleet.ships = random.randint(5, 20) # Give some ships
            fleet.location = worlds[i % len(worlds)] # Assign a starting world
            fleet.owner = "Player 1" # Assign an owner for display
    return Game(worlds, fleets, [])

def get_or_create_game():
    global game
    if game is None:
        game = create_game()
    return game

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/game')
def display_game():
    game_instance = get_or_create_game()
    return render_template('game.html', game=game_instance)

@app.route('/move_fleet', methods=['POST'])
def move_fleet():
    game_instance = get_or_create_game()
    fleet_id_str = request.form.get('fleet_id')
    world1_id_str = request.form.get('world1_id')
    world2_id_str = request.form.get('world2_id')

    if not fleet_id_str or not world1_id_str:
        flash("Error: Fleet ID and at least the first destination World ID are required.")
        return redirect(url_for('display_game'))

    try:
        fleet_id = int(fleet_id_str)
    except ValueError:
        flash(f"Error: Invalid Fleet ID '{fleet_id_str}'. Must be a number.")
        return redirect(url_for('display_game'))

    target_worlds_path = []
    world_ids_str = [world1_id_str, world2_id_str]

    for world_id_s in world_ids_str:
        if world_id_s:  # If the world ID string is not empty
            try:
                world_id = int(world_id_s)
                world = next((w for w in game_instance.worlds if w.id == world_id), None)
                if world:
                    target_worlds_path.append(world)
                else:
                    flash(f"Error: World with ID {world_id} not found.")
                    return redirect(url_for('display_game'))
            except ValueError:
                flash(f"Error: Invalid World ID '{world_id_s}'. Must be a number.")
                return redirect(url_for('display_game'))
    
    if not target_worlds_path: # Should be caught by earlier check for world1_id_str but as a safeguard
        flash("Error: At least one valid destination world must be specified.")
        return redirect(url_for('display_game'))

    # Call MoveCommand
    # We need to ensure the fleet's current location is a World object if it's an ID
    # However, MoveCommand already handles resolving world IDs to objects internally.
    # The target_worlds_path is already a list of World objects.
    
    # First, ensure the fleet itself exists. MoveCommand does this, but we can give a better flash.
    fleet_to_move = next((f for f in game_instance.fleets if f.id == fleet_id), None)
    if not fleet_to_move:
        flash(f"Error: Fleet with ID {fleet_id} not found.")
        return redirect(url_for('display_game'))

    # If the fleet's current location is not set (e.g., newly created fleet)
    # MoveCommand expects fleet.location to be a World object or a resolvable ID
    # Our create_fleets assigns a world object now.
    if fleet_to_move.location is None:
        flash(f"Error: Fleet {fleet_to_move.name} (ID: {fleet_id}) has an unassigned starting location and cannot move.")
        return redirect(url_for('display_game'))


    success = game_instance.MoveCommand(fleet_id=fleet_id, target_world_ids=target_worlds_path)

    if success:
        flash(f"Fleet {fleet_id} move command processed. Check console/fleet list for status.")
    else:
        # MoveCommand prints its own errors, but we can add a generic flash message.
        flash(f"Fleet {fleet_id} move command failed. See console for details.")
            
    return redirect(url_for('display_game'))


if __name__ == '__main__':
    app.wsgi_app = StarWeb(app.wsgi_app)
    app.run()
