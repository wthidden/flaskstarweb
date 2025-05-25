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
                 artifacts: list['Artifact'] | None = None, # Type hint for artifacts
                 turns_owned: int = 0, is_black_hole: bool = False,
                 robot_units: int = 0, convert_units: int = 0, converts_owner_id: str | None = None): 
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
        self.turns_owned = turns_owned
        self.is_black_hole = is_black_hole
        self.robot_units = robot_units
        self.convert_units = convert_units
        self.converts_owner_id = converts_owner_id


class Fleet:
    """This is a docstring for the Fleet class"""

    def __init__(self, id, name, ships: int, location: World | None, owner: 'Player | None', 
                 cargo: int, artifacts: list['Artifact'] | None = None, # Type hint for artifacts
                 is_at_peace: bool = False): 
        self.id = id
        self.name = name
        self.ships = ships
        self.location: World | None = location
        self.owner: Player | None = owner
        self.cargo = cargo
        self.artifacts: list[Artifact] = artifacts if artifacts is not None else []
        self.is_at_peace = is_at_peace

    def get_max_cargo_capacity(self) -> int:
        """Calculates max cargo based on ship count and owner type."""
        if self.owner and self.owner.character_type == "Merchant":
            return self.ships * 2
        return self.ships * 1 # Default for non-Merchants or unowned fleets


class EmpireBuilder:
    """This is a docstring for the EmpireBuilder class"""

    def __init__(self, player: 'Player'):
        self.player = player
        # Future special powers:
        # - Build cost reductions
        # - Faster Terraforming / Population Growth

    def calculate_victory_points(self, game: 'Game') -> int:
        """
        EmpireBuilder VPs:
        - 1 point per 10 population controlled.
        - 1 point per industry controlled.
        - 1 point per mine controlled.
        """
        vp = 0
        total_population = 0
        total_industry = 0
        total_mines = 0

        for world in self.player.worlds:
            if world.owner == self.player: # Ensure the world is still owned by the player
                total_population += world.population
                total_industry += world.industry
                total_mines += world.mines
        
        vp += total_population // 10
        vp += total_industry
        vp += total_mines
        return vp


class Merchant:
    """This is a docstring for the Merchant class"""

    def __init__(self, player: 'Player'):
        self.player = player
        # Future special powers:
        # - Trade bonuses
        # - Access to special markets/items

    def calculate_victory_points(self, game: 'Game') -> int:
        """
        Merchant VPs:
        - Return 0 for now (Action-based VPs will be implemented later).
        """
        return 0


class Pirate:
    """This is a docstring for the Pirate class"""

    def __init__(self, player: 'Player'):
        self.player = player
        # Future special powers:
        # - Ambush bonuses
        # - Ability to demand tribute

    def calculate_victory_points(self, game: 'Game') -> int:
        """
        Pirate VPs:
        - 3 points per Fleet owned.
        """
        vp = 0
        vp += len(self.player.fleets) * 3
        return vp


class ArtifactCollector:
    """This is a docstring for the ArtifactCollector class"""

    def __init__(self, player: 'Player'):
        self.player = player
        # Future special powers:
        # - Better artifact identification/analysis
        # - Bonuses for specific artifact sets

    def calculate_victory_points(self, game: 'Game') -> int:
        """
        ArtifactCollector VPs:
        - "Ancient" or "Pyramid" (non-Plastic): +30 points each.
        - "Ancient Pyramid": +90 points.
        - Other standard non-plastic artifacts: +15 points each.
        - Plastic artifacts: +0 points.
        - "Treasure of Polaris", "Slippers of Venus", "Radioactive Isotope", 
          "Lesser of Two Evils", "The Black Box": +30 points each.
        """
        vp = 0
        
        # Collect all artifacts owned by the player from their worlds and fleets
        owned_artifacts: list[Artifact] = []
        for world in self.player.worlds:
            if world.owner == self.player:
                owned_artifacts.extend(world.artifacts)
        for fleet in self.player.fleets:
            if fleet.owner == self.player:
                owned_artifacts.extend(fleet.artifacts)

        for artifact in owned_artifacts:
            if artifact.name == "Ancient Pyramid": # Specific check for "Ancient Pyramid"
                vp += 90
            elif artifact.category == "Standard":
                if artifact.is_plastic:
                    vp += 0 # Explicitly 0 for plastic
                elif artifact.first_word == "Ancient" or artifact.second_word == "Pyramid":
                    # This covers "Ancient X" or "X Pyramid" that are not "Ancient Pyramid"
                    vp += 30
                else:
                    # Other standard non-plastic artifacts
                    vp += 15
            elif artifact.category == "Special":
                # Specific list of special artifacts for +30 VP
                if artifact.name in [
                    "Treasure of Polaris", "Slippers of Venus", 
                    "Radioactive Isotope", "Lesser of Two Evils", "The Black Box"
                ]:
                    vp += 30
                # Nebula Scrolls and other special artifacts not in the list give VP based on their points attribute (usually 0 unless set otherwise)
                # or through other game mechanics (like set collection for Nebula Scrolls).
                # For now, we only add for the explicitly listed ones.
                # The problem description only lists these 5 for +30 VP.
        return vp


class Berserker:
    """This is a docstring for the Berserker class"""

    def __init__(self, player: 'Player'):
        self.player = player
        # Future special powers:
        # - Combat bonuses when outnumbered
        # - Resistance to certain types of damage

    def calculate_victory_points(self, game: 'Game') -> int:
        """
        Berserker VPs:
        - 5 points per world in self.player.worlds where robot_units > 0 and 
          population == 0 and convert_units == 0.
        """
        vp = 0
        for world in self.player.worlds:
            if world.owner == self.player: # Ensure player owns the world
                if world.robot_units > 0 and world.population == 0 and world.convert_units == 0:
                    vp += 5
        return vp


class Player:
    def __init__(self, name: str, character_type: str, user_id: str, home_world: World | None = None, 
                 diplomacy: dict | None = None, worlds: list[World] | None = None, fleets: list[Fleet] | None = None,
                 victory_points: int = 0, allies: list[str] | None = None):
        self.name = name # Often same as User.username
        self.character_type = character_type
        self.user_id = user_id # Link to Flask-Login User.id
        self.home_world: World | None = home_world
        self.diplomacy = diplomacy if diplomacy is not None else {}
        self.worlds: list[World] = [home_world] if home_world and (worlds is None or home_world not in worlds) else (worlds if worlds is not None else [])
        if home_world and not self.worlds: # Ensure homeworld is in worlds if worlds was passed as empty or None
            self.worlds.append(home_world)
        self.fleets: list[Fleet] = fleets if fleets is not None else []
        self.victory_points = victory_points
        self.allies: list[str] = allies if allies is not None else []
        self.character = self.create_character()

    def create_character(self):
        # Assuming character classes now take the Player object itself if needed
        # For now, their constructors seem to take (self) which implies player instance methods
        # or they take specific attributes. Let's assume they are simple for now.
        # If EmpireBuilder(self) means passing the player instance, this is fine.
        if self.character_type == "Empire Builder":
            return EmpireBuilder(player=self)
        elif self.character_type == "Merchant":
            return Merchant(player=self)
        elif self.character_type == "Pirate":
            return Pirate(player=self)
        elif self.character_type == "Artifact Collector":
            return ArtifactCollector(player=self)
        elif self.character_type == "Berserker":
            return Berserker(player=self)
        elif self.character_type == "Apostle":
            return Apostle(player=self)
        else:
            return None

# Apostle Class (New)
class Apostle:
    """This is a docstring for the Apostle class"""
    def __init__(self, player: 'Player'):
        self.player = player
        # Future special powers:
        # - Convert population/units
        # - Shot penalty for fleets at worlds with friendly converts
        # - Unique 'Convert' unit type

    def calculate_victory_points(self, game: 'Game') -> int:
        """
        Apostle VPs:
        - 5 points per world in self.player.worlds.
        - 1 point per 10 convert_units summed across all game.worlds 
          where world.converts_owner_id == self.player.user_id.
        - Additional 5 points per world in self.player.worlds where 
          world.convert_units > 0 and world.population == 0 and world.robot_units == 0.
        """
        vp = 0
        
        # 5 points per world owned
        for world in self.player.worlds:
            if world.owner == self.player:
                vp += 5
                # Additional 5 points if world is fully converted by this apostle
                if world.convert_units > 0 and world.population == 0 and world.robot_units == 0 and world.converts_owner_id == self.player.user_id:
                    vp += 5

        # 1 point per 10 total convert_units attributed to this Apostle
        total_apostle_converts = 0
        for world in game.worlds: # Iterate all worlds in the game
            if world.converts_owner_id == self.player.user_id:
                total_apostle_converts += world.convert_units
        
        vp += total_apostle_converts // 10
        
        return vp

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

# As per starweb-rules.txt
SPECIAL_ARTIFACT_NAMES_AND_POINTS = {
    "Treasure of Polaris": 20,
    "Slippers of Venus": 10,
    "Radioactive Isotope": -30,
    "Lesser of Two Evils": -15,
    "Nebula Scroll Volume 1": 0, # Points for Nebula Scrolls are often related to collecting the set
    "Nebula Scroll Volume 2": 0,
    "Nebula Scroll Volume 3": 0,
    "Nebula Scroll Volume 4": 0,
    "Nebula Scroll Volume 5": 0,
    "The Black Box": 0 # The Black Box effect is special, not point-based initially
}

ALL_ARTIFACTS = []
artifact_id_counter = 1 # Start with V1

# Create Standard Artifacts (90 total)
# Standard artifacts are V1-V90
for first_word in STANDARD_ARTIFACT_FIRST_WORDS:
    for second_word in STANDARD_ARTIFACT_SECOND_WORDS:
        if artifact_id_counter > 90:
            break # Should produce exactly 10 * 9 = 90 artifacts

        artifact_name = f"{first_word} {second_word}"
        is_plastic_artifact = (first_word.lower() == "plastic") # Case-insensitive check for "Plastic"
        
        points_val = -10 if is_plastic_artifact else 5

        ALL_ARTIFACTS.append(Artifact(
            id=f"V{artifact_id_counter}", # V1, V2, ..., V90
            name=artifact_name,
            points=points_val,
            is_plastic=is_plastic_artifact,
            category="Standard"
        ))
        artifact_id_counter += 1
    if artifact_id_counter > 90:
        break

# Create Special Artifacts (10 total)
# Special artifacts are V91-V100
for name, points_val in SPECIAL_ARTIFACT_NAMES_AND_POINTS.items():
    if artifact_id_counter > 100: # Ensure we don't exceed V100
        break 
        
    ALL_ARTIFACTS.append(Artifact(
        id=f"V{artifact_id_counter}", # V91, V92, ..., V100
        name=name,
        points=points_val,
        is_plastic=False, # None of the special artifacts are plastic
        category="Special" # "GreatestTreasure" is not used here based on prompt, just "Special"
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

class BuildOrder(Order):
    """Represents a build order for a world."""
    def __init__(self, world_id: int, build_type: str, quantity: int, 
                 target_entity_id: int | None = None, migration_pop_type: str | None = None):
        super().__init__(order_type="BUILD", priority=30)
        self.world_id = world_id
        self.build_type = build_type # "SHIP_FLEET", "SHIP_ISHOP", "SHIP_PSHIP", "INDUSTRY", "POP_LIMIT", "MIGRATE_POP", "ROBOTS"
        self.quantity = quantity
        self.target_entity_id = target_entity_id # For target_fleet_id or target_world_id
        self.migration_pop_type = migration_pop_type # "NORMAL", "ROBOT", "CONVERT"

class FireOrder(Order):
    """Represents a fire order for a fleet."""
    def __init__(self, firing_fleet_id: int, target_type: str, world_id: int, 
                 target_id: int | None = None, is_conditional: bool = False):
        super().__init__(order_type="FIRE", priority=50)
        self.firing_fleet_id = firing_fleet_id
        self.target_type = target_type  # "FLEET", "INDUSTRY", "POPULATION", "HOME_FLEETS"
        self.world_id = world_id # Location of combat
        self.target_id = target_id # Fleet ID if target_type is "FLEET"
        self.is_conditional = is_conditional


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
        self.turn_number = 0

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
        # is_merchant = False # No longer needed directly here
        # if fleet.owner and fleet.owner.character_type == "Merchant":
        #     is_merchant = True
        
        # max_cargo_capacity = fleet.ships * (2 if is_merchant else 1) # Old calculation
        max_cargo_capacity = fleet.get_max_cargo_capacity() # Use new method
        can_load_more = max_cargo_capacity - fleet.cargo
        if can_load_more < 0: can_load_more = 0 

        if can_load_more == 0 and order.metal_amount != 0 : # order.metal_amount can be -1 for "all"
             if order.metal_amount != -1 : # If not trying to load all, and capacity is zero, then it's full.
                return False, f"Fleet {fleet.name} (ID: {order.fleet_id}) is already full (capacity: {max_cargo_capacity}, current: {fleet.cargo})."
             elif fleet.cargo >= max_cargo_capacity : # If trying to load "all" but already at/over capacity
                return False, f"Fleet {fleet.name} (ID: {order.fleet_id}) is already at or over capacity (capacity: {max_cargo_capacity}, current: {fleet.cargo}). Cannot load more."


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

    def execute_fire_order(self, order: FireOrder, current_player: Player) -> tuple[bool, str]:
        """Executes a FireOrder for the given player."""
        if not isinstance(order, FireOrder):
            return False, "Invalid order type provided to execute_fire_order."

        firing_fleet = self.get_fleet(order.firing_fleet_id)
        world = self.get_world(order.world_id)

        if not firing_fleet:
            return False, f"Fire Order Error: Firing fleet with ID {order.firing_fleet_id} not found."
        if not world:
            return False, f"Fire Order Error: World with ID {order.world_id} not found."
        if firing_fleet.owner != current_player:
            return False, f"Fire Order Error: Fleet {firing_fleet.name} (ID: {order.firing_fleet_id}) is not owned by player {current_player.name}."
        if firing_fleet.location != world:
            return False, f"Fire Order Error: Firing fleet {firing_fleet.name} is not at world {world.name} (ID: {order.world_id})."
        if firing_fleet.is_at_peace:
             return False, f"Fire Order Error: Firing fleet {firing_fleet.name} is at peace and cannot fire."


        # Apostle Penalty
        if current_player.character_type == "Apostle":
            # current_player.victory_points -= 1 # Direct modification removed
            if current_player.user_id not in self.turn_vp_adjustments: self.turn_vp_adjustments[current_player.user_id] = 0
            self.turn_vp_adjustments[current_player.user_id] -= 1
            self.add_turn_event(current_player.user_id, "Lost 1 VP (event) for initiating combat as Apostle.")


        # Conditional Fire (Simplified: no firing for now)
        if order.is_conditional:
            return True, "Conditional fire order noted. Will not fire this turn under current simplified rules."

        # Calculate Shots
        num_effective_ships = firing_fleet.ships
        if firing_fleet.owner.character_type == "Merchant":
            # Merchants lose 1 shot per 1 metal they carry over their normal capacity (1 per ship)
            # This means if a ship carries 2 metal, it's 1 metal overloaded and doesn't fire.
            # If a ship carries 1 metal (normal capacity), it fires.
            # If a ship carries 0 metal, it fires.
            max_normal_cargo = firing_fleet.ships * 1 # Normal capacity is 1 metal per ship
            if firing_fleet.cargo > max_normal_cargo:
                # Each unit of metal above max_normal_cargo means one ship is fully dedicated to that extra cargo.
                overloaded_by_cargo_units = firing_fleet.cargo - max_normal_cargo
                # The number of ships that are "overloaded" and thus cannot fire is equal to this excess cargo count.
                # However, a single ship can carry 2 units for a Merchant.
                # If a merchant fleet of 10 ships has 15 cargo:
                # Normal capacity = 10. Overloaded by 5 cargo units.
                # This means 5 ships are carrying 2 units of cargo each (5*2=10 cargo).
                # The other 5 ships are carrying 1 unit of cargo each (5*1=5 cargo). Total 15.
                # The 5 ships carrying 2 units cannot fire. So, num_effective_ships = 10 - 5 = 5.
                
                # Simpler: number of ships that are carrying more than 1 unit of cargo.
                # If total cargo is C and total ships is S.
                # Each ship can carry 1 unit without penalty. C_normal = S.
                # Cargo beyond this is C_extra = C - S.
                # Each unit of C_extra must be carried by one of the S ships, making that ship carry 2 units.
                # So, number of ships carrying 2 units = C_extra. These ships don't fire.
                # num_effective_ships = S - C_extra = S - (C - S) = 2*S - C.
                # This formula is valid if C <= 2*S. If C > 2*S, something is wrong with cargo loading.
                # And C_extra should not exceed S (cannot have more double-loaded ships than total ships).
                
                ships_carrying_extra_load = 0
                if firing_fleet.cargo > firing_fleet.ships: # If cargo exceeds 1 per ship
                    ships_carrying_extra_load = firing_fleet.cargo - firing_fleet.ships
                
                num_effective_ships = firing_fleet.ships - ships_carrying_extra_load

        num_shots = num_effective_ships
        if num_shots <= 0:
            return False, f"Fire Order Error: Fleet {firing_fleet.name} has no ships capable of firing (0 effective ships)."

        # Targeting Logic
        message_parts = [f"Fleet {firing_fleet.name} (Player {current_player.name}) fires {num_shots} shots at {world.name} targeting {order.target_type}."]
        shots_remaining = num_shots # Keep track for multi-target types

        if order.target_type == "FLEET":
            if order.target_id is None:
                return False, f"Fire Order Error (FLEET): No target_id specified for FLEET target type."
            target_fleet = self.get_fleet(order.target_id)
            if not target_fleet:
                return False, f"Fire Order Error (FLEET): Target fleet with ID {order.target_id} not found."
            if target_fleet.location != world:
                return False, f"Fire Order Error (FLEET): Target fleet {target_fleet.name} is not at world {world.name}."
            if target_fleet.owner == current_player: # Cannot target own fleet
                 return False, f"Fire Order Error (FLEET): Cannot target own fleet {target_fleet.name}."
            if target_fleet.is_at_peace: # Cannot target fleet at peace
                 return False, f"Fire Order Error (FLEET): Cannot target fleet {target_fleet.name} as it is at peace."


            hits_per_ship = 1 if target_fleet.cargo > 0 else 2
            ships_destroyed_potential = num_shots // hits_per_ship
            actual_ships_lost = min(ships_destroyed_potential, target_fleet.ships)
            
            target_fleet.ships -= actual_ships_lost
            message_parts.append(f"Hit target fleet {target_fleet.name} (Owner: {target_fleet.owner.name if target_fleet.owner else 'Unowned'}), destroying {actual_ships_lost} ships.")

            if target_fleet.ships <= 0:
                original_owner_before_destruction = target_fleet.owner # Could be None already
                target_fleet.owner = None # Becomes unowned (key)
                message_parts.append(f"Target fleet {target_fleet.name} (ID: {target_fleet.id}) is now unowned.")
                
                if current_player.character_type == "Berserker" and original_owner_before_destruction is not None and original_owner_before_destruction != current_player:
                    vp_gain = actual_ships_lost * 2
                    # current_player.victory_points += vp_gain # Direct modification removed
                    if current_player.user_id not in self.turn_vp_adjustments: self.turn_vp_adjustments[current_player.user_id] = 0
                    self.turn_vp_adjustments[current_player.user_id] += vp_gain
                    message_parts.append(f"Berserker {current_player.name} gained {vp_gain} VP (event) for destroying ships of fleet {target_fleet.name}.")
                    self.add_turn_event(current_player.user_id, f"Gained {vp_gain} VP (event) for destroying ships of fleet {target_fleet.name}.")


        elif order.target_type == "INDUSTRY":
            # Target ISHIPS first, then Industry structures
            iships_destroyed_potential = shots_remaining // 2
            actual_iships_destroyed = min(world.iships, iships_destroyed_potential)
            if actual_iships_destroyed > 0:
                world.iships -= actual_iships_destroyed
                shots_remaining -= actual_iships_destroyed * 2
                message_parts.append(f"Destroyed {actual_iships_destroyed} ISHIPS at {world.name}.")

            industry_destroyed_potential = shots_remaining // 2
            actual_industry_destroyed = min(world.industry, industry_destroyed_potential)
            if actual_industry_destroyed > 0:
                world.industry -= actual_industry_destroyed
                # shots_remaining -= actual_industry_destroyed * 2 # Not needed further for this target type
                message_parts.append(f"Destroyed {actual_industry_destroyed} industry units at {world.name}.")
            
            if actual_iships_destroyed == 0 and actual_industry_destroyed == 0:
                 message_parts.append(f"No ISHIPS or industry destroyed at {world.name} (either none present or insufficient shots).")


        elif order.target_type == "POPULATION":
            # Target PSHIPS first, then Population units
            pships_destroyed_potential = shots_remaining // 2
            actual_pships_destroyed = min(world.pships, pships_destroyed_potential)
            if actual_pships_destroyed > 0:
                world.pships -= actual_pships_destroyed
                shots_remaining -= actual_pships_destroyed * 2
                message_parts.append(f"Destroyed {actual_pships_destroyed} PSHIPS at {world.name}.")

            # Now target population units (Normal, then Convert, then Robot)
            population_killed_potential = shots_remaining // 2
            
            # Calculate total killable population
            total_pop_units_at_world = world.population + world.convert_units + world.robot_units
            actual_total_population_killed = min(total_pop_units_at_world, population_killed_potential)
            
            if actual_total_population_killed > 0:
                killed_this_pass = 0
                
                # Kill Normal Population
                killed_normal = min(world.population, actual_total_population_killed - killed_this_pass)
                if killed_normal > 0:
                    world.population -= killed_normal
                    killed_this_pass += killed_normal
                    message_parts.append(f"Killed {killed_normal} normal population at {world.name}.")

                # Kill Convert Units (if still capacity to kill)
                if killed_this_pass < actual_total_population_killed:
                    killed_converts = min(world.convert_units, actual_total_population_killed - killed_this_pass)
                    if killed_converts > 0:
                        world.convert_units -= killed_converts
                        killed_this_pass += killed_converts
                        message_parts.append(f"Killed {killed_converts} convert units at {world.name}.")
                        if world.convert_units == 0: world.converts_owner_id = None # If all converts of an apostle are gone

                # Kill Robot Units (if still capacity to kill)
                if killed_this_pass < actual_total_population_killed:
                    killed_robots = min(world.robot_units, actual_total_population_killed - killed_this_pass)
                    if killed_robots > 0:
                        world.robot_units -= killed_robots
                        # killed_this_pass += killed_robots # Not needed for further calculation
                        message_parts.append(f"Killed {killed_robots} robot units at {world.name}.")
                
                # VP adjustments for population killed
                if current_player.character_type == "Berserker":
                    vp_change = actual_total_population_killed * 2
                    # current_player.victory_points += vp_change # Direct modification removed
                    if current_player.user_id not in self.turn_vp_adjustments: self.turn_vp_adjustments[current_player.user_id] = 0
                    self.turn_vp_adjustments[current_player.user_id] += vp_change
                    message_parts.append(f"Berserker {current_player.name} gained {vp_change} VP (event) for killing population.")
                    self.add_turn_event(current_player.user_id, f"Gained {vp_change} VP (event) for killing population at {world.name}.")

                else: # Non-Berserker firing at population
                    vp_change = actual_total_population_killed * 1
                    # current_player.victory_points -= vp_change # Direct modification removed
                    if current_player.user_id not in self.turn_vp_adjustments: self.turn_vp_adjustments[current_player.user_id] = 0
                    self.turn_vp_adjustments[current_player.user_id] -= vp_change
                    message_parts.append(f"Player {current_player.name} lost {vp_change} VP (event) for killing population.")
                    self.add_turn_event(current_player.user_id, f"Lost {vp_change} VP (event) for killing population at {world.name}.")


            if actual_pships_destroyed == 0 and actual_total_population_killed == 0:
                 message_parts.append(f"No PSHIPS or population units destroyed at {world.name} (either none present or insufficient shots).")
        
        elif order.target_type == "HOME_FLEETS":
            # Target ISHIPS first
            iships_destroyed_potential = shots_remaining // 2
            actual_iships_destroyed = min(world.iships, iships_destroyed_potential)
            if actual_iships_destroyed > 0:
                world.iships -= actual_iships_destroyed
                shots_remaining -= actual_iships_destroyed * 2
                message_parts.append(f"Destroyed {actual_iships_destroyed} ISHIPS at {world.name}.")

            # Then target PSHIPS
            pships_destroyed_potential = shots_remaining // 2
            actual_pships_destroyed = min(world.pships, pships_destroyed_potential)
            if actual_pships_destroyed > 0:
                world.pships -= actual_pships_destroyed
                shots_remaining -= actual_pships_destroyed * 2 # Use up shots for PSHIPS
                message_parts.append(f"Destroyed {actual_pships_destroyed} PSHIPS at {world.name}.")

            # Check for world becoming unowned (key capture)
            if world.iships == 0 and world.pships == 0 and shots_remaining >= 2: # Must have at least 2 shots left to neutralize
                if world.owner is not None: # Only if it was owned
                    message_parts.append(f"World {world.name} (ID: {world.id}) has been neutralized and is now unowned.")
                    world.owner = None
                    world.turns_owned = 0 # Reset turns_owned
                    # Any population/robots/converts remain for now. Conquest logic is separate.
                else:
                    message_parts.append(f"World {world.name} (ID: {world.id}) home fleets destroyed, was already unowned.")
            
            if actual_iships_destroyed == 0 and actual_pships_destroyed == 0:
                 message_parts.append(f"No ISHIPS or PSHIPS destroyed at {world.name} (either none present or insufficient shots).")

        else:
            return False, f"Fire Order Error: Unknown target_type '{order.target_type}'."

        return True, " ".join(message_parts)


    def execute_build_order(self, order: BuildOrder, current_player: Player) -> tuple[bool, str]:
        """Executes a BuildOrder for the given player."""
        if not isinstance(order, BuildOrder):
            return False, "Invalid order type provided to execute_build_order."

        world = self.get_world(order.world_id)
        if not world:
            return False, f"Build Order Error: World with ID {order.world_id} not found."

        if world.owner != current_player:
            return False, f"Build Order Error: Player {current_player.name} does not own World {world.name} (ID: {world.id})."

        if world.is_black_hole:
            return False, f"Build Order Error: Cannot build in Black Hole {world.name} (ID: {world.id})."

        # Resource availability and costs will be handled per build_type
        # order.quantity is the number of items to build or units to affect.

        if order.build_type == "SHIP_FLEET":
            cost_metal_per_ship = 1
            cost_pop_per_ship = 1
            # Industry capacity required is 1 per ship, but industry itself is not "consumed" like metal/pop.
            # The check is against available world.industry.
            
            required_metal = order.quantity * cost_metal_per_ship
            required_pop = order.quantity * cost_pop_per_ship
            required_industry_capacity = order.quantity 

            if order.quantity <= 0:
                return False, f"Build Order Error (SHIP_FLEET): Quantity must be positive. Got {order.quantity}."
            if world.stockpile < required_metal:
                return False, f"Build Order Error (SHIP_FLEET): Not enough metal at {world.name}. Has {world.stockpile}, needs {required_metal}."
            if world.population < required_pop:
                return False, f"Build Order Error (SHIP_FLEET): Not enough population at {world.name}. Has {world.population}, needs {required_pop}."
            if world.industry < required_industry_capacity:
                return False, f"Build Order Error (SHIP_FLEET): Not enough industry capacity at {world.name}. Has {world.industry}, needs {required_industry_capacity}."

            target_fleet = self.get_fleet(order.target_entity_id)
            if not target_fleet:
                return False, f"Build Order Error (SHIP_FLEET): Target fleet with ID {order.target_entity_id} not found."
            if target_fleet.location != world:
                return False, f"Build Order Error (SHIP_FLEET): Target fleet {target_fleet.name} is not at world {world.name}."
            if target_fleet.owner != current_player:
                return False, f"Build Order Error (SHIP_FLEET): Target fleet {target_fleet.name} is not owned by player {current_player.name}."

            world.stockpile -= required_metal
            world.population -= required_pop
            # world.industry is "used" for this turn's capacity, not permanently reduced.
            target_fleet.ships += order.quantity
            return True, f"Successfully built {order.quantity} ships for fleet {target_fleet.name} at {world.name}."

        elif order.build_type == "SHIP_ISHOP" or order.build_type == "SHIP_PSHIP":
            cost_metal_per_ship = 1
            cost_pop_per_ship = 1
            required_industry_capacity = order.quantity

            if order.quantity <= 0:
                return False, f"Build Order Error ({order.build_type}): Quantity must be positive. Got {order.quantity}."

            required_metal = order.quantity * cost_metal_per_ship
            required_pop = order.quantity * cost_pop_per_ship
            
            if world.stockpile < required_metal:
                return False, f"Build Order Error ({order.build_type}): Not enough metal at {world.name}. Has {world.stockpile}, needs {required_metal}."
            if world.population < required_pop:
                return False, f"Build Order Error ({order.build_type}): Not enough population at {world.name}. Has {world.population}, needs {required_pop}."
            if world.industry < required_industry_capacity:
                return False, f"Build Order Error ({order.build_type}): Not enough industry capacity at {world.name}. Has {world.industry}, needs {required_industry_capacity}."

            world.stockpile -= required_metal
            world.population -= required_pop
            
            if order.build_type == "SHIP_ISHOP":
                world.iships += order.quantity
                return True, f"Successfully built {order.quantity} ISHIPS at {world.name}."
            else: # SHIP_PSHIP
                world.pships += order.quantity
                return True, f"Successfully built {order.quantity} PSHIPS at {world.name}."

        elif order.build_type == "INDUSTRY":
            is_empire_builder = current_player.character_type == "Empire Builder"
            cost_per_unit = 4 if is_empire_builder else 5
            
            if order.quantity <= 0:
                return False, f"Build Order Error (INDUSTRY): Quantity must be positive. Got {order.quantity}."

            needed_metal = order.quantity * cost_per_unit
            needed_pop = order.quantity * cost_per_unit
            needed_acting_industry = order.quantity * cost_per_unit # Existing industry needed to build more

            if world.stockpile < needed_metal:
                return False, f"Build Order Error (INDUSTRY): Not enough metal at {world.name}. Has {world.stockpile}, needs {needed_metal}."
            if world.population < needed_pop:
                return False, f"Build Order Error (INDUSTRY): Not enough population at {world.name}. Has {world.population}, needs {needed_pop}."
            if world.industry < needed_acting_industry: # Check if current industry can support building this much new industry
                return False, f"Build Order Error (INDUSTRY): Not enough existing industry capacity at {world.name}. Has {world.industry}, needs {needed_acting_industry} to build {order.quantity} new units."

            world.stockpile -= needed_metal
            world.population -= needed_pop
            # world.industry capacity is "used", not consumed like stockpile/pop.
            world.industry += order.quantity
            return True, f"Successfully built {order.quantity} industry units at {world.name}."

        elif order.build_type == "POP_LIMIT":
            is_empire_builder = current_player.character_type == "Empire Builder"
            cost_per_unit_increase = 4 if is_empire_builder else 5 # Assuming same cost scaling as industry

            if order.quantity <= 0: # Quantity here means how much to increase the pop limit by
                return False, f"Build Order Error (POP_LIMIT): Increase quantity must be positive. Got {order.quantity}."

            needed_metal = order.quantity * cost_per_unit_increase
            needed_pop = order.quantity * cost_per_unit_increase
            needed_acting_industry = order.quantity * cost_per_unit_increase

            if world.stockpile < needed_metal:
                return False, f"Build Order Error (POP_LIMIT): Not enough metal at {world.name}. Has {world.stockpile}, needs {needed_metal}."
            if world.population < needed_pop:
                return False, f"Build Order Error (POP_LIMIT): Not enough population at {world.name}. Has {world.population}, needs {needed_pop}."
            if world.industry < needed_acting_industry:
                return False, f"Build Order Error (POP_LIMIT): Not enough existing industry capacity at {world.name}. Has {world.industry}, needs {needed_acting_industry}."
            
            world.stockpile -= needed_metal
            world.population -= needed_pop
            world.max_population += order.quantity
            return True, f"Successfully increased max population by {order.quantity} at {world.name}. New max: {world.max_population}."

        elif order.build_type == "MIGRATE_POP":
            cost_metal_per_unit = 1
            cost_industry_per_unit = 1 # Industry capacity used

            if order.quantity <= 0:
                return False, f"Build Order Error (MIGRATE_POP): Quantity must be positive. Got {order.quantity}."
            
            needed_metal = order.quantity * cost_metal_per_unit
            needed_industry_capacity = order.quantity * cost_industry_per_unit

            if world.stockpile < needed_metal:
                return False, f"Build Order Error (MIGRATE_POP): Not enough metal at {world.name}. Has {world.stockpile}, needs {needed_metal}."
            if world.industry < needed_industry_capacity:
                 return False, f"Build Order Error (MIGRATE_POP): Not enough industry capacity at {world.name}. Has {world.industry}, needs {needed_industry_capacity}."

            target_world = self.get_world(order.target_entity_id)
            if not target_world:
                return False, f"Build Order Error (MIGRATE_POP): Target world with ID {order.target_entity_id} not found."
            if target_world.is_black_hole:
                return False, f"Build Order Error (MIGRATE_POP): Cannot migrate population to Black Hole {target_world.name}."
            if target_world not in world.connections and world not in target_world.connections : # Check direct connection
                return False, f"Build Order Error (MIGRATE_POP): World {world.name} is not connected to target world {target_world.name}."

            source_pop_count = 0
            if order.migration_pop_type == "NORMAL":
                source_pop_count = world.population
            elif order.migration_pop_type == "ROBOT":
                source_pop_count = world.robot_units
            elif order.migration_pop_type == "CONVERT":
                source_pop_count = world.convert_units
                if world.converts_owner_id != current_player.user_id: # Must be player's own converts
                     return False, f"Build Order Error (MIGRATE_POP): Player {current_player.name} cannot migrate converts they do not control at {world.name}."
            else:
                return False, f"Build Order Error (MIGRATE_POP): Invalid migration_pop_type '{order.migration_pop_type}'."

            if source_pop_count < order.quantity:
                return False, f"Build Order Error (MIGRATE_POP): Insufficient {order.migration_pop_type} population at {world.name}. Has {source_pop_count}, needs {order.quantity}."

            # Check target world capacity
            if order.migration_pop_type == "NORMAL" and target_world.population + order.quantity > target_world.max_population:
                return False, f"Build Order Error (MIGRATE_POP): Target world {target_world.name} does not have enough max population capacity for {order.quantity} new NORMAL population."
            # Robot and Convert migrations don't check max_population of target world as per typical game rules.

            # Consume resources from source world
            world.stockpile -= needed_metal
            # world.industry capacity used

            # Move population
            if order.migration_pop_type == "NORMAL":
                world.population -= order.quantity
                target_world.population += order.quantity
            elif order.migration_pop_type == "ROBOT":
                world.robot_units -= order.quantity
                target_world.robot_units += order.quantity
                # If robots move to a world not owned by the current player, ownership dynamics might apply (later feature)
            elif order.migration_pop_type == "CONVERT":
                world.convert_units -= order.quantity
                
                # If target world is unowned by an apostle or owned by a different apostle, current player's converts take over/establish.
                if target_world.converts_owner_id != current_player.user_id:
                    target_world.converts_owner_id = current_player.user_id
                    target_world.convert_units = order.quantity # New converts replace any existing ones of a different apostle
                else: # Target world already has converts of the current player
                    target_world.convert_units += order.quantity
            
            return True, f"Successfully migrated {order.quantity} {order.migration_pop_type} population from {world.name} to {target_world.name}."

        elif order.build_type == "ROBOTS": # Build new robots
            if current_player.character_type != "Berserker":
                return False, f"Build Order Error (ROBOTS): Only Berserkers can build robots. Player {current_player.name} is a {current_player.character_type}."
            
            # World must be robot-controlled by this player
            is_robot_controlled_by_player = (
                world.robot_units > 0 and 
                world.population == 0 and 
                world.convert_units == 0 and 
                world.owner == current_player
            )
            if not is_robot_controlled_by_player:
                return False, f"Build Order Error (ROBOTS): World {world.name} is not robot-controlled by player {current_player.name} (needs: robots > 0, pop == 0, converts == 0)."

            # Cost: 1 industry & 1 metal makes 2 robots. Order.quantity is the amount of "pairs" or "sets" to build.
            # So, if order.quantity is 1, it means 1 unit of industry and 1 unit of metal are used to make 2 robots.
            if order.quantity <= 0:
                return False, f"Build Order Error (ROBOTS): Quantity (of build effort) must be positive. Got {order.quantity}."

            cost_metal_per_effort = 1
            cost_industry_capacity_per_effort = 1
            robots_built_per_effort = 2
            # Existing robots needed to operate the industry
            robots_operating_industry_per_effort = 1 

            needed_metal = order.quantity * cost_metal_per_effort
            needed_industry_capacity = order.quantity * cost_industry_capacity_per_effort
            needed_robot_operators = order.quantity * robots_operating_industry_per_effort
            
            num_robots_to_build = order.quantity * robots_built_per_effort

            if world.stockpile < needed_metal:
                return False, f"Build Order Error (ROBOTS): Not enough metal at {world.name}. Has {world.stockpile}, needs {needed_metal}."
            if world.industry < needed_industry_capacity:
                 return False, f"Build Order Error (ROBOTS): Not enough industry capacity at {world.name}. Has {world.industry}, needs {needed_industry_capacity}."
            if world.robot_units < needed_robot_operators: # Check if enough existing robots to do the work
                 return False, f"Build Order Error (ROBOTS): Not enough existing robots to operate industry at {world.name}. Has {world.robot_units}, needs {needed_robot_operators} for this build quantity."
            
            world.stockpile -= needed_metal
            # world.industry capacity used
            # world.robot_units used for operation are not "consumed" from world.robot_units, they are just busy.
            world.robot_units += num_robots_to_build
            return True, f"Successfully built {num_robots_to_build} robots at {world.name}."

        else:
            return False, f"Build Order Error: Unknown build_type '{order.build_type}'."


    def process_turn(self, user_id: str, raw_orders_list: list[dict]) -> list[str]:
        """Processes a list of raw order dictionaries for a turn, for a given user."""
        self.turn_number += 1
        print(f"Processing Turn {self.turn_number} for user: {user_id}")
        
        # Initialize turn-specific VP adjustments
        self.turn_vp_adjustments: dict[str, int] = {}

        current_player_object = next((p for p in self.players if p.user_id == user_id), None)
        if not current_player_object:
            # This case should ideally be prevented by @login_required and game setup
            # Or if an admin is somehow submitting turns for a non-existent player.
            return [f"Critical Error: Player object not found for user_id {user_id}. Cannot process turn."]

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
            if isinstance(order_obj, MoveOrder): # Use isinstance for clarity
                success, message = self.execute_move_order(order_obj)
            elif isinstance(order_obj, TransferOrder):
                success, message = self.execute_transfer_order(order_obj)
            elif isinstance(order_obj, LoadCargoOrder):
                success, message = self.execute_load_cargo_order(order_obj)
            elif isinstance(order_obj, UnloadCargoOrder):
                success, message = self.execute_unload_cargo_order(order_obj)
            elif isinstance(order_obj, BuildOrder):
                success, message = self.execute_build_order(order_obj, current_player_object)
            else:
                # This path should ideally not be reached if order_from_dict is comprehensive
                message = f"Order type {type(order_obj).__name__} not recognized by process_turn."
            
            results_messages.append(f"Order ({order_obj.order_type} P{order_obj.priority}): {message} (Success: {success})")
        
        # --- Metal Production Phase ---
        # This should happen after all orders that might consume stockpile or affect mines/population.
        # For simplicity, doing it after all player orders for this turn.
        # A more complex turn sequence might have it at a specific phase relative to other game events.
        for world in self.worlds:
            if world.owner and not world.is_black_hole: # Only owned, non-black hole worlds produce
                pop_for_mining = 0
                if world.robot_units > 0 and world.population == 0 and world.convert_units == 0 : # Robot-controlled world
                    pop_for_mining = world.robot_units
                elif world.robot_units == 0 and world.convert_units == 0: # Normal population controlled world
                     pop_for_mining = world.population
                # else: mixed population, or convert-controlled worlds don't run mines as per rules.
                
                if pop_for_mining > 0 and world.mines > 0:
                    produced_metal = min(world.mines, pop_for_mining)
                    old_stockpile = world.stockpile
                    world.stockpile = min(world.stockpile + produced_metal, 255) # Cap stockpile at 255
                    if world.stockpile > old_stockpile :
                         # Only log if metal was actually added (relevant if already at cap)
                        production_msg = f"World {world.name} (ID: {world.id}, Owner: {world.owner.name}) produced {world.stockpile - old_stockpile} metal. New stockpile: {world.stockpile}."
                        # This message is for server log for now, could be an event for player.
                        print(production_msg) 
                        # self.add_turn_event(world.owner.user_id, production_msg) # If players should be notified

        # --- Metal Production Phase --- (Already done)
        # ...

        # --- Population Growth Phase ---
        print(f"Turn {self.turn_number}: Starting Population Growth Phase for player {current_player_object.name}...")
        for world in self.worlds:
            if world.owner and world.owner == current_player_object and not world.is_black_hole: # Process growth only for current player's worlds
                # Plunder check would go here: if world.is_recovering_from_plunder: continue

                if world.robot_units > 0: # Robots don't grow naturally
                    pass # No natural growth for robots
                else: # Normal or Convert populations
                    current_total_pop = world.population + world.convert_units
                    
                    if current_total_pop >= world.max_population:
                        continue # No room to grow

                    base_growth = (world.population + world.convert_units) // 10
                    if base_growth == 0 and current_total_pop > 0 and current_total_pop < world.max_population:
                        base_growth = 1 # Ensure at least 1 growth if pop > 0, < 10 and space exists

                    potential_new_total_pop = current_total_pop + base_growth
                    actual_growth = base_growth if potential_new_total_pop <= world.max_population else world.max_population - current_total_pop

                    if actual_growth <= 0:
                        continue

                    growth_message_parts = [f"World {world.name} (ID: {world.id})"]
                    if world.owner.character_type == "Apostle":
                        original_pop = world.population
                        original_converts = world.convert_units

                        # Try to convert existing normal population first
                        converts_from_normal = min(actual_growth, world.population)
                        if converts_from_normal > 0:
                            world.population -= converts_from_normal
                            world.convert_units += converts_from_normal
                            growth_message_parts.append(f"converted {converts_from_normal} normal pop to converts.")
                        
                        # If more growth capacity remains, add new converts
                        remaining_growth_capacity = actual_growth - converts_from_normal
                        if remaining_growth_capacity > 0:
                            world.convert_units += remaining_growth_capacity
                            growth_message_parts.append(f"grew {remaining_growth_capacity} new converts.")
                        
                        world.converts_owner_id = world.owner.user_id # Ensure owner ID is set
                        if world.population != original_pop or world.convert_units != original_converts:
                             self.add_turn_event(world.owner.user_id, f"{' '.join(growth_message_parts)} New totals: Pop {world.population}, Converts {world.convert_units}.")

                    else: # Owner is not Apostle
                        world.population += actual_growth
                        self.add_turn_event(world.owner.user_id, f"World {world.name} (ID: {world.id}) population grew by {actual_growth}. New population: {world.population}.")
                    
                    # Ensure consistency (should be guaranteed by logic above but as a safeguard)
                    if world.population + world.convert_units > world.max_population:
                        # This case should ideally not be hit if logic is correct
                        print(f"Warning: Pop growth exceeded max_population for world {world.id}. Correcting.")
                        if world.owner.character_type == "Apostle":
                             # Prioritize converts if overflown, remove from normal pop first if mixed.
                             # This part of correction might need more nuanced rules if hit.
                             overflow = (world.population + world.convert_units) - world.max_population
                             world.convert_units -= overflow # Simplistic correction
                        else:
                            world.population = world.max_population - world.convert_units # Assumes converts are 0 for non-apostles

        # --- World and Key Capture Logic ---
        # This should run *after* all orders for the turn, including combat and movement.
        self.resolve_world_and_key_capture() # This now also includes turns_owned/mine_increase at its end

        # --- Final Player VP Update Phase ---
        print(f"Turn {self.turn_number}: Final VP Update Phase for player {current_player_object.name}...")
        # This part should iterate over ALL players if process_turn becomes a global EOT function.
        # For now, it correctly processes for the current_user_id who submitted the turn.
        # If multiple players submit turns in a "round", this VP calculation will reflect their state
        # after their orders and subsequent growth/capture phases.
        
        # Calculate base VPs from character type (based on current game state)
        base_turn_vp = current_player_object.character.calculate_victory_points(self)
        
        # Get event VPs accumulated during this player's order processing
        event_vp = self.turn_vp_adjustments.get(current_player_object.user_id, 0)
        
        current_player_object.victory_points = base_turn_vp + event_vp
        
        vp_update_msg = (
            f"End of Turn {self.turn_number} for {current_player_object.name}: "
            f"Base VP: {base_turn_vp}, Event VP: {event_vp}, Total VP: {current_player_object.victory_points}."
        )
        self.add_turn_event(current_player_object.user_id, vp_update_msg)
        print(vp_update_msg) # Server log

        return results_messages
    
    def resolve_world_and_key_capture(self):
        """Resolves world ownership and capture of unowned fleets (keys) based on presence.
           Also handles end-of-turn mine increases."""
        print(f"Turn {self.turn_number}: Resolving world/key capture and mine increases...")

        # World Capture
        for world in self.worlds:
            if world.is_black_hole:
                continue

            # Fleets that can exert control: has ships, not at peace, and owned by a player
            eligible_fleets_present = [
                f for f in self.fleets 
                if f.location == world and f.ships > 0 and not f.is_at_peace and f.owner is not None
            ]

            if not eligible_fleets_present:
                # If no eligible fleets, current owner retains control unless the world is truly empty
                # and was made unowned by combat (e.g. HOME_FLEETS target).
                # If world.owner is None (e.g. from combat), it remains None.
                # If world has defenses (iships, pships, pop etc.) it can defend itself if owner is present.
                # This part is simplified: if no one is there to challenge, owner keeps it.
                # A world becoming unowned due to combat is handled by execute_fire_order.
                continue 
            
            # Get set of unique player objects who have eligible fleets at the world
            owners_present_objects = {f.owner for f in eligible_fleets_present} # Set of Player objects

            if len(owners_present_objects) == 1:
                new_potential_owner = owners_present_objects.pop() # The Player object

                # Check for capturing from an ally
                is_capturing_from_ally = False
                if world.owner and world.owner != new_potential_owner: # If there's a different current owner
                    if world.owner.user_id in new_potential_owner.allies or new_potential_owner.user_id in world.owner.allies:
                        is_capturing_from_ally = True
                
                if not is_capturing_from_ally:
                    if world.owner != new_potential_owner:
                        capture_msg = f"World {world.name} (ID: {world.id}) captured by {new_potential_owner.name} from {world.owner.name if world.owner else 'Unowned'}."
                        print(capture_msg)
                        if world.owner: # Notify old owner if existed
                            self.add_turn_event(world.owner.user_id, f"You lost control of world {world.name} (ID: {world.id}) to {new_potential_owner.name}.")
                        self.add_turn_event(new_potential_owner.user_id, f"You captured world {world.name} (ID: {world.id}) from {world.owner.name if world.owner else 'Unowned'}.")
                        
                        world.owner = new_potential_owner
                        world.turns_owned = 1 # Reset turns owned for new owner
                        # Reset convert units if captured by non-apostle or different apostle
                        if new_potential_owner.character_type != "Apostle" or world.converts_owner_id != new_potential_owner.user_id:
                            if world.convert_units > 0:
                                world.convert_units = 0
                                world.converts_owner_id = None
                                self.add_turn_event(new_potential_owner.user_id, f"Any convert units at {world.name} were disbanded upon capture.")
                else:
                    # Log attempt to capture from ally
                    print(f"Player {new_potential_owner.name} fleet at {world.name} but world is owned by ally {world.owner.name}. No capture.")
                    self.add_turn_event(new_potential_owner.user_id, f"Your fleet at {world.name} did not capture it as it's owned by your ally {world.owner.name}.")


            # Else (multiple owners present, or no owners with fleets and world was already unowned): ownership doesn't change from this phase.
            # Combat might have already made it unowned.

        # Loose Key (Unowned Fleet) Capture
        for key_fleet in self.fleets:
            # Candidate for capture: unowned fleet with 0 ships, at a non-black hole world
            if key_fleet.owner is None and key_fleet.ships == 0 and key_fleet.location and not key_fleet.location.is_black_hole:
                world_of_key = key_fleet.location
                
                eligible_capturing_fleets_at_key_loc = [
                    f for f in self.fleets 
                    if f.location == world_of_key and f.ships > 0 and not f.is_at_peace and f.owner is not None
                ]
                
                capturing_owners_objects = {f.owner for f in eligible_capturing_fleets_at_key_loc} # Set of Player objects

                if len(capturing_owners_objects) == 1:
                    new_owner_of_key = capturing_owners_objects.pop() # The Player object
                    
                    # No direct check for "capturing key from ally" as keys are unowned.
                    # The implicit rule is that if an ally is the only one who could capture it, they get it.
                    # If multiple non-allied players could, it remains unowned. (Handled by len(capturing_owners_objects) == 1)

                    key_fleet.owner = new_owner_of_key
                    key_capture_msg = f"Unowned fleet key {key_fleet.name} (ID: {key_fleet.id}) at {world_of_key.name} now owned by {new_owner_of_key.name}."
                    print(key_capture_msg)
                    self.add_turn_event(new_owner_of_key.user_id, f"You acquired unowned fleet key {key_fleet.name} (ID: {key_fleet.id}) at {world_of_key.name}.")
                    # Artifacts on the key_fleet are now implicitly owned by new_owner_of_key.
        
        # --- Turns Owned & Mine Increase Phase (Moved to very end) ---
        for world in self.worlds:
            if world.owner and not world.is_black_hole:
                world.turns_owned += 1
                if world.turns_owned == 8:
                    world.turns_owned = 1 
                    if world.mines > 0 and world.mines < 30: # Max mines strictly 30
                        world.mines += 1
                        mine_increase_msg = f"World {world.name} (ID: {world.id}, Owner: {world.owner.name}) increased mines to {world.mines} due to sustained ownership."
                        print(mine_increase_msg)
                        if world.owner: # Should always be true here
                             self.add_turn_event(world.owner.user_id, mine_increase_msg)


        return results_messages


# Global helper function
def order_from_dict(order_dict: dict) -> Order | None:
    """Creates an Order subclass instance from a dictionary."""
    order_type = order_dict.get('order_type')
    
    # Prepare data by removing 'order_type' for **kwargs to pass to constructors
    # This assumes constructor parameters match dictionary keys.
    data = {k: v for k, v in order_dict.items() if k != 'order_type'}

    try:
        if order_type == "BUILD":
            # Ensure quantity is int. target_entity_id can be None.
            data['quantity'] = int(data['quantity'])
            if 'target_entity_id' in data and data['target_entity_id'] is not None:
                data['target_entity_id'] = int(data['target_entity_id'])
            return BuildOrder(**data)
        elif order_type == "FIRE":
            data['firing_fleet_id'] = int(data['firing_fleet_id'])
            data['world_id'] = int(data['world_id'])
            if 'target_id' in data and data['target_id'] is not None:
                data['target_id'] = int(data['target_id'])
            if 'is_conditional' in data: # Should be boolean
                 data['is_conditional'] = bool(data['is_conditional'])
            return FireOrder(**data)
        elif order_type == "MOVE":
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
            artifacts=[], # Initialized as empty list
            robot_units=0, # Standard worlds start with no robots
            convert_units=0, # Standard worlds start with no converts
            converts_owner_id=None
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

    # Initialize black holes (example: 5% chance for any world to be a black hole)
    # This should be done after worlds are created.
    for world_obj in new_game.worlds:
        if random.random() < 0.05: # 5% chance
            world_obj.is_black_hole = True
            # Potentially modify other attributes for black holes, e.g., no population, no owner
            world_obj.owner = None
            world_obj.population = 0
            world_obj.max_population = 0
            world_obj.industry = 0
            world_obj.mines = 0
            world_obj.stockpile = 0
            world_obj.iships = 0
            world_obj.pships = 0
            world_obj.artifacts = [] # Black holes probably don't have artifacts
            world_obj.robot_units = 0 # Black holes don't have robots
            world_obj.convert_units = 0 # Black holes don't have converts
            world_obj.converts_owner_id = None
            world_obj.name = f"Black Hole W{world_obj.id}" # Rename for clarity
            # Black holes might not have connections, or limited/special connections.
            # For now, connect_all_worlds might connect them. This may need adjustment.
            # If black holes should not be connected, their connections list should be cleared
            # AFTER connect_all_worlds, or connect_all_worlds should be made aware of them.
            # For simplicity, let's assume they can be part of the network for now,
            # but their properties make them undesirable/dangerous.

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
    selected_homeworld.turns_owned = 1 # Initialize to 1 as it's now owned
    selected_homeworld.robot_units = 0 # Homeworlds start with no robots
    selected_homeworld.convert_units = 0 # Homeworlds start with no converts
    selected_homeworld.converts_owner_id = None # Homeworlds start with no apostle converts
    # selected_homeworld.is_black_hole remains False by default for homeworlds
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
