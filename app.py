import random
import json # Added for parsing JSON

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required # Added logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash # Already present, good

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Name of the login route's view function
login_manager.login_message_category = 'info'


game = None  # Global game instance

character_types = {"Empire Builder", "Merchant", "Pirate", "Artifact Collector", "Berserker", "Apostle"}

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

    def __init__(self, id, name, owner: 'Player | None', connections: list, iships: int, pships: int, 
                 population: int, max_population: int, industry: int, mines: int,
                 stockpile: int,
                 artifacts: list['Artifact'] | None = None): # Type hint for artifacts
        self.id = id
        self.name = name
        self.owner: Player | None = owner
        self.connections = connections if connections is not None else []
        self.iships = iships
        self.pships = pships
        self.population = population
        self.max_population = max_population
        self.industry = industry
        self.mines = mines
        self.stockpile = stockpile
        self.artifacts: list[Artifact] = artifacts if artifacts is not None else []


class Fleet:
    """This is a docstring for the Fleet class"""

    def __init__(self, id, name, ships: int, location: World | None, owner: 'Player | None', 
                 cargo: int, artifacts: list['Artifact'] | None = None): # Type hint for artifacts
        self.id = id
        self.name = name
        self.ships = ships
        self.location: World | None = location
        self.owner: Player | None = owner
        self.cargo = cargo
        self.artifacts: list[Artifact] = artifacts if artifacts is not None else []


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
    def __init__(self, name: str, character_type: str, user_id: str, home_world: World | None = None, diplomacy: dict | None = None, worlds: list[World] | None = None, fleets: list[Fleet] | None = None):
        self.name = name # Often same as User.username
        self.character_type = character_type
        self.user_id = user_id # Link to Flask-Login User.id
        self.home_world: World | None = home_world
        self.diplomacy = diplomacy if diplomacy is not None else {}
        self.worlds: list[World] = [home_world] if home_world and (worlds is None or home_world not in worlds) else (worlds if worlds is not None else [])
        if home_world and not self.worlds: # Ensure homeworld is in worlds if worlds was passed as empty or None
            self.worlds.append(home_world)
        self.fleets: list[Fleet] = fleets if fleets is not None else []
        self.character = self.create_character()

    def create_character(self):
        # Assuming character classes now take the Player object itself if needed
        # For now, their constructors seem to take (self) which implies player instance methods
        # or they take specific attributes. Let's assume they are simple for now.
        # If EmpireBuilder(self) means passing the player instance, this is fine.
        if self.character_type == "Empire Builder":
            # Pass necessary player attributes if character class expects them
            return EmpireBuilder(id=self.name, name=self.name, world=self.home_world, fleets=self.fleets, artifacts=[], ships=0) # Example
        elif self.character_type == "Merchant":
            return Merchant(id=self.name, name=self.name, world=self.home_world, fleets=self.fleets, artifacts=[], ships=0)
        elif self.character_type == "Pirate":
            return Pirate(id=self.name, name=self.name, world=self.home_world, fleets=self.fleets, artifacts=[], ships=0)
        elif self.character_type == "Artifact Collector":
            return ArtifactCollector(id=self.name, name=self.name, world=self.home_world, fleets=self.fleets, artifacts=[], ships=0)
        elif self.character_type == "Berserker":
            return Berserker(id=self.name, name=self.name, world=self.home_world, fleets=self.fleets, artifacts=[], ships=0)
        else:
            return None

# Artifact Class
class Artifact:
    def __init__(self, id: str, name: str, points: int = 0, is_plastic: bool = False, category: str = "Standard"):
        self.id = id # e.g., "V1", "V2", ... "V100"
        self.name = name
        self.points = points # General score, specific character bonuses handled by game logic later
        self.is_plastic = is_plastic
        self.category = category # "Standard", "Special", "GreatestTreasure" (for easier identification if needed)
        # For standard artifacts, we might add first_word, second_word attributes if useful for scoring later
        self.first_word = ""
        self.second_word = ""
        if category == "Standard": 
            parts = name.split(" ", 1)
            if len(parts) == 2:
                self.first_word = parts[0]
                self.second_word = parts[1]
        # No special parsing needed for "Special" category for first/second word here based on prompt

    def __repr__(self):
        return f"<Artifact {self.id}: {self.name} ({self.category}, {self.points}pts, Plastic: {self.is_plastic})>"

# Global Artifact Data and Instances
STANDARD_ARTIFACT_FIRST_WORDS = ["Platinum", "Ancient", "Vegan", "Blessed", "Arcturian", "Silver", "Titanium", "Gold", "Radiant", "Plastic"]
STANDARD_ARTIFACT_SECOND_WORDS = ["Lodestar", "Pyramid", "Stardust", "Shekel", "Crown", "Sword", "Moonstone", "Sepulchre", "Sphinx"]

SPECIAL_ARTIFACT_NAMES = [
    "Treasure of Polaris", "Slippers of Venus", "Radioactive Isotope", 
    "Lesser of Two Evils", "Nebula Scroll Volume 1", "Nebula Scroll Volume 2", 
    "Nebula Scroll Volume 3", "Nebula Scroll Volume 4", "Nebula Scroll Volume 5", 
    "The Black Box"
]

ALL_ARTIFACTS = []
artifact_id_counter = 1

# Create Standard Artifacts (90 total)
for first_word in STANDARD_ARTIFACT_FIRST_WORDS:
    if artifact_id_counter > 90: break
    for second_word in STANDARD_ARTIFACT_SECOND_WORDS:
        if artifact_id_counter > 90: break
        artifact_name = f"{first_word} {second_word}"
        is_plastic_artifact = (first_word.upper() == "PLASTIC")
        
        # Simplified base points for demonstration; actual scoring is complex
        points_val = -10 if is_plastic_artifact else 5 

        ALL_ARTIFACTS.append(Artifact(
            id=f"V{artifact_id_counter}",
            name=artifact_name,
            points=points_val,
            is_plastic=is_plastic_artifact,
            category="Standard"
        ))
        artifact_id_counter += 1

# Create Special Artifacts (10 total, ensuring artifact_id_counter continues to 100)
# Points for special artifacts also vary. Using placeholder values.
special_points = {
    "Treasure of Polaris": 20, "Slippers of Venus": 10, "Radioactive Isotope": -30,
    "Lesser of Two Evils": -15, "Nebula Scroll Volume 1": 0, "Nebula Scroll Volume 2": 0,
    "Nebula Scroll Volume 3": 0, "Nebula Scroll Volume 4": 0, "Nebula Scroll Volume 5": 0,
    "The Black Box": 0 
}
for name in SPECIAL_ARTIFACT_NAMES:
    if artifact_id_counter > 100: break # Should be exactly 10 for 100 total
    ALL_ARTIFACTS.append(Artifact(
        id=f"V{artifact_id_counter}",
        name=name,
        points=special_points.get(name, 0),
        is_plastic=False, # None of the specials are plastic
        category="Special"
    ))
    artifact_id_counter += 1


# Order Classes

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, username, password, is_admin: bool = False): # Added is_admin
        self.id = username # For Flask-Login, id should be a string
        self.username = username
        self.is_admin = is_admin # New attribute
        self.password_hash = generate_password_hash(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

users_db = {} # In-memory user store {username: UserObject}

@login_manager.user_loader
def load_user(user_id): # user_id is username here
    return users_db.get(user_id)


class Order:
    """Base class for player orders."""
    def __init__(self, order_type: str, priority: int):
        self.order_type = order_type
        self.priority = priority

class MoveOrder(Order):
    """Represents a fleet movement order."""
    def __init__(self, fleet_id: int, target_world_ids: list[int]):
        super().__init__(order_type="MOVE", priority=60)
        self.fleet_id = fleet_id
        self.target_world_ids = target_world_ids

class TransferOrder(Order):
    """Represents a ship transfer order."""
    def __init__(self, ship_count: int, from_entity_type: str, from_id: int, to_entity_type: str, to_id: int):
        super().__init__(order_type="TRANSFER", priority=20)
        self.ship_count = ship_count
        self.from_entity_type = from_entity_type
        self.from_id = from_id
        self.to_entity_type = to_entity_type
        self.to_id = to_id

class LoadCargoOrder(Order):
    """Represents an order to load cargo (metal) onto a fleet."""
    def __init__(self, fleet_id: int, world_id: int, metal_amount: int):
        super().__init__(order_type="LOAD_CARGO", priority=40)
        self.fleet_id = fleet_id
        self.world_id = world_id
        self.metal_amount = metal_amount

class UnloadCargoOrder(Order):
    """Represents an order to unload cargo (metal) from a fleet."""
    def __init__(self, fleet_id: int, world_id: int, metal_amount: int, as_consumer_goods: bool = False):
        super().__init__(order_type="UNLOAD_CARGO", priority=10)
        self.fleet_id = fleet_id
        self.world_id = world_id
        self.metal_amount = metal_amount
        self.as_consumer_goods = as_consumer_goods


def stream_fleet(fleet):
    return render_template('fleet.html', fleet=fleet)


# string that renders a world object using jinja2
def stream_world(world):
    return render_template('world.html', world=world)


# string that renders a player object using jinja2
def stream_player(player):
    return render_template('player.html', player=player)


# The old artifact_first_names, artifact_second_names, and artifact_list are now replaced by ALL_ARTIFACTS.

def connect_all_worlds(worlds: list[World], min_connections_per_world: int = 1, avg_connections_per_world: int = 3):
    """
    Connects all worlds in the provided list to ensure a connected graph,
    then adds more connections to meet average and minimums.
    """
    if not worlds:
        return

    num_worlds = len(worlds)

    # --- a. Ensure Basic Connectivity (Spanning Tree) ---
    # Initialize all worlds with empty connections (already done in World.__init__)
    for world in worlds:
        world.connections = []

    connected_set = set()
    unconnected_set = set(worlds)
    
    # Start with the first world
    start_world = worlds[0]
    connected_set.add(start_world)
    unconnected_set.remove(start_world)

    while unconnected_set:
        w1 = random.choice(list(connected_set)) # Pick a random world from the connected set
        w2 = random.choice(list(unconnected_set)) # Pick a random world from the unconnected set

        # Connect w1 and w2
        if w2 not in w1.connections:
            w1.connections.append(w2)
        if w1 not in w2.connections:
            w2.connections.append(w1)
        
        unconnected_set.remove(w2)
        connected_set.add(w2)

    # --- b. Add More Random Connections ---
    # Calculate current number of unique edges
    current_edges = 0
    for world in worlds:
        current_edges += len(world.connections)
    current_edges //= 2 # Each edge is counted twice

    desired_total_edges = (num_worlds * avg_connections_per_world) / 2
    
    # Max attempts to prevent infinite loop if graph becomes too dense to easily find new connections
    max_attempts_b = num_worlds * num_worlds 
    attempts_b = 0

    while current_edges < desired_total_edges and attempts_b < max_attempts_b:
        w_a = random.choice(worlds)
        w_b = random.choice(worlds)
        attempts_b +=1

        if w_a is not w_b and w_b not in w_a.connections:
            w_a.connections.append(w_b)
            w_b.connections.append(w_a)
            current_edges += 1
        
    # --- c. Ensure Minimum Connections ---
    max_attempts_c_world = num_worlds * 10 # Max attempts per world to find new connections

    for world in worlds:
        attempts_c_this_world = 0
        while len(world.connections) < min_connections_per_world and attempts_c_this_world < max_attempts_c_world :
            attempts_c_this_world +=1
            # Pick a random other world
            other_world = random.choice(worlds)
            
            if world is not other_world and other_world not in world.connections:
                world.connections.append(other_world)
                other_world.connections.append(world)
            
            if attempts_c_this_world >= max_attempts_c_world:
                print(f"Warning: Max attempts reached for world {world.id} to meet min connections. Current: {len(world.connections)}")


# Old create_worlds, connect_worlds, create_fleets are removed or commented out
# as their logic is now part of the new create_game or will be handled differently.

# def create_worlds():
#     worlds = []
#     for i in range(1, 11): # Old: creates 10 worlds
#         worlds.append(
#             World(i, "World " + str(i), None, [], random.randint(1, 10), random.randint(1, 10), random.randint(1, 10),
#                   random.randint(1, 10), random.randint(1, 10), random.randint(1, 10), random.randint(1, 10), [])
#         )
#     return worlds

# def connect_worlds(worlds: []): # This might be reused or adapted later
#     max_worlds = len(worlds)
#     for i in range(0, max_worlds - 1):
#         connection_number = 1 + random.randint(1, 3)
#         for c in range(0, connection_number):
#             j = random.randint(0, max_worlds - 1)
#             if i != j:
#                 # Ensure not already connected to avoid duplicate connections
#                 if worlds[j] not in worlds[i].connections:
#                     worlds[i].connections.append(worlds[j])
#                 if worlds[i] not in worlds[j].connections:
#                     worlds[j].connections.append(worlds[i])

# def create_fleets(): # Old: creates 10 fleets
#     fleets = []
#     for i in range(1, 11):
#         fleets.append(Fleet(i, "Fleet " + str(i), 0, None, None, 0, [])) # Ensure artifacts is a list
#     return fleets


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
        self.turn_events: dict[str, list[str]] = {} # Key: player.user_id, Value: list of event message strings

    def add_turn_event(self, user_id_to_notify: str, message: str):
        if user_id_to_notify not in self.turn_events:
            self.turn_events[user_id_to_notify] = []
        self.turn_events[user_id_to_notify].append(message)

    def get_and_clear_turn_events(self, user_id: str) -> list[str]:
        events = self.turn_events.get(user_id, [])
        if user_id in self.turn_events:
            self.turn_events[user_id] = [] # Clear after retrieval
        return events

    def BuildCommand(self):
        print("Build")

    def execute_move_order(self, order: MoveOrder) -> tuple[bool, str]:
        """Executes a MoveOrder, moving a fleet along a path of worlds."""
        if not isinstance(order, MoveOrder):
            return False, "Invalid order type provided to execute_move_order."

        fleet_to_move = self.get_fleet(order.fleet_id)

        if not fleet_to_move:
            return False, f"Error: Fleet with ID {order.fleet_id} not found."

        if fleet_to_move.ships <= 0:
            return False, f"Error: Fleet {fleet_to_move.name} (ID: {order.fleet_id}) has no ships and cannot move."
        
        if not fleet_to_move.location: # Should not happen with current game setup
             return False, f"Error: Fleet {fleet_to_move.name} (ID: {order.fleet_id}) has no current location and cannot move."

        if not order.target_world_ids: # Empty list of targets
            return False, f"Error: No target worlds specified for fleet {fleet_to_move.name} (ID: {order.fleet_id})."

        if len(order.target_world_ids) > 2:
            return False, f"Error: Fleet {fleet_to_move.name} (ID: {order.fleet_id}) path too long (max 2 segments)."

        # Resolve World IDs from order.target_world_ids to World Objects
        path_world_objects = []
        for world_id in order.target_world_ids:
            if world_id is None: # Handle cases where optional second world ID might be null from JS
                if len(path_world_objects) == 0: # First world cannot be None
                     return False, f"Error: First target world ID is null for fleet {fleet_to_move.name}."
                continue # Skip if optional second world is None
            world_obj = self.get_world(world_id)
            if not world_obj:
                return False, f"Error: Target world with ID {world_id} not found in game data for fleet {fleet_to_move.name}."
            path_world_objects.append(world_obj)
        
        if not path_world_objects: # If all target_world_ids were None or list was empty
             return False, f"Error: No valid target worlds could be resolved for fleet {fleet_to_move.name}."

        current_location = fleet_to_move.location
        # The full path for validation includes the current location + resolved target world objects
        full_path_for_validation = [current_location] + path_world_objects 

        # Validate path connections
        for i in range(len(full_path_for_validation) - 1):
            world1 = full_path_for_validation[i]
            world2 = full_path_for_validation[i+1]
            
            if world2 not in world1.connections and world1 not in world2.connections: # Assuming connections are two-way
                return False, f"Error: World {world1.name} (ID: {world1.id}) is not connected to {world2.name} (ID: {world2.id})."
        
        # Movement Logic
        final_destination_world = path_world_objects[-1] # The last valid world in the resolved target path

        # Simulate passing through intermediate worlds (for future hostile fleet interactions)
        for i in range(len(path_world_objects)):
            intermediate_world_object = path_world_objects[i]
            
            # Check if this is an intermediate stop (not the final destination of this move order)
            is_intermediate_stop = (intermediate_world_object != final_destination_world)
            
            if is_intermediate_stop:
                # This world is being passed through.
                # Log event if owned by a different player.
                world_owner = intermediate_world_object.owner
                moving_fleet_owner = fleet_to_move.owner

                if world_owner and world_owner != moving_fleet_owner and world_owner.user_id:
                    event_message = (
                        f"ALERT: Your world {intermediate_world_object.name} (ID: {intermediate_world_object.id}) "
                        f"was passed through by Fleet ID: {fleet_to_move.id} "
                        f"(Name: {fleet_to_move.name}, Owner: {moving_fleet_owner.name if moving_fleet_owner else 'Unowned'})."
                    )
                    self.add_turn_event(world_owner.user_id, event_message)
                    print(f"Event for {world_owner.user_id}: {event_message}") # Server log for event
            
        fleet_to_move.location = final_destination_world
        msg = f"Fleet {fleet_to_move.name} (ID: {order.fleet_id}) moved to {final_destination_world.name} (ID: {final_destination_world.id})."
        # print(msg) # Server log
        return True, msg

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

    # Helper methods for entity resolution
    def get_fleet(self, fleet_id: int) -> Fleet | None:
        """Retrieves a fleet by its ID."""
        return next((f for f in self.fleets if f.id == fleet_id), None)

    def get_world(self, world_id: int) -> World | None:
        """Retrieves a world by its ID."""
        return next((w for w in self.worlds if w.id == world_id), None)

    def get_visible_worlds_for_player(self, current_player: Player) -> list[World]:
        if not current_player: # Or if current_player is an admin with no game entity
            return [] # Or handle as appropriate for non-participating users

        visible_worlds = set() # Use a set to avoid duplicates

        # 1. Worlds owned by the player
        for world in self.worlds: # Iterate all worlds in the game
            if world.owner == current_player: # Direct object comparison
                visible_worlds.add(world)

        # 2. Worlds where any of the player's fleets are located
        for fleet in self.fleets: # Iterate all fleets in the game
            if fleet.owner == current_player and fleet.location:
                visible_worlds.add(fleet.location)
       
        return list(visible_worlds)

    def get_visible_fleets_for_player(self, current_player: Player) -> list[Fleet]:
        if not current_player:
            return []

        visible_fleets_set = set() # Use a set to avoid duplicates
       
        # Prepare sets of world IDs relevant to the current player for efficient lookup
        player_owned_world_ids = {world.id for world in self.worlds if world.owner == current_player}
        
        player_fleet_location_ids = set()
        for p_fleet in self.fleets: # Iterate all fleets to find current player's fleet locations
            if p_fleet.owner == current_player and p_fleet.location:
                player_fleet_location_ids.add(p_fleet.location.id)

        for fleet_to_check in self.fleets: # Iterate all fleets in the game
            # Rule 0: Player always sees their own fleets
            if fleet_to_check.owner == current_player:
                visible_fleets_set.add(fleet_to_check)
                continue

            # Rules for seeing other players' fleets:
            if fleet_to_check.location: # Fleet must have a location
                # Rule 1: Player A owns the world where Player B's fleet is located
                if fleet_to_check.location.id in player_owned_world_ids:
                    visible_fleets_set.add(fleet_to_check)
                    continue
               
                # Rule 3: Player A's fleet is at the same world as Player B's fleet
                if fleet_to_check.location.id in player_fleet_location_ids:
                    visible_fleets_set.add(fleet_to_check)
                    continue
       
        return list(visible_fleets_set)

    def execute_transfer_order(self, order: TransferOrder) -> tuple[bool, str]:
        """Executes a TransferOrder, moving ships between entities."""
        if not isinstance(order, TransferOrder):
            return False, "Invalid order type provided to execute_transfer_order."

        if order.ship_count <= 0:
            return False, "Ship count for transfer must be positive."

        from_type = order.from_entity_type.upper()
        to_type = order.to_entity_type.upper()

        # --- Scenario A: Fleet to Fleet ---
        if from_type == "FLEET" and to_type == "FLEET":
            source_fleet = self.get_fleet(order.from_id)
            target_fleet = self.get_fleet(order.to_id)

            if not source_fleet:
                return False, f"Source fleet with ID {order.from_id} not found."
            if not target_fleet:
                return False, f"Target fleet with ID {order.to_id} not found."
            if source_fleet.location != target_fleet.location:
                return False, f"Fleets {source_fleet.name} and {target_fleet.name} are not in the same location."
            if source_fleet.ships < order.ship_count:
                return False, f"Source fleet {source_fleet.name} has insufficient ships ({source_fleet.ships} < {order.ship_count})."
            
            # Ownership check
            if source_fleet.owner and target_fleet.owner and source_fleet.owner is not target_fleet.owner:
                return False, f"Ownership mismatch: Source fleet {source_fleet.name} owned by {source_fleet.owner.name}, target fleet {target_fleet.name} owned by {target_fleet.owner.name}."

            # Cargo rule
            if source_fleet.cargo > 0:
                source_fleet.cargo = 0 # Cargo jettisoned

            source_fleet.ships -= order.ship_count
            target_fleet.ships += order.ship_count
            return True, f"Successfully transferred {order.ship_count} ships from fleet {source_fleet.name} to fleet {target_fleet.name}."

        # --- Scenario B: Fleet to PSHIPS/ISHIPS ---
        elif from_type == "FLEET" and (to_type == "PSHIP" or to_type == "ISHIP"):
            source_fleet = self.get_fleet(order.from_id)
            target_world = self.get_world(order.to_id) # to_id is world_id here

            if not source_fleet:
                return False, f"Source fleet with ID {order.from_id} not found."
            if not target_world:
                return False, f"Target world with ID {order.to_id} not found."
            if source_fleet.location != target_world:
                return False, f"Fleet {source_fleet.name} is not at world {target_world.name}."
            if source_fleet.ships < order.ship_count:
                return False, f"Source fleet {source_fleet.name} has insufficient ships ({source_fleet.ships} < {order.ship_count})."

            # Ownership check
            if source_fleet.owner and target_world.owner and source_fleet.owner is not target_world.owner:
                 return False, f"Ownership mismatch: Source fleet {source_fleet.name} owned by {source_fleet.owner.name}, target world {target_world.name} owned by {target_world.owner.name}."


            # Cargo rule
            if source_fleet.cargo > 0:
                source_fleet.cargo = 0 # Cargo jettisoned
            
            source_fleet.ships -= order.ship_count
            if to_type == "PSHIP":
                target_world.pships += order.ship_count
                return True, f"Successfully transferred {order.ship_count} ships from fleet {source_fleet.name} to PSHIPS at world {target_world.name}."
            else: # ISHIP
                target_world.iships += order.ship_count
                return True, f"Successfully transferred {order.ship_count} ships from fleet {source_fleet.name} to ISHIPS at world {target_world.name}."

        # --- Scenario C: PSHIPS/ISHIPS to Fleet ---
        elif (from_type == "PSHIP" or from_type == "ISHIP") and to_type == "FLEET":
            source_world = self.get_world(order.from_id) # from_id is world_id here
            target_fleet = self.get_fleet(order.to_id)

            if not source_world:
                return False, f"Source world with ID {order.from_id} not found."
            if not target_fleet:
                return False, f"Target fleet with ID {order.to_id} not found."
            if target_fleet.location != source_world:
                return False, f"Fleet {target_fleet.name} is not at world {source_world.name}."

            # Ownership check
            if source_world.owner and target_fleet.owner and source_world.owner is not target_fleet.owner:
                return False, f"Ownership mismatch: Source world {source_world.name} owned by {source_world.owner.name}, target fleet {target_fleet.name} owned by {target_fleet.owner.name}."

            if from_type == "PSHIP":
                if source_world.pships < order.ship_count:
                    return False, f"Source world {source_world.name} has insufficient PSHIPS ({source_world.pships} < {order.ship_count})."
                source_world.pships -= order.ship_count
            else: # ISHIP
                if source_world.iships < order.ship_count:
                    return False, f"Source world {source_world.name} has insufficient ISHIPS ({source_world.iships} < {order.ship_count})."
                source_world.iships -= order.ship_count
            
            target_fleet.ships += order.ship_count
            return True, f"Successfully transferred {order.ship_count} {from_type.lower()}s from world {source_world.name} to fleet {target_fleet.name}."

        # --- Scenario D: PSHIPS to ISHIPS (or vice-versa) at the same world ---
        elif (from_type == "PSHIP" and to_type == "ISHIP") or \
             (from_type == "ISHIP" and to_type == "PSHIP"):
            if order.from_id != order.to_id:
                return False, "PSHIPS and ISHIPS transfers must occur at the same world (from_id must equal to_id)."
            
            world = self.get_world(order.from_id)
            if not world:
                return False, f"World with ID {order.from_id} not found for PSHIP/ISHIP transfer."

            # Ownership check (world must be owned by the player or unowned)
            # Since there's no explicit player_id on the order, we just check if the world is owned.
            # The rule "Make sure that a key or world is ALREADY listed as belonging to YOU" implies
            # that if it's owned, it must be by the current player. This is a simplification.
            # For PSHIP <-> ISHIP, only one world is involved, so no source/target ownership conflict.

            if from_type == "PSHIP": # PSHIP to ISHIP
                if world.pships < order.ship_count:
                    return False, f"World {world.name} has insufficient PSHIPS ({world.pships} < {order.ship_count})."
                world.pships -= order.ship_count
                world.iships += order.ship_count
                return True, f"Successfully transferred {order.ship_count} PSHIPS to ISHIPS at world {world.name}."
            else: # ISHIP to PSHIP
                if world.iships < order.ship_count:
                    return False, f"World {world.name} has insufficient ISHIPS ({world.iships} < {order.ship_count})."
                world.iships -= order.ship_count
                world.pships += order.ship_count
                return True, f"Successfully transferred {order.ship_count} ISHIPS to PSHIPS at world {world.name}."

        else:
            return False, f"Invalid or unsupported transfer entity type combination: from '{from_type}' to '{to_type}'."

    def execute_unload_cargo_order(self, order: UnloadCargoOrder) -> tuple[bool, str]:
        """Executes an UnloadCargoOrder, moving metal from a fleet to a world or as consumer goods."""
        if not isinstance(order, UnloadCargoOrder):
            return False, "Invalid order type provided to execute_unload_cargo_order."

        fleet = self.get_fleet(order.fleet_id)
        world = self.get_world(order.world_id)

        if not fleet:
            return False, f"Fleet with ID {order.fleet_id} not found."
        if not world:
            return False, f"World with ID {order.world_id} not found."
        if fleet.location != world:
            return False, f"Fleet {fleet.name} (ID: {order.fleet_id}) is not at world {world.name} (ID: {order.world_id})."

        # Ownership check: if both have owners, they must match.
        if fleet.owner and world.owner and fleet.owner is not world.owner:
            return False, f"Ownership mismatch: Fleet {fleet.name} (ID: {order.fleet_id}) owned by {fleet.owner.name if fleet.owner else 'N/A'}, World {world.name} (ID: {order.world_id}) owned by {world.owner.name if world.owner else 'N/A'}."
        
        amount_to_unload: int
        if order.metal_amount == -1: # Unload all
            amount_to_unload = fleet.cargo
        else:
            amount_to_unload = order.metal_amount

        if amount_to_unload < 0:
            return False, "Cannot unload a negative amount of metal."
        if amount_to_unload > fleet.cargo:
            return False, f"Fleet {fleet.name} (ID: {order.fleet_id}) has insufficient cargo to unload {amount_to_unload} (has {fleet.cargo})."

        fleet.cargo -= amount_to_unload
        msg_action = ""

        if not order.as_consumer_goods:
            # TODO: Consider timing issues if metal is also used for building in the same turn.
            world.stockpile += amount_to_unload
            msg_action = f"to stockpile at world {world.name} (ID: {order.world_id})."
        else:
            msg_action = f"as consumer goods at world {world.name} (ID: {order.world_id})."
        
        msg = f"Successfully unloaded {amount_to_unload} metal from fleet {fleet.name} (ID: {order.fleet_id}) {msg_action}"
        # print(msg) # Server log
        return True, msg

    def execute_load_cargo_order(self, order: LoadCargoOrder) -> tuple[bool, str]:
        """Executes a LoadCargoOrder, moving metal from a world's stockpile to a fleet."""
        if not isinstance(order, LoadCargoOrder):
            return False, "Invalid order type provided to execute_load_cargo_order."

        fleet = self.get_fleet(order.fleet_id)
        world = self.get_world(order.world_id)

        if not fleet:
            return False, f"Fleet with ID {order.fleet_id} not found."
        if not world:
            return False, f"World with ID {order.world_id} not found."
        if fleet.location != world:
            return False, f"Fleet {fleet.name} (ID: {order.fleet_id}) is not at world {world.name} (ID: {order.world_id})."

        # Ownership for loading: Fleet owner must match world owner, OR world must be unowned.
        # TODO: Implement full "loader" status permissions for loading from non-owned worlds.
        if world.owner and (not fleet.owner or fleet.owner is not world.owner):
            return False, f"Fleet {fleet.name} (ID: {order.fleet_id}, owner: {fleet.owner.name if fleet.owner else 'N/A'}) cannot load from world {world.name} (ID: {order.world_id}, owner: {world.owner.name if world.owner else 'N/A'}) without loader status or matching ownership."
        
        is_merchant = False
        if fleet.owner and fleet.owner.character_type == "Merchant":
            is_merchant = True
        
        max_cargo_capacity = fleet.ships * (2 if is_merchant else 1)
        can_load_more = max_cargo_capacity - fleet.cargo
        if can_load_more < 0: can_load_more = 0 

        if can_load_more == 0 and order.metal_amount != 0 :
             return False, f"Fleet {fleet.name} (ID: {order.fleet_id}) is already full (capacity: {max_cargo_capacity}, current: {fleet.cargo})."

        amount_to_load: int
        if order.metal_amount == -1: # Load all possible
            amount_to_load = min(world.stockpile, can_load_more)
        else:
            amount_to_load = order.metal_amount
        
        if amount_to_load < 0:
            return False, "Cannot load a negative amount of metal."
        if amount_to_load > can_load_more:
            return False, f"Fleet {fleet.name} (ID: {order.fleet_id}) has insufficient capacity to load {amount_to_load} (can load {can_load_more} more)."
        if amount_to_load > world.stockpile:
            return False, f"World {world.name} (ID: {order.world_id}) has insufficient stockpile to load {amount_to_load} (has {world.stockpile})."

        fleet.cargo += amount_to_load
        world.stockpile -= amount_to_load
        
        msg = f"Successfully loaded {amount_to_load} metal onto fleet {fleet.name} (ID: {order.fleet_id}) from world {world.name} (ID: {order.world_id})."
        # print(msg) # Server log
        return True, msg

    def process_turn(self, user_id: str, raw_orders_list: list[dict]) -> list[str]:
        """Processes a list of raw order dictionaries for a turn, for a given user."""
        print(f"Processing turn for user: {user_id}") # Log the user processing the turn
        
        typed_orders: list[Order] = []
        for order_dict in raw_orders_list:
            order_obj = order_from_dict(order_dict) # Uses the global helper
            if order_obj:
                typed_orders.append(order_obj)
            else:
                print(f"Warning: Could not create order from dict: {order_dict}")

        typed_orders.sort(key=lambda o: o.priority)

        results_messages: list[str] = []
        for order_obj in typed_orders:
            success = False
            message = "Unknown order type or execution error."
            # Dispatch to the correct execute_* method based on order_type
            if order_obj.order_type == "MOVE":
                success, message = self.execute_move_order(order_obj)
            elif order_obj.order_type == "TRANSFER":
                success, message = self.execute_transfer_order(order_obj)
            elif order_obj.order_type == "LOAD_CARGO":
                success, message = self.execute_load_cargo_order(order_obj)
            elif order_obj.order_type == "UNLOAD_CARGO":
                success, message = self.execute_unload_cargo_order(order_obj)
            
            results_messages.append(f"Order ({order_obj.order_type} P{order_obj.priority}): {message} (Success: {success})")
        
        return results_messages


# Global helper function
def order_from_dict(order_dict: dict) -> Order | None:
    """Creates an Order subclass instance from a dictionary."""
    order_type = order_dict.get('order_type')
    
    # Prepare data by removing 'order_type' for **kwargs to pass to constructors
    # This assumes constructor parameters match dictionary keys.
    data = {k: v for k, v in order_dict.items() if k != 'order_type'}

    try:
        if order_type == "MOVE":
            # Ensure target_world_ids is a list and contains only non-null integers
            raw_ids = data.get('target_world_ids', [])
            if not isinstance(raw_ids, list): # Should be a list from JS
                print(f"Warning: 'target_world_ids' for MOVE order is not a list: {raw_ids}")
                return None
            
            # Filter out None values which might come from optional second world ID if not provided
            # And ensure all are integers
            processed_ids = []
            for world_id in raw_ids:
                if world_id is not None:
                    try:
                        processed_ids.append(int(world_id))
                    except (ValueError, TypeError):
                        print(f"Warning: Invalid world ID '{world_id}' in MOVE order.")
                        return None # Invalid ID type
            data['target_world_ids'] = processed_ids
            if not data['target_world_ids']: # If list becomes empty after processing
                 print(f"Warning: No valid target world IDs for MOVE order after processing: {raw_ids}")
                 return None
            return MoveOrder(**data)
        elif order_type == "TRANSFER":
            return TransferOrder(**data)
        elif order_type == "LOAD_CARGO":
            return LoadCargoOrder(**data)
        elif order_type == "UNLOAD_CARGO":
            return UnloadCargoOrder(**data)
        else:
            print(f"Warning: Unknown order type '{order_type}' in order_from_dict.")
            return None
    except TypeError as e:
        # This catches errors if dict keys don't match constructor args
        print(f"Error creating order {order_type} from dict {data}: {e}")
        return None
    except Exception as e: # Catch any other unexpected error during instantiation
        print(f"Unexpected error creating order {order_type} from dict {data}: {e}")
        return None


def create_game():
    # --- create_game() Refactored for Large Universe ---
    
    new_game = Game(worlds=[], fleets=[], players=[]) # Initialize with empty lists

    # Create 255 Worlds
    for i in range(1, 256): # Worlds W1 to W255
        world = World(
            id=i,
            name=f"World {i}",
            owner=None, # Initially unowned
            connections=[], # Connections can be established later if needed
            iships=0,
            pships=0,
            population=random.randint(0, 20),
            max_population=random.randint(50, 150),
            industry=random.randint(0, 5),
            mines=random.randint(0, 3),
            stockpile=random.randint(0, 50),
            artifacts=[] # Initialized as empty list
        )
        new_game.worlds.append(world)

    # Connect the worlds
    connect_all_worlds(new_game.worlds) # Call the new connection logic

    # Distribute 100 Artifacts
    if ALL_ARTIFACTS and new_game.worlds: # Ensure there are artifacts and worlds
        shuffled_artifacts = list(ALL_ARTIFACTS)
        random.shuffle(shuffled_artifacts)

        for artifact_instance in shuffled_artifacts:
            chosen_world = random.choice(new_game.worlds)
            chosen_world.artifacts.append(artifact_instance)
    
    # Create 255 Unowned Fleets at Random Locations
    for i in range(1, 256): # Fleets F1 to F255
        if not new_game.worlds: # Should not happen if worlds were created
            initial_location_world = None
        else:
            initial_location_world = random.choice(new_game.worlds)
        
        fleet = Fleet(
            id=i,
            name=f"Fleet {i}",
            ships=0, # All fleets start with 0 ships
            location=initial_location_world,
            owner=None, # Initially unowned
            cargo=0,
            artifacts=[] # Initialized as empty list
        )
        new_game.fleets.append(fleet)

    # Player creation and assignment logic is removed for now,
    # as this setup is for a large, initially unowned universe.
    # new_game.players will remain empty or be handled by a separate mechanism.
    # The old player assignment logic from previous create_game is omitted here.

    return new_game


def get_or_create_game():
    global game
    if game is None:
        game = create_game()
    return game

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/game')
@login_required # Protect this route
def display_game():
    game_instance = get_or_create_game()
    current_player_ingame = None
    player_turn_events = [] # Initialize here

    if current_user.is_authenticated: # current_user is from flask_login
        # Find the in-game Player object linked to the logged-in User
        current_player_ingame = next((p for p in game_instance.players if p.user_id == current_user.id), None)
        # Get and clear events for the current logged-in user
        player_turn_events = game_instance.get_and_clear_turn_events(current_user.id)


    worlds_to_display = []
    fleets_to_display = []
    is_admin_view = False

    if current_user.is_authenticated and current_user.is_admin:
        worlds_to_display = game_instance.worlds
        fleets_to_display = game_instance.fleets
        is_admin_view = True
        # flash("Displaying full galaxy view (Admin).", "info") # Already flashed by login or other actions
    elif current_player_ingame: # Regular player who is set up in the game
        worlds_to_display = game_instance.get_visible_worlds_for_player(current_player_ingame)
        fleets_to_display = game_instance.get_visible_fleets_for_player(current_player_ingame)
        # flash("Displaying your known galaxy view.", "info")
    else:
        # Logged in, but not an admin and not set up as a player in the game 
        # (e.g., registered but game was reset, or admin who isn't playing)
        # Or, if a user somehow gets here without being fully set up.
        if current_user.is_authenticated: # Avoid flashing if not logged in at all (though @login_required should prevent this)
            flash("You are logged in, but not currently an active player in this game. Displaying limited or no view.", "warning")
        # worlds_to_display and fleets_to_display remain empty

    return render_template('game.html', 
                            game=game_instance, # Still pass for general game info if any needed
                            current_player_ingame=current_player_ingame,
                            worlds_to_display=worlds_to_display,
                            fleets_to_display=fleets_to_display,
                            is_admin_view=is_admin_view,
                            player_turn_events=player_turn_events) # Pass events to template

@app.route('/move_fleet', methods=['POST'])
def move_fleet():
    game_instance = get_or_create_game()
    # The /move_fleet route is now obsolete as Move orders are handled by /submit_turn
    flash("The direct /move_fleet route is deprecated. Please use the 'Plan Your Turn' interface to move fleets.")
    return redirect(url_for('display_game'))

# Helper functions for registration
def assign_homeworld_to_player(player_obj: Player, game_instance: Game):
    unowned_worlds = [world for world in game_instance.worlds if world.owner is None]
    if not unowned_worlds:
        # This should not happen in a new game with 255 worlds and few players
        raise Exception("No unowned worlds available for new player!") 
    
    selected_homeworld = random.choice(unowned_worlds) # random.choice
    
    selected_homeworld.owner = player_obj
    selected_homeworld.name = f"{player_obj.name}'s Homeworld" # Rename for clarity
    selected_homeworld.population = 50
    selected_homeworld.max_population = 100
    selected_homeworld.industry = 30
    selected_homeworld.mines = 2
    selected_homeworld.stockpile = 30
    selected_homeworld.iships = 1
    selected_homeworld.pships = 1
    # selected_homeworld.turns_owned = 1 # If 'turns_owned' attribute exists
    # Ensure connections made by connect_all_worlds are preserved.
    
    player_obj.home_world = selected_homeworld
    if selected_homeworld not in player_obj.worlds:
        player_obj.worlds.append(selected_homeworld)
    
    print(f"Homeworld {selected_homeworld.name} (ID: {selected_homeworld.id}) assigned to player {player_obj.name}.")
    return selected_homeworld

def assign_starting_fleets_to_player(player_obj: Player, game_instance: Game):
    if not player_obj.home_world:
        raise Exception(f"Player {player_obj.name} has no homeworld to assign fleets to.")

    unowned_fleets = [fleet for fleet in game_instance.fleets if fleet.owner is None]
    
    # Ensure there are enough unowned fleets; create more if necessary (though create_game should make plenty)
    fleets_to_assign_count = 5
    if len(unowned_fleets) < fleets_to_assign_count:
        print(f"Warning: Not enough unowned fleets ({len(unowned_fleets)} found) for new player {player_obj.name}. Need {fleets_to_assign_count}.")
        # Optionally create more fleets here if this is a possible scenario.
        # For now, we'll assign as many as possible.
        fleets_to_assign_count = len(unowned_fleets)
        if fleets_to_assign_count == 0:
            print(f"No unowned fleets to assign to player {player_obj.name}")
            return # No fleets to assign

    starting_fleets_assigned = 0
    for i in range(fleets_to_assign_count):
        fleet_to_assign = unowned_fleets[i] 
        fleet_to_assign.owner = player_obj
        fleet_to_assign.location = player_obj.home_world
        fleet_to_assign.ships = 0 # Explicitly ensure 0 ships
        fleet_to_assign.name = f"{player_obj.name}'s Fleet {starting_fleets_assigned + 1}" # Rename for clarity
        if fleet_to_assign not in player_obj.fleets:
            player_obj.fleets.append(fleet_to_assign)
        starting_fleets_assigned +=1
    
    print(f"{starting_fleets_assigned} starting fleets assigned to player {player_obj.name} at {player_obj.home_world.name}.")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # character_type is retrieved later, only if not admin

        if not username or not password or not confirm_password: # Character type not mandatory at this stage of validation
            flash('Username, password, and password confirmation are required!', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        if username in users_db:
            flash('Username already exists. Please choose a different one.', 'warning')
            return redirect(url_for('register'))

        is_admin_user = False
        if username.lower() == "admin": # Temporary: specific username becomes admin
            is_admin_user = True
            flash("Admin user registration recognized.", "info")
        
        new_user = User(username=username, password=password, is_admin=is_admin_user)
        users_db[username] = new_user
        
        game_instance = get_or_create_game() # Ensure game instance is available
        ingame_player = None # Initialize

        if not is_admin_user:
            character_type = request.form.get('character_type')
            if not character_type:
                flash('Character type is required for players!', 'danger')
                users_db.pop(username, None) # Clean up created User
                return redirect(url_for('register'))
            
            if character_type not in character_types:
                flash('Invalid character type selected!', 'danger')
                users_db.pop(username, None) # Clean up created User
                return redirect(url_for('register'))

            # Check if this user_id (username) already has an in-game Player object.
            # This check is more robust if a user account might exist without a player object yet.
            existing_player_for_user = next((p for p in game_instance.players if p.user_id == new_user.id), None)
            if existing_player_for_user:
                flash(f'User {new_user.username} already has a player character in this game. Cannot create another.', 'warning')
                # If user exists but player setup failed previously, this path might need review.
                # For now, we assume this is an error state if reached.
                # users_db.pop(username, None) # Might be too aggressive if user is just re-registering
                return redirect(url_for('register'))
            
            ingame_player = Player(name=new_user.username,
                                   character_type=character_type,
                                   user_id=new_user.id)
            game_instance.players.append(ingame_player)

            try:
                assign_homeworld_to_player(ingame_player, game_instance)
                assign_starting_fleets_to_player(ingame_player, game_instance)
                flash(f'Player {ingame_player.name} ({character_type}) created. Homeworld and fleets assigned. Please login.', 'success')
            except Exception as e:
                flash(f'User {new_user.username} created, but error setting up player in game: {e}. Please contact admin.', 'danger')
                # Clean up: remove player from game and user from users_db
                if ingame_player and ingame_player in game_instance.players:
                    game_instance.players.remove(ingame_player)
                users_db.pop(username, None)
                return redirect(url_for('register'))
        elif is_admin_user:
            flash(f'Admin user {new_user.username} registered. No in-game player entity created. Please login.', 'info')

        return redirect(url_for('login'))

    return render_template('register.html', character_types=character_types)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('display_game')) # Or a dashboard route

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users_db.get(username) # users_db is global

        if user and user.check_password(password): # User class has check_password
            login_user(user) # Create session
            flash('Logged in successfully!', 'success')
            # Redirect to the page user was trying to access, or a default
            next_page = request.args.get('next')
            return redirect(next_page or url_for('display_game'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/submit_turn', methods=['POST'])
@login_required # Protect this route
def submit_turn():
    game_instance = get_or_create_game()
    orders_json_str = request.form.get('orders_json')

    if not orders_json_str:
        flash("Error: No orders received.")
        return redirect(url_for('display_game'))

    try:
        raw_orders_list = json.loads(orders_json_str)
        if not isinstance(raw_orders_list, list):
            flash("Error: Orders format is invalid (not a list).")
            return redirect(url_for('display_game'))
    except json.JSONDecodeError:
        flash("Error: Could not decode orders JSON.")
        return redirect(url_for('display_game'))

    results_messages = game_instance.process_turn(current_user.id, raw_orders_list) # Pass current_user.id

    for msg in results_messages:
        flash(msg) # Flash individual detailed messages
    
    if not results_messages and raw_orders_list : # If orders were submitted but none were processed (e.g. all malformed)
        flash("Orders submitted, but no valid orders were processed successfully.")
    elif not raw_orders_list: # If an empty list of orders was submitted
         flash("No orders were submitted in the turn plan.")

    return redirect(url_for('display_game'))

@app.route('/logout')
@login_required # Ensures only logged-in users can access logout
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login')) # Or url_for('hello_world') or another public page


if __name__ == '__main__':
    app.wsgi_app = StarWeb(app.wsgi_app)
    app.run()
