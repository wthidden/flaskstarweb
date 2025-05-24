import random
import json # Added for parsing JSON

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

    def __init__(self, id, name, owner: 'Player | None', connections, iships, pships, population, max_population, industry, mines,
                 stockpile,
                 artifacts):
        self.id = id
        self.name = name
        self.owner: Player | None = owner
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

    def __init__(self, id, name, ships, location: World | None, owner: 'Player | None', cargo, artifacts):
        self.id = id
        self.name = name
        self.ships = ships
        self.location: World | None = location
        self.owner: Player | None = owner
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
    def __init__(self, name: str, character_type: str, home_world: World | None = None, diplomacy: dict | None = None, worlds: list[World] | None = None, fleets: list[Fleet] | None = None):
        self.name = name
        self.character_type = character_type
        self.home_world: World | None = home_world 
        self.diplomacy = diplomacy if diplomacy is not None else {}
        self.worlds: list[World] = worlds if worlds is not None else []
        self.fleets: list[Fleet] = fleets if fleets is not None else []
        self.character = self.create_character() # This might need self to be passed if methods depend on player state

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


# Order Classes
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
            intermediate_world = path_world_objects[i]
            if intermediate_world == final_destination_world and i == len(path_world_objects) -1 :
                # This is the final destination, not an intermediate pass-through
                pass
            else:
                # TODO: Implement logic for hostile fleets at this intermediate world to fire upon the moving fleet.
                # print(f"Fleet {fleet_to_move.name} passing through {intermediate_world.name}...") # Optional: for tracing
                pass
            
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

    def process_turn(self, raw_orders_list: list[dict]) -> list[str]:
        """Processes a list of raw order dictionaries for a turn."""
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
    # --- Game Initialization Refactor ---
    num_players = 2 # Example: Create 2 players
    num_worlds_per_player = 2 # Each player gets a couple of starting worlds
    num_fleets_per_player = 1

    all_worlds = create_worlds() # Creates 10 worlds by default, no owners
    connect_worlds(all_worlds)

    players = []
    player_character_types = ["Merchant", "Empire Builder", "Pirate", "Berserker"] # Cycle through these
    
    # Create Players
    for i in range(num_players):
        player_name = f"Player {i+1}"
        char_type_index = i % len(player_character_types)
        # Homeworld will be assigned shortly
        player = Player(name=player_name, character_type=player_character_types[char_type_index], home_world=None)
        players.append(player)

    # Assign Homeworlds and initial worlds to players
    world_idx_counter = 0
    for i, player in enumerate(players):
        if world_idx_counter < len(all_worlds):
            home_world_candidate = all_worlds[world_idx_counter]
            player.home_world = home_world_candidate
            home_world_candidate.owner = player # Assign player object as owner
            player.worlds.append(home_world_candidate)
            world_idx_counter += 1
        
        # Assign additional worlds if available
        for _ in range(num_worlds_per_player -1): # -1 because homeworld is already one
            if world_idx_counter < len(all_worlds):
                other_world = all_worlds[world_idx_counter]
                if other_world.owner is None: # Only take unowned worlds
                    other_world.owner = player
                    player.worlds.append(other_world)
                world_idx_counter +=1
            else:
                break # No more worlds to assign

    all_fleets = []
    fleet_id_counter = 1
    for i, player in enumerate(players):
        if player.home_world: # Ensure player has a homeworld to place fleets
            for _ in range(num_fleets_per_player):
                fleet = Fleet(
                    id=fleet_id_counter,
                    name=f"Fleet {fleet_id_counter} ({player.name})",
                    ships=random.randint(5, 10),
                    location=player.home_world, # Start at homeworld
                    owner=player, # Assign Player object
                    cargo=0,
                    artifacts=[]
                )
                all_fleets.append(fleet)
                player.fleets.append(fleet)
                fleet_id_counter += 1
    
    # Assign remaining unowned worlds to be ownerless (None) - create_worlds already does this.
    # Ensure all worlds and fleets are in the main game lists
    return Game(worlds=all_worlds, fleets=all_fleets, players=players)


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
    # The /move_fleet route is now obsolete as Move orders are handled by /submit_turn
    flash("The direct /move_fleet route is deprecated. Please use the 'Plan Your Turn' interface to move fleets.")
    return redirect(url_for('display_game'))

@app.route('/submit_turn', methods=['POST'])
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

    results_messages = game_instance.process_turn(raw_orders_list)

    for msg in results_messages:
        flash(msg) # Flash individual detailed messages
    
    if not results_messages and raw_orders_list : # If orders were submitted but none were processed (e.g. all malformed)
        flash("Orders submitted, but no valid orders were processed successfully.")
    elif not raw_orders_list: # If an empty list of orders was submitted
         flash("No orders were submitted in the turn plan.")

    return redirect(url_for('display_game'))


if __name__ == '__main__':
    app.wsgi_app = StarWeb(app.wsgi_app)
    app.run()
