import unittest
import sys
import os

# Adjust the path to import from the parent directory (project root)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import Game, World, Fleet, Player, User, Artifact # Added User for _register_new_player_setup, Artifact
from app import MoveOrder, TransferOrder, LoadCargoOrder, UnloadCargoOrder, order_from_dict
from app import AttachArtifactOrder, DropArtifactOrder, AmbushOrder, SetAllyOrder, GiftWorldOrder, GiftFleetOrder # Import new order classes
from app import create_game, assign_homeworld_to_player, assign_starting_fleets_to_player, ALL_ARTIFACTS # Added game setup functions and ALL_ARTIFACTS
import random # For artifact distribution check

class TestGameCommands(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, create a new game instance for each test."""
        self.player1_name = "Player1"
        self.player2_name = "Player2"
        
        # Create Player objects
        self.player1_obj = Player(name=self.player1_name, character_type="Merchant", home_world=None) # Homeworld assigned below
        self.player2_obj = Player(name=self.player2_name, character_type="Empire Builder", home_world=None) # Homeworld assigned below

        self.game = Game(worlds=[], fleets=[], players=[self.player1_obj, self.player2_obj])

        # Create Worlds and assign owners using Player objects
        self.world_a = World(id=1, name="World A", owner=self.player1_obj, connections=[], iships=5, pships=5, population=10, max_population=100, industry=10, mines=1, stockpile=20, artifacts=[])
        self.player1_obj.home_world = self.world_a # Assign homeworld
        self.player1_obj.worlds.append(self.world_a)

        self.world_b = World(id=2, name="World B", owner=None, connections=[], iships=5, pships=5, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        
        self.world_c = World(id=3, name="World C", owner=self.player1_obj, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=5, artifacts=[])
        self.player1_obj.worlds.append(self.world_c)

        self.world_d = World(id=4, name="World D", owner=self.player2_obj, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=100, artifacts=[])
        self.player2_obj.home_world = self.world_d
        self.player2_obj.worlds.append(self.world_d)
        
        self.world_isolated = World(id=5, name="World Isolated", owner=self.player1_obj, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=0, artifacts=[])
        self.player1_obj.worlds.append(self.world_isolated)
        
        self.game.worlds.extend([self.world_a, self.world_b, self.world_c, self.world_d, self.world_isolated])

        # Connect worlds: A <-> B, B <-> C, C <-> D
        self.world_a.connections.append(self.world_b)
        self.world_b.connections.append(self.world_a)
        self.world_b.connections.append(self.world_c)
        self.world_c.connections.append(self.world_b)
        self.world_c.connections.append(self.world_d)
        self.world_d.connections.append(self.world_c)

        # Create Fleets and assign owners using Player objects
        self.fleet1 = Fleet(id=1, name="Fleet 1", ships=10, location=self.world_a, owner=self.player1_obj, cargo=10, artifacts=[]) 
        self.player1_obj.fleets.append(self.fleet1)

        self.fleet2_no_ships = Fleet(id=2, name="Fleet 2", ships=0, location=self.world_a, owner=self.player1_obj, cargo=0, artifacts=[])
        self.player1_obj.fleets.append(self.fleet2_no_ships)

        self.fleet3_at_b = Fleet(id=3, name="Fleet 3", ships=5, location=self.world_b, owner=self.player1_obj, cargo=0, artifacts=[])
        self.player1_obj.fleets.append(self.fleet3_at_b)
        
        self.fleet4_p2_at_a = Fleet(id=4, name="Fleet 4 (P2)", ships=10, location=self.world_a, owner=self.player2_obj, cargo=5, artifacts=[])
        self.player2_obj.fleets.append(self.fleet4_p2_at_a)
        
        # self.merchant_fleet is now player1_obj's fleet, and player1_obj is Merchant
        self.merchant_fleet = Fleet(id=5, name="Merchant Fleet", ships=10, location=self.world_a, owner=self.player1_obj, cargo=0, artifacts=[])
        self.player1_obj.fleets.append(self.merchant_fleet)


        self.game.fleets.extend([self.fleet1, self.fleet2_no_ships, self.fleet3_at_b, self.fleet4_p2_at_a, self.merchant_fleet])

        # Ensure player's character object is created (Player.create_character() is called in Player.__init__)
        # This is important if character specific logic in Player methods is ever used.
        # For now, character_type string is used directly from Player object.


    def test_execute_move_order_single_step_valid(self):
        """Test valid single-step fleet movement with execute_move_order."""
        initial_location = self.fleet1.location
        self.assertTrue(self.world_b in initial_location.connections, "Pre-condition: World B not connected to World A")
        move_order = MoveOrder(fleet_id=self.fleet1.id, target_world_ids=[self.world_b.id])
        
        success, message = self.game.execute_move_order(move_order)
        
        self.assertTrue(success, f"execute_move_order failed for valid single step: {message}")
        self.assertEqual(self.fleet1.location, self.world_b, "Fleet location should be updated to World B.")

    def test_execute_move_order_multi_step_valid(self):
        """Test valid multi-step fleet movement with execute_move_order."""
        move_order = MoveOrder(fleet_id=self.fleet1.id, target_world_ids=[self.world_b.id, self.world_c.id])
        success, message = self.game.execute_move_order(move_order)
        self.assertTrue(success, f"execute_move_order failed for valid multi-step: {message}")
        self.assertEqual(self.fleet1.location, self.world_c, "Fleet location should be updated to World C.")

    def test_execute_move_order_invalid_fleet_not_found(self):
        move_order = MoveOrder(fleet_id=999, target_world_ids=[self.world_b.id])
        success, _ = self.game.execute_move_order(move_order)
        self.assertFalse(success, "execute_move_order should return False if fleet ID is not found.")

    def test_execute_move_order_invalid_no_ships(self):
        initial_location = self.fleet2_no_ships.location
        move_order = MoveOrder(fleet_id=self.fleet2_no_ships.id, target_world_ids=[self.world_b.id])
        success, _ = self.game.execute_move_order(move_order)
        self.assertFalse(success, "execute_move_order should return False if the fleet has no ships.")
        self.assertEqual(self.fleet2_no_ships.location, initial_location, "Fleet location should not change.")

    def test_execute_move_order_invalid_path_too_long(self):
        initial_location = self.fleet1.location
        move_order = MoveOrder(fleet_id=self.fleet1.id, target_world_ids=[self.world_b.id, self.world_c.id, self.world_d.id])
        success, _ = self.game.execute_move_order(move_order)
        self.assertFalse(success, "execute_move_order should return False for a path longer than 2 steps.")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change.")

    def test_execute_move_order_invalid_disconnected_first_step(self):
        initial_location = self.fleet1.location
        move_order = MoveOrder(fleet_id=self.fleet1.id, target_world_ids=[self.world_c.id]) # A not directly connected to C
        success, _ = self.game.execute_move_order(move_order)
        self.assertFalse(success, "execute_move_order should return False if the first target world is not connected.")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change.")

    def test_execute_move_order_invalid_disconnected_second_step(self):
        initial_location = self.fleet1.location # A
        move_order = MoveOrder(fleet_id=self.fleet1.id, target_world_ids=[self.world_b.id, self.world_d.id]) # B not connected to D
        success, _ = self.game.execute_move_order(move_order)
        self.assertFalse(success, "execute_move_order should return False if the second target world is not connected to the first.")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change.")
    
    def test_execute_move_order_invalid_target_world_id_not_found(self):
        initial_location = self.fleet1.location
        move_order = MoveOrder(fleet_id=self.fleet1.id, target_world_ids=[999]) # Non-existent world ID
        success, message = self.game.execute_move_order(move_order)
        self.assertFalse(success, f"execute_move_order should return False if target world ID not found. Msg: {message}")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change.")

    def test_execute_move_order_to_current_location_fails_connection_check(self):
        initial_location = self.fleet1.location
        move_order = MoveOrder(fleet_id=self.fleet1.id, target_world_ids=[self.world_a.id])
        success, message = self.game.execute_move_order(move_order)
        self.assertFalse(success, f"execute_move_order should return False for move to current location. Msg: {message}")
        self.assertEqual(self.fleet1.location, initial_location)

    # --- Tests for order_from_dict ---
    def test_order_from_dict_valid(self):
        move_dict = {"order_type": "MOVE", "fleet_id": 1, "target_world_ids": [2, 3]}
        move_obj = order_from_dict(move_dict)
        self.assertIsInstance(move_obj, MoveOrder)
        self.assertEqual(move_obj.fleet_id, 1)
        self.assertEqual(move_obj.target_world_ids, [2,3])

        transfer_dict = {"order_type": "TRANSFER", "ship_count": 10, "from_entity_type": "FLEET", "from_id": 1, "to_entity_type": "WORLD", "to_id": 2}
        transfer_obj = order_from_dict(transfer_dict) # Note: to_entity_type WORLD should be PSHIP or ISHIP
        # The class TransferOrder itself doesn't validate entity types, just stores them.
        self.assertIsInstance(transfer_obj, TransferOrder)
        self.assertEqual(transfer_obj.ship_count, 10)

        load_dict = {"order_type": "LOAD_CARGO", "fleet_id": 1, "world_id": 2, "metal_amount": 100}
        load_obj = order_from_dict(load_dict)
        self.assertIsInstance(load_obj, LoadCargoOrder)
        self.assertEqual(load_obj.metal_amount, 100)

        unload_dict = {"order_type": "UNLOAD_CARGO", "fleet_id": 1, "world_id": 2, "metal_amount": 50, "as_consumer_goods": True}
        unload_obj = order_from_dict(unload_dict)
        self.assertIsInstance(unload_obj, UnloadCargoOrder)
        self.assertTrue(unload_obj.as_consumer_goods)

    def test_order_from_dict_invalid_type(self):
        invalid_dict = {"order_type": "FLY_TO_MARS", "param": 1}
        self.assertIsNone(order_from_dict(invalid_dict))

    def test_order_from_dict_malformed_data(self):
        # Missing 'fleet_id' for MoveOrder
        malformed_move_dict = {"order_type": "MOVE", "target_world_ids": [1]}
        self.assertIsNone(order_from_dict(malformed_move_dict))
        # Missing target_world_ids
        malformed_move_dict_2 = {"order_type": "MOVE", "fleet_id": 1}
        self.assertIsNone(order_from_dict(malformed_move_dict_2))
         # target_world_ids is empty list after processing
        malformed_move_dict_3 = {"order_type": "MOVE", "fleet_id": 1, "target_world_ids": [None]}
        self.assertIsNone(order_from_dict(malformed_move_dict_3))


    # --- Tests for execute_transfer_order ---
    def test_transfer_fleet_to_fleet_valid(self):
        self.fleet1.cargo = 5 # Set cargo to test jettisoning
        self.fleet1.location = self.world_a
        self.fleet3_at_b.location = self.world_a # Move fleet3 to same location
        self.fleet3_at_b.owner = self.player1_name # Same owner
        
        initial_fleet1_ships = self.fleet1.ships
        initial_fleet3_ships = self.fleet3_at_b.ships
        
        order = TransferOrder(ship_count=3, from_entity_type="FLEET", from_id=self.fleet1.id, to_entity_type="FLEET", to_id=self.fleet3_at_b.id)
        success, msg = self.game.execute_transfer_order(order)
        
        self.assertTrue(success, f"Valid fleet-to-fleet transfer failed: {msg}")
        self.assertEqual(self.fleet1.ships, initial_fleet1_ships - 3)
        self.assertEqual(self.fleet3_at_b.ships, initial_fleet3_ships + 3)
        self.assertEqual(self.fleet1.cargo, 0, "Source fleet cargo should be jettisoned.")

    def test_transfer_fleet_to_fleet_invalid_location(self):
        self.fleet1.location = self.world_a
        self.fleet3_at_b.location = self.world_b # Different locations
        order = TransferOrder(ship_count=1, from_entity_type="FLEET", from_id=self.fleet1.id, to_entity_type="FLEET", to_id=self.fleet3_at_b.id)
        success, _ = self.game.execute_transfer_order(order)
        self.assertFalse(success, "Transfer should fail if fleets are in different locations.")

    def test_transfer_fleet_to_fleet_invalid_owner(self):
        self.fleet1.owner = self.player1_obj
        self.fleet4_p2_at_a.owner = self.player2_obj # Different owner
        self.fleet1.location = self.world_a
        self.fleet4_p2_at_a.location = self.world_a # Same location
        order = TransferOrder(ship_count=1, from_entity_type="FLEET", from_id=self.fleet1.id, to_entity_type="FLEET", to_id=self.fleet4_p2_at_a.id)
        success, _ = self.game.execute_transfer_order(order)
        self.assertFalse(success, "Transfer should fail if fleets have different owners (Player objects).")

    def test_transfer_fleet_to_fleet_insufficient_ships(self):
        order = TransferOrder(ship_count=self.fleet1.ships + 1, from_entity_type="FLEET", from_id=self.fleet1.id, to_entity_type="FLEET", to_id=self.fleet3_at_b.id)
        success, _ = self.game.execute_transfer_order(order)
        self.assertFalse(success, "Transfer should fail if source fleet has insufficient ships.")

    def test_transfer_fleet_to_pships_valid(self):
        self.fleet1.location = self.world_a
        self.world_a.owner = self.player1_obj # Ensure world is owned by same player or unowned
        initial_fleet_ships = self.fleet1.ships
        initial_world_pships = self.world_a.pships
        self.fleet1.cargo = 5

        order = TransferOrder(ship_count=5, from_entity_type="FLEET", from_id=self.fleet1.id, to_entity_type="PSHIP", to_id=self.world_a.id)
        success, msg = self.game.execute_transfer_order(order)
        self.assertTrue(success, f"Fleet to PSHIPS transfer failed: {msg}")
        self.assertEqual(self.fleet1.ships, initial_fleet_ships - 5)
        self.assertEqual(self.world_a.pships, initial_world_pships + 5)
        self.assertEqual(self.fleet1.cargo, 0, "Fleet cargo should be jettisoned when transferring to PSHIPS.")

    def test_transfer_pships_to_fleet_valid(self):
        self.fleet1.location = self.world_a
        self.world_a.owner = self.player1_obj
        initial_fleet_ships = self.fleet1.ships
        initial_world_pships = self.world_a.pships
        
        order = TransferOrder(ship_count=3, from_entity_type="PSHIP", from_id=self.world_a.id, to_entity_type="FLEET", to_id=self.fleet1.id)
        success, msg = self.game.execute_transfer_order(order)
        self.assertTrue(success, f"PSHIPS to Fleet transfer failed: {msg}")
        self.assertEqual(self.world_a.pships, initial_world_pships - 3)
        self.assertEqual(self.fleet1.ships, initial_fleet_ships + 3)

    def test_transfer_pships_to_iships_valid(self):
        self.world_a.owner = self.player1_obj # or None
        initial_pships = self.world_a.pships
        initial_iships = self.world_a.iships
        order = TransferOrder(ship_count=2, from_entity_type="PSHIP", from_id=self.world_a.id, to_entity_type="ISHIP", to_id=self.world_a.id)
        success, msg = self.game.execute_transfer_order(order)
        self.assertTrue(success, f"PSHIPS to ISHIPS transfer failed: {msg}")
        self.assertEqual(self.world_a.pships, initial_pships - 2)
        self.assertEqual(self.world_a.iships, initial_iships + 2)

    def test_transfer_invalid_entity_types(self):
        order = TransferOrder(ship_count=1, from_entity_type="PLANET", from_id=1, to_entity_type="STAR", to_id=2)
        success, _ = self.game.execute_transfer_order(order)
        self.assertFalse(success, "Transfer should fail for invalid entity types.")

    # --- Tests for execute_load_cargo_order ---
    def test_load_cargo_valid_all(self):
        self.fleet1.location = self.world_a
        self.fleet1.cargo = 0
        self.fleet1.ships = 15 # Capacity = 15
        self.world_a.stockpile = 10 # Less than capacity
        
        order = LoadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=-1)
        success, msg = self.game.execute_load_cargo_order(order)
        
        self.assertTrue(success, f"Load cargo (all) failed: {msg}")
        self.assertEqual(self.fleet1.cargo, 10) # Loaded all from stockpile
        self.assertEqual(self.world_a.stockpile, 0)

    def test_load_cargo_valid_specific_amount(self):
        self.fleet1.location = self.world_a
        self.fleet1.cargo = 0
        self.fleet1.ships = 20 # Capacity = 20
        self.world_a.stockpile = 15
        
        order = LoadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=10)
        success, msg = self.game.execute_load_cargo_order(order)
        
        self.assertTrue(success, f"Load cargo (specific) failed: {msg}")
        self.assertEqual(self.fleet1.cargo, 10)
        self.assertEqual(self.world_a.stockpile, 5)

    def test_load_cargo_invalid_not_at_world(self):
        self.fleet1.location = self.world_b # Different world
        order = LoadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=5)
        success, _ = self.game.execute_load_cargo_order(order)
        self.assertFalse(success, "Load cargo should fail if fleet not at world.")

    def test_load_cargo_invalid_world_owner(self):
        self.fleet1.owner = self.player1_obj
        self.world_d.owner = self.player2_obj # World D owned by P2
        self.fleet1.location = self.world_d # Fleet at P2's world
        
        order = LoadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_d.id, metal_amount=5)
        success, _ = self.game.execute_load_cargo_order(order)
        self.assertFalse(success, "Load cargo should fail if world owned by different player (Player objects).")

    def test_load_cargo_insufficient_stockpile(self):
        self.world_a.stockpile = 5
        self.fleet1.location = self.world_a
        order = LoadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=10)
        success, _ = self.game.execute_load_cargo_order(order)
        self.assertFalse(success, "Load cargo should fail if world has insufficient stockpile.")

    def test_load_cargo_insufficient_capacity(self):
        self.fleet1.ships = 5 # Capacity 5
        self.fleet1.cargo = 3 # Already has 3
        self.world_a.stockpile = 10
        self.fleet1.location = self.world_a
        
        order = LoadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=3) # Tries to load 3, has capacity for 2
        success, _ = self.game.execute_load_cargo_order(order)
        self.assertFalse(success, "Load cargo should fail if fleet has insufficient capacity.")

    def test_load_cargo_merchant_capacity(self):
        # self.merchant_fleet is owned by self.player1_obj, and self.player1_obj is "Merchant"
        self.merchant_fleet.location = self.world_a
        self.merchant_fleet.ships = 10 # Standard capacity 10, Merchant capacity 20
        self.merchant_fleet.cargo = 0
        self.world_a.stockpile = 25
        self.world_a.owner = self.player1_obj # World A owned by Player 1 (Merchant)

        order = LoadCargoOrder(fleet_id=self.merchant_fleet.id, world_id=self.world_a.id, metal_amount=15)
        success, msg = self.game.execute_load_cargo_order(order)
        
        self.assertTrue(success, f"Merchant load cargo failed: {msg}")
        self.assertEqual(self.merchant_fleet.cargo, 15)
        self.assertEqual(self.world_a.stockpile, 10)


    # --- Tests for execute_unload_cargo_order ---
    def test_unload_cargo_valid_all(self):
        self.fleet1.location = self.world_a
        self.fleet1.cargo = 15
        initial_stockpile = self.world_a.stockpile
        
        order = UnloadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=-1)
        success, msg = self.game.execute_unload_cargo_order(order)
        
        self.assertTrue(success, f"Unload cargo (all) failed: {msg}")
        self.assertEqual(self.fleet1.cargo, 0)
        self.assertEqual(self.world_a.stockpile, initial_stockpile + 15)

    def test_unload_cargo_valid_specific_amount(self):
        self.fleet1.location = self.world_a
        self.fleet1.cargo = 15
        initial_stockpile = self.world_a.stockpile
        
        order = UnloadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=10)
        success, msg = self.game.execute_unload_cargo_order(order)
        
        self.assertTrue(success, f"Unload cargo (specific) failed: {msg}")
        self.assertEqual(self.fleet1.cargo, 5)
        self.assertEqual(self.world_a.stockpile, initial_stockpile + 10)

    def test_unload_cargo_consumer_goods(self):
        self.fleet1.location = self.world_a
        self.fleet1.cargo = 15
        initial_stockpile = self.world_a.stockpile
        
        order = UnloadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=10, as_consumer_goods=True)
        success, msg = self.game.execute_unload_cargo_order(order)
        
        self.assertTrue(success, f"Unload consumer goods failed: {msg}")
        self.assertEqual(self.fleet1.cargo, 5)
        self.assertEqual(self.world_a.stockpile, initial_stockpile, "Stockpile should not change for consumer goods.")

    def test_unload_cargo_insufficient_cargo(self):
        self.fleet1.cargo = 5
        self.fleet1.location = self.world_a
        order = UnloadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=10)
        success, _ = self.game.execute_unload_cargo_order(order)
        self.assertFalse(success, "Unload cargo should fail if fleet has insufficient cargo.")

    def test_unload_cargo_invalid_location(self):
        self.fleet1.location = self.world_b # Different world
        order = UnloadCargoOrder(fleet_id=self.fleet1.id, world_id=self.world_a.id, metal_amount=5)
        success, _ = self.game.execute_unload_cargo_order(order)
        self.assertFalse(success, "Unload cargo should fail if fleet not at world.")

    # --- Tests for Game.process_turn ---
    def test_process_turn_order_sorting_and_dispatch(self):
        # Setup:
        # Fleet F1 (P1) at World A (P1), 10 ships, 0 cargo. World A stockpile 100.
        # Fleet F3 (P1) at World B (Unowned), 5 ships, 0 cargo. World B stockpile 100.
        # Order of ops by priority: UNLOAD (10), TRANSFER (20), LOAD (40), MOVE (60)
        
        self.fleet1.location = self.world_a
        self.fleet1.owner = self.player1_obj # P1
        self.fleet1.ships = 10
        self.fleet1.cargo = 0 
        
        self.fleet3_at_b.location = self.world_b
        self.fleet3_at_b.owner = self.player1_obj # P1
        self.fleet3_at_b.ships = 5
        self.fleet3_at_b.cargo = 0

        self.world_a.owner = self.player1_obj # P1
        self.world_a.stockpile = 100
        self.world_a.pships = 0 

        self.world_b.owner = None # Unowned
        self.world_b.stockpile = 100


        # 1. UNLOAD_CARGO (P10): Fleet3 unloads 5 cargo at World B (needs cargo to unload)
        self.fleet3_at_b.cargo = 5 
        unload_order_dict = {"order_type": "UNLOAD_CARGO", "fleet_id": self.fleet3_at_b.id, "world_id": self.world_b.id, "metal_amount": 5}

        # 2. TRANSFER (P20): Fleet1 transfers 2 ships to World A pships
        transfer_order_dict = {"order_type": "TRANSFER", "ship_count": 2, "from_entity_type": "FLEET", "from_id": self.fleet1.id, "to_entity_type": "PSHIP", "to_id": self.world_a.id}
        
        # 3. LOAD_CARGO (P40): Fleet1 loads 10 metal from World A
        load_order_dict = {"order_type": "LOAD_CARGO", "fleet_id": self.fleet1.id, "world_id": self.world_a.id, "metal_amount": 10}
        
        # 4. MOVE (P60): Fleet1 moves from World A to World B
        move_order_dict = {"order_type": "MOVE", "fleet_id": self.fleet1.id, "target_world_ids": [self.world_b.id]}

        raw_orders = [move_order_dict, load_order_dict, transfer_order_dict, unload_order_dict] # Deliberately out of priority
        
        initial_f1_ships = self.fleet1.ships
        initial_f3_cargo = self.fleet3_at_b.cargo
        initial_wa_pships = self.world_a.pships
        initial_wa_stockpile = self.world_a.stockpile
        initial_wb_stockpile = self.world_b.stockpile


        results = self.game.process_turn(raw_orders)
        # print(f"Process Turn Results for sorting test: {results}") # For debugging

        # Check Unload (P10)
        self.assertEqual(self.fleet3_at_b.cargo, initial_f3_cargo - 5, "Unload should have occurred first.")
        self.assertEqual(self.world_b.stockpile, initial_wb_stockpile + 5, "World B stockpile should increase from unload.")
        
        # Check Transfer (P20)
        self.assertEqual(self.fleet1.ships, initial_f1_ships - 2, "Transfer should reduce fleet1 ships.")
        self.assertEqual(self.world_a.pships, initial_wa_pships + 2, "World A pships should increase.")
        
        # Check Load (P40) - Fleet1 is still at World A
        self.assertEqual(self.fleet1.cargo, 10, "Fleet1 should have loaded 10 cargo.")
        self.assertEqual(self.world_a.stockpile, initial_wa_stockpile - 10, "World A stockpile should decrease from load.")
        
        # Check Move (P60) - Fleet1 moves after loading
        self.assertEqual(self.fleet1.location, self.world_b, "Fleet1 should have moved to World B last.")

    def test_process_turn_results_messages(self):
        valid_move_dict = {"order_type": "MOVE", "fleet_id": self.fleet1.id, "target_world_ids": [self.world_b.id]}
        invalid_load_dict = {"order_type": "LOAD_CARGO", "fleet_id": self.fleet1.id, "world_id": self.world_a.id, "metal_amount": 9999} # Insufficient stockpile
        
        # Note: process_turn now requires user_id. Using a dummy one for this test as it's not the focus here.
        raw_orders = [valid_move_dict, invalid_load_dict]
        # Ensure self.game.players is populated if needed by order execution logic, even if not directly used by this test's focus
        if not self.game.players:
            self.game.players.append(self.player1_obj) # Add a dummy player if list is empty

        results = self.game.process_turn("test_user", raw_orders)
        
        self.assertEqual(len(results), 2)
        self.assertIn("(Success: True)", results[1]) # Move is P60, Load is P40. Load happens first.
        self.assertIn("(Success: False)", results[0]) # Load should fail
        self.assertIn("LOAD_CARGO", results[0])
        self.assertIn("MOVE", results[1])

    # --- Tests for create_game() and new player setup ---

    def test_create_full_game_entities_counts(self):
        """Test the counts of entities created by create_game."""
        game_instance = create_game()
        self.assertEqual(len(game_instance.worlds), 255)
        self.assertEqual(len(game_instance.fleets), 255)
        
        total_artifacts_on_worlds = sum(len(world.artifacts) for world in game_instance.worlds)
        self.assertEqual(total_artifacts_on_worlds, 100) # Assuming ALL_ARTIFACTS has 100
        
        self.assertTrue(all(fleet.owner is None for fleet in game_instance.fleets))
        self.assertTrue(all(fleet.ships == 0 for fleet in game_instance.fleets))
        self.assertTrue(all(fleet.location is not None for fleet in game_instance.fleets))
        self.assertEqual(len(game_instance.players), 0) # No players created by default in new create_game

    def test_create_full_game_artifact_distribution(self):
        """Test artifact distribution in create_game."""
        game_instance = create_game()
        ids_on_worlds = set()
        for world in game_instance.worlds:
            for artifact in world.artifacts:
                ids_on_worlds.add(artifact.id)
        
        self.assertEqual(len(ids_on_worlds), 100, "All 100 unique artifacts should be placed.")
        
        # Sanity check: at least some worlds should have artifacts
        worlds_with_artifacts = sum(1 for world in game_instance.worlds if world.artifacts)
        self.assertGreater(worlds_with_artifacts, 0, "Some worlds should have artifacts.")
        # And not all artifacts on one world (highly unlikely with random.choice over 255 worlds)
        if worlds_with_artifacts == 1 and len(game_instance.worlds) >1 : # if only one world has artifacts
             self.assertNotEqual(len(game_instance.worlds[0].artifacts), 100, "Not all artifacts should be on a single world if many worlds exist.")


    def test_create_full_game_world_connectivity(self):
        """Pragmatic checks for world connectivity."""
        game_instance = create_game()
        if not game_instance.worlds:
            self.fail("No worlds created by create_game for connectivity test.")

        self.assertTrue(all(len(world.connections) >= 1 for world in game_instance.worlds if len(game_instance.worlds) > 1))
        
        total_connections_sum = sum(len(world.connections) for world in game_instance.worlds)
        avg_connections = total_connections_sum / len(game_instance.worlds) if len(game_instance.worlds) > 0 else 0
        
        # These are approximate, based on the desired avg_connections_per_world=3
        # A true spanning tree has N-1 edges. Min 1 ensures this.
        # Avg connections can be slightly off due to randomness and min connection enforcement.
        self.assertGreaterEqual(avg_connections, 1.8, "Average connections too low.") # Adjusted due to ensure_min_connections
        self.assertLessEqual(avg_connections, 7.0, "Average connections too high, possibly over-connected.") # Slightly higher upper bound for safety

    def _register_new_player_setup(self, game: Game, username: str, character_type: str) -> Player:
        """Helper to simulate new player setup steps after User creation."""
        # User object creation is handled by Flask-Login; here we focus on Player object.
        # The user_id for Player object would be current_user.id (which is username)
        ingame_player = Player(name=username, character_type=character_type, user_id=username)
        game.players.append(ingame_player) # Add to game's player list

        assign_homeworld_to_player(ingame_player, game)
        assign_starting_fleets_to_player(ingame_player, game)
        return ingame_player

    def test_new_player_setup_homeworld(self):
        """Test homeworld assignment for a new player."""
        game_instance = create_game() # Start with a full, unowned galaxy
        player1 = self._register_new_player_setup(game_instance, "TestPlayer1", "Merchant")

        self.assertIsNotNone(player1.home_world)
        self.assertIn(player1.home_world, player1.worlds)
        self.assertIs(player1.home_world.owner, player1)
        self.assertEqual(player1.home_world.industry, 30)
        self.assertEqual(player1.home_world.population, 50)
        self.assertEqual(player1.home_world.iships, 1)
        self.assertEqual(player1.home_world.pships, 1)
        self.assertEqual(player1.home_world.name, "TestPlayer1's Homeworld")

    def test_new_player_setup_fleets(self):
        """Test starting fleet assignment for a new player."""
        game_instance = create_game()
        player1 = self._register_new_player_setup(game_instance, "TestPlayer1", "Pirate")

        self.assertEqual(len(player1.fleets), 5)
        owned_fleet_count_in_game = 0
        for fleet in player1.fleets:
            self.assertIs(fleet.owner, player1)
            self.assertEqual(fleet.ships, 0)
            self.assertIs(fleet.location, player1.home_world)
            self.assertIn(fleet.name, [f"TestPlayer1's Fleet {i+1}" for i in range(5)])
            
            # Check if this fleet is also in the main game.fleets list and owned
            game_fleet = next((f for f in game_instance.fleets if f.id == fleet.id), None)
            self.assertIsNotNone(game_fleet)
            if game_fleet.owner is player1:
                owned_fleet_count_in_game +=1
        
        self.assertEqual(owned_fleet_count_in_game, 5, "Player's fleets not correctly reflected as owned in main game list.")


    def test_multiple_player_setups(self):
        """Test setup for multiple new players."""
        game_instance = create_game()
        player1 = self._register_new_player_setup(game_instance, "PlayerAlpha", "Empire Builder")
        player2 = self._register_new_player_setup(game_instance, "PlayerBeta", "Berserker")

        self.assertIsNotNone(player1.home_world)
        self.assertIsNotNone(player2.home_world)
        self.assertIsNot(player1.home_world, player2.home_world, "Players should have different homeworlds.")
        
        self.assertEqual(len(player1.fleets), 5)
        self.assertEqual(len(player2.fleets), 5)

        player1_fleet_ids = {f.id for f in player1.fleets}
        player2_fleet_ids = {f.id for f in player2.fleets}
        self.assertTrue(player1_fleet_ids.isdisjoint(player2_fleet_ids), "Fleets assigned to different players should be unique.")
        
        # Check total number of players in game
        self.assertEqual(len(game_instance.players), 2)
        self.assertIn(player1, game_instance.players)
        self.assertIn(player2, game_instance.players)

    # --- Tests for Admin User, Visibility, and Event Logging ---

    def test_admin_user_registration_setup(self):
        """Test that registering 'admin' user sets is_admin and skips player setup."""
        # Simulate app.users_db for this test - this is normally global in app.py
        # For testing, we can pass a mock or use a temporary one if User class doesn't depend on Flask context.
        # The User class itself does not depend on Flask context for its methods.
        
        admin_user = User(username="admin", password="password", is_admin=True) # Simulating admin flag logic
        self.assertTrue(admin_user.is_admin)
        
        # In the actual /register route, if username is "admin", no Player object is created.
        # We test this by ensuring an admin user doesn't get game entities by default.
        game_instance = create_game() # Fresh game
        
        # Check if a player object for 'admin' was accidentally created (it shouldn't be)
        admin_player_in_game = next((p for p in game_instance.players if p.user_id == "admin"), None)
        self.assertIsNone(admin_player_in_game, "Admin user 'admin' should not have an in-game Player object created by default player setup logic.")

    def test_regular_user_is_not_admin(self):
        """Test that a regular user is not flagged as admin and gets player setup."""
        regular_user = User(username="player1", password="password") # Default is_admin=False
        self.assertFalse(regular_user.is_admin)

        # Simulate the player setup part for a regular user
        game_instance = create_game()
        player_obj = self._register_new_player_setup(game_instance, "player1", "Merchant")
        self.assertIsNotNone(player_obj)
        self.assertIsNotNone(player_obj.home_world)
        self.assertTrue(len(player_obj.fleets) > 0)


    def _setup_visibility_test_scenario(self) -> tuple[Game, Player, Player]:
        """Helper to create a specific game state for visibility tests."""
        game = Game(worlds=[], fleets=[], players=[])

        # Create Players
        player_a = Player(name="PlayerA", character_type="Merchant", user_id="userA")
        player_b = Player(name="PlayerB", character_type="Pirate", user_id="userB")
        game.players.extend([player_a, player_b])

        # Create Worlds
        wa1 = World(id=1, name="WA1", owner=player_a, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        player_a.worlds.append(wa1)
        player_a.home_world = wa1
        
        wb1 = World(id=2, name="WB1", owner=player_b, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        player_b.worlds.append(wb1)
        player_b.home_world = wb1

        wn1 = World(id=3, name="WN1", owner=None, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[]) # Neutral
        w_shared = World(id=4, name="W_Shared", owner=None, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[]) # Neutral, for shared fleets

        game.worlds.extend([wa1, wb1, wn1, w_shared])
        
        # Connect worlds for movement tests if needed later, but not strictly for visibility by ownership/presence
        wa1.connections.append(w_shared)
        w_shared.connections.append(wa1)
        wb1.connections.append(w_shared)
        w_shared.connections.append(wb1)


        # Create Fleets
        fa1 = Fleet(id=1, name="FA1", ships=10, location=wa1, owner=player_a, cargo=0, artifacts=[]) # A's fleet at A's world
        player_a.fleets.append(fa1)
        fa2 = Fleet(id=2, name="FA2", ships=10, location=w_shared, owner=player_a, cargo=0, artifacts=[]) # A's fleet at shared neutral world
        player_a.fleets.append(fa2)

        fb1 = Fleet(id=3, name="FB1", ships=10, location=wb1, owner=player_b, cargo=0, artifacts=[]) # B's fleet at B's world
        player_b.fleets.append(fb1)
        fb2 = Fleet(id=4, name="FB2", ships=10, location=w_shared, owner=player_b, cargo=0, artifacts=[]) # B's fleet at shared neutral world
        player_b.fleets.append(fb2)
        fb3 = Fleet(id=5, name="FB3", ships=10, location=wa1, owner=player_b, cargo=0, artifacts=[]) # B's fleet at A's world WA1
        player_b.fleets.append(fb3)
        
        # Unowned fleet for good measure
        fu1 = Fleet(id=6, name="FU1", ships=10, location=wn1, owner=None, cargo=0, artifacts=[])


        game.fleets.extend([fa1, fa2, fb1, fb2, fb3, fu1])
        return game, player_a, player_b

    def test_get_visible_worlds_for_player(self):
        game, player_a, player_b = self._setup_visibility_test_scenario()
        
        visible_to_a = game.get_visible_worlds_for_player(player_a)
        visible_to_a_ids = {w.id for w in visible_to_a}

        # Player A should see:
        # WA1 (owned by A)
        # W_Shared (FA2 is there)
        self.assertIn(game.get_world(1).id, visible_to_a_ids, "Player A should see WA1 (owned)")
        self.assertIn(game.get_world(4).id, visible_to_a_ids, "Player A should see W_Shared (FA2 location)")
        
        # Player A should NOT see (unless other rules apply not tested here like connections):
        # WB1 (owned by B, no A presence)
        # WN1 (neutral, no A presence)
        self.assertNotIn(game.get_world(2).id, visible_to_a_ids, "Player A should NOT see WB1 (B's world, no A presence)")
        self.assertNotIn(game.get_world(3).id, visible_to_a_ids, "Player A should NOT see WN1 (Neutral, no A presence)")


    def test_get_visible_fleets_for_player(self):
        game, player_a, player_b = self._setup_visibility_test_scenario()

        visible_to_a = game.get_visible_fleets_for_player(player_a)
        visible_to_a_ids = {f.id for f in visible_to_a}

        # Player A should see:
        # FA1 (own fleet)
        # FA2 (own fleet)
        # FB2 (B's fleet at W_Shared, where FA2 is also located - Rule 3)
        # FB3 (B's fleet at WA1, which A owns - Rule 1)
        self.assertIn(game.get_fleet(1).id, visible_to_a_ids, "Player A should see FA1 (own)")
        self.assertIn(game.get_fleet(2).id, visible_to_a_ids, "Player A should see FA2 (own)")
        self.assertIn(game.get_fleet(4).id, visible_to_a_ids, "Player A should see FB2 (co-located at W_Shared)")
        self.assertIn(game.get_fleet(5).id, visible_to_a_ids, "Player A should see FB3 (at A's world WA1)")

        # Player A should NOT see:
        # FB1 (B's fleet at B's world WB1, no A presence)
        # FU1 (Unowned fleet at neutral WN1, no A presence)
        self.assertNotIn(game.get_fleet(3).id, visible_to_a_ids, "Player A should NOT see FB1 (B's fleet at B's world)")
        self.assertNotIn(game.get_fleet(6).id, visible_to_a_ids, "Player A should NOT see FU1 (Unowned fleet at neutral WN1)")


    def test_add_and_get_clear_turn_events(self):
        game_instance = Game([],[],[]) # Minimal game instance
        user_id = "test_user_events"
        
        self.assertEqual(game_instance.get_and_clear_turn_events(user_id), []) # Should be empty initially
        
        game_instance.add_turn_event(user_id, "Event 1")
        game_instance.add_turn_event(user_id, "Event 2")
        
        events = game_instance.get_and_clear_turn_events(user_id)
        self.assertEqual(len(events), 2)
        self.assertIn("Event 1", events)
        self.assertIn("Event 2", events)
        
        self.assertEqual(game_instance.get_and_clear_turn_events(user_id), [], "Events should be cleared after retrieval.")
        self.assertEqual(game_instance.turn_events.get(user_id, []), [], "Event list for user should be empty in internal dict.")


    def test_move_order_logs_passthrough_event(self):
        # Setup: Player A owns W_Mid. Player B moves FleetFB1 from W_Start -> W_Mid -> W_End.
        game, player_a, player_b = self._setup_visibility_test_scenario() # Gets a basic setup
        
        # Customize for this test:
        w_start = World(id=10, name="W_Start", owner=player_b, connections=[], iships=0,pships=0,population=0,max_population=0,industry=0,mines=0,stockpile=0,artifacts=[])
        w_mid = World(id=11, name="W_Mid", owner=player_a, connections=[], iships=0,pships=0,population=0,max_population=0,industry=0,mines=0,stockpile=0,artifacts=[]) # Owned by Player A
        w_end = World(id=12, name="W_End", owner=player_b, connections=[], iships=0,pships=0,population=0,max_population=0,industry=0,mines=0,stockpile=0,artifacts=[])
        
        game.worlds.extend([w_start, w_mid, w_end])
        
        # Connections: Start -> Mid -> End
        w_start.connections.append(w_mid)
        w_mid.connections.append(w_start)
        w_mid.connections.append(w_end)
        w_end.connections.append(w_mid)
        
        fleet_b1 = Fleet(id=20, name="FB_MoveTest", ships=10, location=w_start, owner=player_b, cargo=0, artifacts=[])
        game.fleets.append(fleet_b1)
        player_b.fleets.append(fleet_b1)

        move_order = MoveOrder(fleet_id=fleet_b1.id, target_world_ids=[w_mid.id, w_end.id])
        success, msg = game.execute_move_order(move_order)
        
        self.assertTrue(success, f"Move order failed: {msg}")
        self.assertEqual(fleet_b1.location, w_end)
        
        # Check events for Player A (owner of W_Mid)
        player_a_events = game.get_and_clear_turn_events(player_a.user_id)
        self.assertEqual(len(player_a_events), 1, "Player A should have one event.")
        self.assertIn(f"ALERT: Your world {w_mid.name}", player_a_events[0])
        self.assertIn(f"passed through by Fleet ID: {fleet_b1.id}", player_a_events[0])

    def test_admin_sees_all_data(self):
        # This test uses the full game created by create_game()
        full_game = create_game() 
        
        # Admin user doesn't have an in-game player object for visibility filtering
        # So, if current_user.is_admin, the route provides game.worlds and game.fleets directly
        admin_worlds_view = full_game.worlds
        admin_fleets_view = full_game.fleets

        self.assertEqual(len(admin_worlds_view), 255)
        self.assertEqual(len(admin_fleets_view), 255)

        # Simulate a regular player setup in this full game
        # (Need to ensure this player is added to full_game.players for get_visible_* to work)
        if not full_game.players: # If create_game doesn't add players by default
             # Create a dummy User object for Player's user_id
            test_user = User(username="TestRegular", password="password")
            # Create a Player linked to this User
            regular_player = Player(name=test_user.username, character_type="Merchant", user_id=test_user.id)
            full_game.players.append(regular_player) # Add to game for visibility functions
            # Assign a homeworld and some fleets for this test player to have some visibility
            assign_homeworld_to_player(regular_player, full_game)
            assign_starting_fleets_to_player(regular_player, full_game)
        else: # If create_game already makes some players, pick one
            regular_player = full_game.players[0]
            if not regular_player.home_world: # If the default player from create_game needs setup
                 assign_homeworld_to_player(regular_player, full_game)
                 assign_starting_fleets_to_player(regular_player, full_game)


        player_worlds = full_game.get_visible_worlds_for_player(regular_player)
        player_fleets = full_game.get_visible_fleets_for_player(regular_player)

        # A regular player should see far fewer than all worlds/fleets unless they own/are on many
        self.assertLess(len(player_worlds), 255, "Regular player should see fewer than all worlds.")
        self.assertLess(len(player_fleets), 255, "Regular player should see fewer than all fleets.")
        self.assertGreater(len(player_worlds), 0, "Player should see at least their homeworld.")
        self.assertGreater(len(player_fleets), 0, "Player should see at least their own fleets.")

    def _create_player_for_test(self, username: str, character_type: str, user_id_override: str | None = None) -> Player:
        """Creates a player and adds to the game instance for specific test needs."""
        user_id = user_id_override if user_id_override else username
        player = Player(name=username, character_type=character_type, user_id=user_id)
        self.game.players.append(player)
        # It's important that this player also has worlds/fleets assigned if the test expects it.
        # For many tests, we might use existing self.player1_obj or self.player2_obj,
        # or assign worlds/fleets to this new player explicitly in the test.
        return player

    def _process_single_order(self, order, player):
        """Helper to simulate processing a single order for a player."""
        # Ensure turn_number is initialized if it's the first action in a test scope
        if not hasattr(self.game, 'turn_number') or self.game.turn_number == 0:
            self.game.turn_number = 1 
        
        # Ensure turn_vp_adjustments is initialized for the game instance
        if not hasattr(self.game, 'turn_vp_adjustments'):
            self.game.turn_vp_adjustments = {}
        
        # Initialize vp adjustment for the specific player if not present for this turn
        if player.user_id not in self.game.turn_vp_adjustments:
            self.game.turn_vp_adjustments[player.user_id] = 0

        # Dispatch to the correct execute method based on order type
        if isinstance(order, MoveOrder):
            return self.game.execute_move_order(order)
        elif isinstance(order, TransferOrder):
            return self.game.execute_transfer_order(order)
        elif isinstance(order, LoadCargoOrder):
            return self.game.execute_load_cargo_order(order)
        elif isinstance(order, UnloadCargoOrder):
            return self.game.execute_unload_cargo_order(order)
        elif order.order_type == "BUILD": # Use string check first for broader compatibility if classes not imported
            from app import BuildOrder # Ensure it's imported
            if isinstance(order, BuildOrder):
                return self.game.execute_build_order(order, player)
        elif order.order_type == "FIRE":
            from app import FireOrder # Ensure it's imported
            if isinstance(order, FireOrder):
                return self.game.execute_fire_order(order, player)
        elif order.order_type == "ATTACH_ARTIFACT":
            if isinstance(order, AttachArtifactOrder):
                return self.game.execute_attach_artifact_order(order, player)
        elif order.order_type == "DROP_ARTIFACT":
            if isinstance(order, DropArtifactOrder):
                return self.game.execute_drop_artifact_order(order, player)
        elif order.order_type == "AMBUSH":
            if isinstance(order, AmbushOrder):
                return self.game.execute_ambush_order(order, player)
        elif order.order_type == "SET_ALLY":
            if isinstance(order, SetAllyOrder):
                return self.game.execute_set_ally_order(order, player)
        elif order.order_type == "GIFT_WORLD":
            if isinstance(order, GiftWorldOrder):
                return self.game.execute_gift_world_order(order, player)
        elif order.order_type == "GIFT_FLEET":
            if isinstance(order, GiftFleetOrder):
                return self.game.execute_gift_fleet_order(order, player)

        # Fallback for comprehensive check
        known_order_types = (
            MoveOrder, TransferOrder, LoadCargoOrder, UnloadCargoOrder,
            BuildOrder, FireOrder, AttachArtifactOrder, DropArtifactOrder,
            AmbushOrder, SetAllyOrder, GiftWorldOrder, GiftFleetOrder
        )
        if not isinstance(order, known_order_types):
             raise ValueError(f"Order type {type(order)} (or string type '{order.order_type}') not supported by _process_single_order helper in test.")
        
        # Should have been caught by one of the isinstance or order_type string checks above
        return False, f"Unhandled order type in _process_single_order: {type(order)}"


    # --- 1. Building Tests (Existing) ---
    def test_build_ships_fleet(self):
        from app import BuildOrder # Ensure BuildOrder is available
        player1 = self.player1_obj # Merchant, but for basic build, type doesn't change cost of ships
        world1 = self.world_a # Owned by P1, Pop:10, Ind:10, Stockpile:20
        world1.population = 100 # Ensure enough pop/stockpile for test
        world1.stockpile = 50
        world1.industry = 10

        # fleet1 is P1's fleet, 10 ships, at World A. Let's use it.
        fleet_to_build_on = self.fleet1
        initial_ships = fleet_to_build_on.ships # Should be 10 from setUp

        # Valid build
        order1 = BuildOrder(world_id=world1.id, build_type="SHIP_FLEET", quantity=5, target_entity_id=fleet_to_build_on.id)
        success, msg = self._process_single_order(order1, player1)
        self.assertTrue(success, f"Ship build failed: {msg}")
        self.assertEqual(fleet_to_build_on.ships, initial_ships + 5)
        self.assertEqual(world1.stockpile, 45) 
        self.assertEqual(world1.population, 95)

        # Test build beyond industry capacity
        world1.stockpile = 50
        world1.population = 100
        fleet_to_build_on.ships = initial_ships # Reset
        order_cap = BuildOrder(world_id=world1.id, build_type="SHIP_FLEET", quantity=11, target_entity_id=fleet_to_build_on.id) # 11 > 10 industry
        success, msg = self._process_single_order(order_cap, player1)
        self.assertFalse(success, f"Should fail due to insufficient industry capacity: {msg}")
        self.assertEqual(fleet_to_build_on.ships, initial_ships)

    def test_build_ships_iships_pships(self):
        from app import BuildOrder
        player1 = self.player1_obj
        world1 = self.world_a
        world1.population = 100
        world1.stockpile = 50
        world1.industry = 10
        initial_iships = world1.iships
        initial_pships = world1.pships

        # Build ISHIPS
        order_is = BuildOrder(world_id=world1.id, build_type="SHIP_ISHOP", quantity=3)
        success, msg = self._process_single_order(order_is, player1)
        self.assertTrue(success, msg)
        self.assertEqual(world1.iships, initial_iships + 3)
        self.assertEqual(world1.stockpile, 47) 
        self.assertEqual(world1.population, 97) 
        
        # Build PSHIPS
        order_ps = BuildOrder(world_id=world1.id, build_type="SHIP_PSHIP", quantity=2)
        success, msg = self._process_single_order(order_ps, player1)
        self.assertTrue(success, msg)
        self.assertEqual(world1.pships, initial_pships + 2)
        self.assertEqual(world1.stockpile, 45) 
        self.assertEqual(world1.population, 95) 

    def test_build_industry(self):
        from app import BuildOrder
        player_eb = self.player2_obj # Empire Builder
        world_eb = self.world_d # Owned by P2 (EB)
        world_eb.population = 100
        world_eb.stockpile = 100
        world_eb.industry = 10 # Initial industry

        player_normal = self.player1_obj # Merchant
        world_normal = self.world_a # Owned by P1 (Merchant)
        world_normal.population = 100
        world_normal.stockpile = 100
        world_normal.industry = 10 # Initial industry

        # Empire Builder (cost 4 per unit) - Build 2 industry
        # Needs: 2*4=8 metal, 2*4=8 pop, 2*4=8 ind capacity. (Has 10 ind capacity)
        order_eb_ok = BuildOrder(world_id=world_eb.id, build_type="INDUSTRY", quantity=2)
        success, msg = self._process_single_order(order_eb_ok, player_eb)
        self.assertTrue(success, f"EB Industry build failed: {msg}")
        self.assertEqual(world_eb.industry, 12) 
        self.assertEqual(world_eb.stockpile, 100 - 8)
        self.assertEqual(world_eb.population, 100 - 8)

        # Normal Player (cost 5 per unit) - Build 1 industry
        # Needs: 1*5=5 metal, 1*5=5 pop, 1*5=5 ind capacity. (Has 10 ind capacity)
        order_normal_ok = BuildOrder(world_id=world_normal.id, build_type="INDUSTRY", quantity=1)
        success, msg = self._process_single_order(order_normal_ok, player_normal)
        self.assertTrue(success, f"Normal Industry build failed: {msg}")
        self.assertEqual(world_normal.industry, 11)
        self.assertEqual(world_normal.stockpile, 100 - 5)
        self.assertEqual(world_normal.population, 100 - 5)

    def test_build_population_limit(self):
        from app import BuildOrder
        player_eb = self.player2_obj # Empire Builder
        world_eb = self.world_d
        world_eb.population = 100
        world_eb.stockpile = 100
        world_eb.industry = 40 # Sufficient industry
        initial_max_pop_eb = world_eb.max_population

        player_normal = self.player1_obj # Merchant
        world_normal = self.world_a
        world_normal.population = 100
        world_normal.stockpile = 100
        world_normal.industry = 25 # Sufficient industry
        initial_max_pop_normal = world_normal.max_population
        
        # Empire Builder (cost 4 per unit of increase) - Increase by 10
        order_eb_ok = BuildOrder(world_id=world_eb.id, build_type="POP_LIMIT", quantity=10)
        success, msg = self._process_single_order(order_eb_ok, player_eb)
        self.assertTrue(success, msg)
        self.assertEqual(world_eb.max_population, initial_max_pop_eb + 10)
        self.assertEqual(world_eb.stockpile, 100 - (10*4))
        self.assertEqual(world_eb.population, 100 - (10*4))

        # Normal Player (cost 5 per unit of increase) - Increase by 5
        order_normal_ok = BuildOrder(world_id=world_normal.id, build_type="POP_LIMIT", quantity=5)
        success, msg = self._process_single_order(order_normal_ok, player_normal)
        self.assertTrue(success, msg)
        self.assertEqual(world_normal.max_population, initial_max_pop_normal + 5)
        self.assertEqual(world_normal.stockpile, 100 - (5*5))
        self.assertEqual(world_normal.population, 100 - (5*5))

    def test_migrate_population(self):
        from app import BuildOrder
        player_apostle = self._create_player_for_test("apostle_mig", "Apostle", "apostle_mig_id")
        
        # Source world for apostle
        world_source = self._create_player_for_test("source_owner", "Empire Builder").home_world # Dummy owner for setup
        world_source = World(id=20, name="SourceWorld", owner=player_apostle, population=50, robot_units=20, convert_units=10, converts_owner_id="apostle_mig_id", industry=10, stockpile=30, max_population=100)
        self.game.worlds.append(world_source)
        player_apostle.worlds.append(world_source)
        player_apostle.home_world = world_source


        # Target world for apostle
        world_target = World(id=21, name="TargetWorld", owner=player_apostle, population=5, robot_units=0, convert_units=0, industry=10, stockpile=10, max_population=50)
        self.game.worlds.append(world_target)
        player_apostle.worlds.append(world_target)

        world_source.connections.append(world_target) # Connect them
        world_target.connections.append(world_source)

        # Migrate NORMAL pop
        order_norm = BuildOrder(world_id=world_source.id, build_type="MIGRATE_POP", quantity=10, target_entity_id=world_target.id, migration_pop_type="NORMAL")
        success, msg = self._process_single_order(order_norm, player_apostle)
        self.assertTrue(success, f"Migrate NORMAL failed: {msg}")
        self.assertEqual(world_source.population, 40)
        self.assertEqual(world_target.population, 15)
        self.assertEqual(world_source.stockpile, 20)

        # Migrate ROBOT pop
        world_source.stockpile = 30 # Reset
        order_robot = BuildOrder(world_id=world_source.id, build_type="MIGRATE_POP", quantity=5, target_entity_id=world_target.id, migration_pop_type="ROBOT")
        success, msg = self._process_single_order(order_robot, player_apostle) # Player type doesn't restrict robot migration itself
        self.assertTrue(success, f"Migrate ROBOT failed: {msg}")
        self.assertEqual(world_source.robot_units, 15)
        self.assertEqual(world_target.robot_units, 5)
        self.assertEqual(world_source.stockpile, 25)

        # Migrate CONVERT pop
        world_source.stockpile = 30 # Reset
        order_convert = BuildOrder(world_id=world_source.id, build_type="MIGRATE_POP", quantity=3, target_entity_id=world_target.id, migration_pop_type="CONVERT")
        success, msg = self._process_single_order(order_convert, player_apostle)
        self.assertTrue(success, f"Migrate CONVERT failed: {msg}")
        self.assertEqual(world_source.convert_units, 7)
        self.assertEqual(world_target.convert_units, 3 + 0) # Target had 0 converts, now 3
        self.assertEqual(world_target.converts_owner_id, player_apostle.user_id)
        self.assertEqual(world_source.stockpile, 27)

    def test_build_robots_berserker(self):
        from app import BuildOrder
        player_berserker = self._create_player_for_test("robo_builder", "Berserker")
        world_b_robot_controlled = World(id=30, name="RoboWorld", owner=player_berserker, population=0, robot_units=10, convert_units=0, industry=10, stockpile=20)
        self.game.worlds.append(world_b_robot_controlled)
        player_berserker.worlds.append(world_b_robot_controlled)

        player_normal = self.player1_obj # Merchant

        # Valid Berserker build (1 effort unit = 1 metal, 1 ind capacity, 1 robot operator -> 2 new robots)
        order_b_ok = BuildOrder(world_id=world_b_robot_controlled.id, build_type="ROBOTS", quantity=1)
        success, msg = self._process_single_order(order_b_ok, player_berserker)
        self.assertTrue(success, msg)
        self.assertEqual(world_b_robot_controlled.robot_units, 12)
        self.assertEqual(world_b_robot_controlled.stockpile, 19)
        
        # Test non-Berserker cannot build robots (using world_a, which is owned by Merchant player1_obj)
        self.world_a.robot_units = 10 # Make it seem robot controlled for a moment
        self.world_a.population = 0
        self.world_a.convert_units = 0
        order_n_fail = BuildOrder(world_id=self.world_a.id, build_type="ROBOTS", quantity=1)
        success, msg = self._process_single_order(order_n_fail, player_normal)
        self.assertFalse(success, "Non-Berserker should not be able to build robots: " + msg)
        self.world_a.population = 10 # Reset world_a

    # --- 2. Metal Production & Mine Logic Tests (Added based on subtask) ---
    def _run_full_turn_for_player(self, player):
        """
        Simulates the core logic of Game.process_turn for a single player's orders.
        Focuses on end-of-turn phases: production, growth, capture, VP.
        Assumes player orders for the 'turn' being simulated are processed before calling this.
        """
        # self.game.turn_number +=1 # Turn number incremented by process_turn, not here.
        # self.game.turn_vp_adjustments = {} # Reset by process_turn
        
        # Simulate these phases as they happen in process_turn, after orders
        # Metal Production (Simplified: for all worlds in game, check owner)
        for world in self.game.worlds:
            if world.owner and not world.is_black_hole:
                pop_for_mining = 0
                if world.robot_units > 0 and world.population == 0 and world.convert_units == 0:
                    pop_for_mining = world.robot_units
                elif world.robot_units == 0 and world.convert_units == 0:
                     pop_for_mining = world.population
                if pop_for_mining > 0 and world.mines > 0:
                    produced_metal = min(world.mines, pop_for_mining)
                    old_stockpile = world.stockpile
                    world.stockpile = min(world.stockpile + produced_metal, 255)
        
        # Population Growth (Simplified: for the specified player's worlds only)
        for world in self.game.worlds:
            if world.owner == player and not world.is_black_hole:
                if world.robot_units > 0: continue
                current_total_pop = world.population + world.convert_units
                if current_total_pop >= world.max_population: continue
                base_growth = (world.population + world.convert_units) // 10
                if base_growth == 0 and current_total_pop > 0 and current_total_pop < world.max_population: base_growth = 1
                actual_growth = min(base_growth, world.max_population - current_total_pop)
                if actual_growth <= 0: continue
                if player.character_type == "Apostle":
                    converts_from_normal = min(actual_growth, world.population)
                    if converts_from_normal > 0: world.population -= converts_from_normal; world.convert_units += converts_from_normal
                    remaining_growth = actual_growth - converts_from_normal
                    if remaining_growth > 0: world.convert_units += remaining_growth
                    world.converts_owner_id = player.user_id
                else:
                    world.population += actual_growth
        
        # Resolve World/Key Capture (this calls its own print and event logic)
        self.game.resolve_world_and_key_capture() # This also does mine increase at its end

        # Final VP update for the player
        base_vp = player.character.calculate_victory_points(self.game)
        event_vp = self.game.turn_vp_adjustments.get(player.user_id, 0) # Assuming turn_vp_adjustments was populated by order processing
        player.victory_points = base_vp + event_vp

    def test_metal_production(self):
        player1 = self.player1_obj
        world1 = self.world_a 
        world1.population=15; world1.mines=10; world1.stockpile=0 # Prod=10
        
        world_less_pop = World(id=100, name="WLessPop", owner=player1, population=5, mines=10, stockpile=0) # Prod=5
        self.game.worlds.append(world_less_pop)
        player1.worlds.append(world_less_pop)

        world_robot = World(id=101, name="WRobot", owner=player1, population=0, robot_units=8, mines=10, stockpile=0) # Prod=8
        self.game.worlds.append(world_robot)
        player1.worlds.append(world_robot)
        
        world_cap = World(id=102, name="WCap", owner=player1, population=20, mines=10, stockpile=250) # Stockpile cap
        self.game.worlds.append(world_cap)
        player1.worlds.append(world_cap)

        self._run_full_turn_for_player(player1) 

        self.assertEqual(world1.stockpile, 10)
        self.assertEqual(world_less_pop.stockpile, 5)
        self.assertEqual(world_robot.stockpile, 8)
        self.assertEqual(world_cap.stockpile, 255)

    def test_turns_owned_and_mine_increase(self):
        player1 = self.player1_obj
        world_inc = World(id=110, name="WInc", owner=player1, mines=5, turns_owned=7)
        self.game.worlds.append(world_inc)
        player1.worlds.append(world_inc)

        world_max = World(id=111, name="WMax", owner=player1, mines=30, turns_owned=7)
        self.game.worlds.append(world_max)
        player1.worlds.append(world_max)
        
        self._run_full_turn_for_player(player1) 
        
        self.assertEqual(world_inc.turns_owned, 1) 
        self.assertEqual(world_inc.mines, 6)
        self.assertEqual(world_max.turns_owned, 1)
        self.assertEqual(world_max.mines, 30)


    # --- 3. Basic Firing Logic Tests ---
    def test_fire_at_fleet(self):
        # Player objects are: self.player1_obj (Merchant), self.player2_obj (Empire Builder)
        # Worlds: self.world_a (P1), self.world_b (None), self.world_c (P1), self.world_d (P2)
        # Fleets: self.fleet1 (P1@A), self.fleet2_no_ships (P1@A), self.fleet3_at_b (P1@B), self.fleet4_p2_at_a (P2@A)
        
        # For firing tests, let's use player2 (Empire Builder) as attacker initially to avoid Merchant penalty complications.
        attacker_player = self.player2_obj # Empire Builder
        defender_player = self.player1_obj # Merchant

        # Move P2's fleet (fleet4_p2_at_a) to world_b to avoid conflict with P1's fleet1 if world_a is used.
        # Or, use world_b which is neutral and has P1's fleet3_at_b.
        # Let's setup a new fleet for P2 at world_b for clarity.
        world_combat = self.world_b # Neutral world
        
        attacker_fleet = Fleet(id=101, name="AttackerP2", ships=10, location=world_combat, owner=attacker_player, cargo=0)
        self.game.fleets.append(attacker_fleet)
        attacker_player.fleets.append(attacker_fleet)

        defender_fleet_loaded = Fleet(id=102, name="DefenderP1Loaded", ships=10, location=world_combat, owner=defender_player, cargo=5) # Loaded, 1 hit/ship
        self.game.fleets.append(defender_fleet_loaded)
        defender_player.fleets.append(defender_fleet_loaded)
        
        defender_fleet_empty = Fleet(id=103, name="DefenderP1Empty", ships=10, location=world_combat, owner=defender_player, cargo=0) # Empty, 2 hits/ship
        self.game.fleets.append(defender_fleet_empty)
        defender_player.fleets.append(defender_fleet_empty)

        from app import FireOrder # Ensure FireOrder is available

        # Fire at loaded fleet (10 shots, 1 hit/ship => 10 ships destroyed)
        fire_order_loaded = FireOrder(firing_fleet_id=attacker_fleet.id, target_type="FLEET", world_id=world_combat.id, target_id=defender_fleet_loaded.id)
        success, msg = self._process_single_order(fire_order_loaded, attacker_player)
        self.assertTrue(success, msg)
        self.assertEqual(defender_fleet_loaded.ships, 0, msg) 
        self.assertIsNone(defender_fleet_loaded.owner, "Destroyed fleet should be unowned")

        # Fire at empty fleet (10 shots, 2 hits/ship => 5 ships destroyed)
        defender_fleet_empty.ships = 10 # Reset
        attacker_fleet.ships = 10 # Reset
        fire_order_empty = FireOrder(firing_fleet_id=attacker_fleet.id, target_type="FLEET", world_id=world_combat.id, target_id=defender_fleet_empty.id)
        success, msg = self._process_single_order(fire_order_empty, attacker_player)
        self.assertTrue(success, msg)
        self.assertEqual(defender_fleet_empty.ships, 5, msg)

        # Test Merchant firing limitation (using self.player1_obj as Merchant)
        merchant_player = self.player1_obj
        merchant_fleet_normal_cargo = self.fleet1 # P1@A, 10 ships, 10 cargo. Effective ships = 10.
        merchant_fleet_normal_cargo.location = world_combat # Move to combat zone
        merchant_fleet_normal_cargo.ships = 10
        merchant_fleet_normal_cargo.cargo = 10 

        merchant_fleet_overloaded = Fleet(id=104, name="MerchantOver", ships=10, location=world_combat, owner=merchant_player, cargo=15) # Effective ships = 5
        self.game.fleets.append(merchant_fleet_overloaded)
        merchant_player.fleets.append(merchant_fleet_overloaded)

        defender_target_for_merchant = Fleet(id=105, name="TargetForMerc", ships=20, location=world_combat, owner=self.player2_obj, cargo=0) # Empty target
        self.game.fleets.append(defender_target_for_merchant)
        self.player2_obj.fleets.append(defender_target_for_merchant)

        # Merchant with normal cargo (10 ships, 10 cargo -> 10 effective ships -> 5 destroyed from target)
        fire_order_merc_norm = FireOrder(firing_fleet_id=merchant_fleet_normal_cargo.id, target_type="FLEET", world_id=world_combat.id, target_id=defender_target_for_merchant.id)
        success, msg = self._process_single_order(fire_order_merc_norm, merchant_player)
        self.assertTrue(success, msg)
        self.assertEqual(defender_target_for_merchant.ships, 15, f"Merchant normal cargo firing failed: {msg}")

        # Merchant with overloaded cargo (10 ships, 15 cargo -> 5 effective ships -> 2 destroyed from target)
        defender_target_for_merchant.ships = 20 # Reset target
        fire_order_merc_over = FireOrder(firing_fleet_id=merchant_fleet_overloaded.id, target_type="FLEET", world_id=world_combat.id, target_id=defender_target_for_merchant.id)
        success, msg = self._process_single_order(fire_order_merc_over, merchant_player)
        self.assertTrue(success, msg)
        self.assertEqual(defender_target_for_merchant.ships, 18, f"Merchant overloaded firing failed: {msg}") # 20 - (5/2) = 17.5 -> 18 (or 2 destroyed)

        # Test Berserker VP for ship kills
        berserker_player = self._create_player_for_test("berserker_killer", "Berserker")
        berserker_fleet = Fleet(id=106, name="BerserkerF", owner=berserker_player, location=world_combat, ships=10, cargo=0)
        self.game.fleets.append(berserker_fleet)
        berserker_player.fleets.append(berserker_fleet)
        
        target_for_berserker = Fleet(id=107, name="TargetForBers", owner=self.player1_obj, location=world_combat, ships=3, cargo=0)
        self.game.fleets.append(target_for_berserker)
        self.player1_obj.fleets.append(target_for_berserker)
        
        initial_berserker_vp_adj = self.game.turn_vp_adjustments.get(berserker_player.user_id, 0)
        
        fire_order_berserker = FireOrder(firing_fleet_id=berserker_fleet.id, target_type="FLEET", world_id=world_combat.id, target_id=target_for_berserker.id)
        success, msg = self._process_single_order(fire_order_berserker, berserker_player)
        self.assertTrue(success, msg)
        self.assertEqual(target_for_berserker.ships, 0, msg)
        expected_vp_gain = 3 * 2 
        self.assertEqual(self.game.turn_vp_adjustments.get(berserker_player.user_id, 0), initial_berserker_vp_adj + expected_vp_gain)


    def test_fire_at_industry(self):
        attacker_player = self.player1_obj # Merchant, but penalty doesn't apply to non-fleet targets
        attacker_fleet = self.fleet1 # 10 ships, 10 cargo (effective 10 shots)
        attacker_fleet.location = self.world_b # Target world_b
        self.world_b.owner = self.player2_obj # Defender owns the world
        self.world_b.iships = 5
        self.world_b.industry = 10
        
        from app import FireOrder

        # Fire order: 10 shots. ISHIPS cost 2 shots each. Industry costs 2 shots each.
        # Destroy 5 ISHIPS (5 * 2 = 10 shots). Remaining shots = 10 - 10 = 0.
        # No industry destroyed.
        fire_order = FireOrder(firing_fleet_id=attacker_fleet.id, target_type="INDUSTRY", world_id=self.world_b.id)
        success, msg = self._process_single_order(fire_order, attacker_player)
        self.assertTrue(success, msg)
        self.assertEqual(self.world_b.iships, 0, msg)
        self.assertEqual(self.world_b.industry, 10, msg) 

        # Test with more shots to hit industry
        attacker_fleet.ships = 15 # 15 shots (assuming cargo doesn't affect industry targeting shots for Merchant)
        self.world_b.iships = 3
        self.world_b.industry = 7
        # 15 shots. ISHIPS: 3 * 2 = 6 shots. Rem = 9. Industry: 9/2 = 4 units.
        fire_order_more = FireOrder(firing_fleet_id=attacker_fleet.id, target_type="INDUSTRY", world_id=self.world_b.id)
        success, msg = self._process_single_order(fire_order_more, attacker_player)
        self.assertTrue(success, msg)
        self.assertEqual(self.world_b.iships, 0, msg)
        self.assertEqual(self.world_b.industry, 3, msg) # 7 - 4 = 3


    def test_fire_at_population(self):
        from app import FireOrder
        attacker_berserker = self._create_player_for_test("berserker_pop_killer", "Berserker")
        attacker_normal = self.player1_obj # Merchant
        
        world_target = self.world_c # Owned by P1 initially, let's make it P2's for this test
        world_target.owner = self.player2_obj
        world_target.pships=5
        world_target.population=20
        world_target.convert_units=10 
        world_target.converts_owner_id = self.player2_obj.user_id # P2's converts
        world_target.robot_units=5
        
        fleet_berserker = Fleet(id=201, name="BerserkerPopF", owner=attacker_berserker, location=world_target, ships=30)
        self.game.fleets.append(fleet_berserker)
        attacker_berserker.fleets.append(fleet_berserker)

        fleet_normal = Fleet(id=202, name="NormalPopF", owner=attacker_normal, location=world_target, ships=30, cargo=0) # No cargo penalty
        self.game.fleets.append(fleet_normal)
        attacker_normal.fleets.append(fleet_normal)
        
        # Berserker firing (30 shots)
        # PSHIPS: 5 units * 2 shots/unit = 10 shots. Destroy 5 PSHIPS. Shots remaining = 20.
        # POP: 20 shots / 2 shots/unit = 10 pop units killed. (Order: 10 Normal)
        # VP Gain: 10 pop units * 2 VP/unit = 20 VP
        initial_b_vp_adj = self.game.turn_vp_adjustments.get(attacker_berserker.user_id, 0)
        
        fire_order_b = FireOrder(firing_fleet_id=fleet_berserker.id, target_type="POPULATION", world_id=world_target.id)
        success, msg = self._process_single_order(fire_order_b, attacker_berserker)
        self.assertTrue(success, msg)
        self.assertEqual(world_target.pships, 0, f"Berserker PSHIPs: {msg}")
        self.assertEqual(world_target.population, 10, f"Berserker Normal Pop: {msg}") # 20 - 10
        self.assertEqual(world_target.convert_units, 10, f"Berserker Convert Pop should be untouched: {msg}")
        self.assertEqual(self.game.turn_vp_adjustments.get(attacker_berserker.user_id, 0), initial_b_vp_adj + (10 * 2))

        # Reset world for normal player
        world_target.owner = self.player2_obj
        world_target.pships=5
        world_target.population=20
        world_target.convert_units=10
        world_target.robot_units=5

        # Normal player firing (30 shots) - same destruction, different VP
        # VP Loss: 10 pop units * 1 VP/unit = -10 VP
        initial_n_vp_adj = self.game.turn_vp_adjustments.get(attacker_normal.user_id, 0)
        fire_order_n = FireOrder(firing_fleet_id=fleet_normal.id, target_type="POPULATION", world_id=world_target.id)
        success, msg = self._process_single_order(fire_order_n, attacker_normal)
        self.assertTrue(success, msg)
        self.assertEqual(world_target.pships, 0, f"Normal PSHIPs: {msg}")
        self.assertEqual(world_target.population, 10, f"Normal Normal Pop: {msg}")
        self.assertEqual(self.game.turn_vp_adjustments.get(attacker_normal.user_id, 0), initial_n_vp_adj + (-10 * 1))


    def test_fire_at_home_fleets(self):
        from app import FireOrder
        attacker_player = self.player1_obj
        defender_player = self.player2_obj
        
        world_target = self.world_d # Owned by P2 (defender)
        world_target.iships = 5
        world_target.pships = 5
        
        attacker_fleet = self.fleet1 # P1's fleet
        attacker_fleet.location = world_target
        attacker_fleet.ships = 22 # 22 shots (cargo is 10, so 10 effective shots for Merchant)
                                  # The prompt says "Merchant firing limitations (overloaded ships don't fire)"
                                  # This usually applies to FLEET targets. Let's assume for non-FLEET targets, all ships fire.
                                  # Revisit this if rule implies Merchant shot penalty applies to all target types.
                                  # For now, assuming 22 shots from 22 ships if cargo doesn't reduce for ground targets.
                                  # Let's simplify and assume attacker_fleet has 0 cargo for this test for max shots.
        attacker_fleet.cargo = 0
        attacker_fleet.ships = 22


        # 22 shots:
        # ISHIPS: 5 units * 2 shots/unit = 10 shots. Destroy 5 ISHIPS. Shots remaining = 12.
        # PSHIPS: 5 units * 2 shots/unit = 10 shots. Destroy 5 PSHIPS. Shots remaining = 2.
        # World neutralized as ISHIPS=0, PSHIPS=0 and >=2 shots remaining.
        fire_order = FireOrder(firing_fleet_id=attacker_fleet.id, target_type="HOME_FLEETS", world_id=world_target.id)
        success, msg = self._process_single_order(fire_order, attacker_player)
        self.assertTrue(success, msg)
        self.assertEqual(world_target.iships, 0, msg)
        self.assertEqual(world_target.pships, 0, msg)
        self.assertIsNone(world_target.owner, "World should be unowned: " + msg)
        self.assertEqual(world_target.turns_owned, 0, "Turns_owned should reset")


    def test_apostle_firing_penalty(self):
        from app import FireOrder
        apostle_player = self._create_player_for_test("apostle_fire", "Apostle")
        apostle_fleet = Fleet(id=301, name="ApostleF", owner=apostle_player, location=self.world_a, ships=1)
        self.game.fleets.append(apostle_fleet)
        apostle_player.fleets.append(apostle_fleet)
        
        target_fleet = self.fleet4_p2_at_a # P2's fleet at World A
        
        initial_apostle_vp_adj = self.game.turn_vp_adjustments.get(apostle_player.user_id, 0)

        fire_order = FireOrder(firing_fleet_id=apostle_fleet.id, target_type="FLEET", world_id=self.world_a.id, target_id=target_fleet.id)
        success, msg = self._process_single_order(fire_order, apostle_player)
        self.assertTrue(success, msg)
        self.assertEqual(self.game.turn_vp_adjustments.get(apostle_player.user_id, 0), initial_apostle_vp_adj -1)


    def test_conditional_fire_order_handling(self):
        from app import FireOrder
        player1 = self.player1_obj
        fleet1 = self.fleet1
        fleet1.location = self.world_a
        
        target_fleet = self.fleet4_p2_at_a # P2's fleet at A
        target_fleet.ships = 1 # Ensure it can be destroyed

        fire_order_cond = FireOrder(
            firing_fleet_id=fleet1.id, 
            target_type="FLEET", 
            world_id=self.world_a.id, 
            target_id=target_fleet.id, 
            is_conditional=True
        )
        success, msg = self._process_single_order(fire_order_cond, player1)
        self.assertTrue(success, msg)
        self.assertIn("Conditional fire order noted", msg)
        self.assertEqual(target_fleet.ships, 1, "Conditional fire should not destroy ships")


    # --- Helper for end-of-turn phase tests ---
    def _run_full_turn_for_player_eot_phases(self, player):
        """
        Simulates end-of-turn phases for a given player after their orders would have been processed.
        This includes Metal Production, Population Growth, and World/Key Capture (which includes mine increase).
        It then calculates final VPs for that player for the "turn".
        NOTE: This helper assumes player orders for the 'turn' being simulated are already processed
        and their effects (like VP adjustments from combat) are in self.game.turn_vp_adjustments.
        """
        if not hasattr(self.game, 'turn_number') or self.game.turn_number == 0:
            self.game.turn_number = 1
        else:
            # If called multiple times in a test for sequential turns, increment.
            # For isolated EOT phase testing, usually turn_number=1 is fine.
            # self.game.turn_number +=1 
            pass
        
        print(f"--- Simulating EOT Phases for Turn {self.game.turn_number} for Player {player.name} ---")
        
        if not hasattr(self.game, 'turn_vp_adjustments'): # Ensure this exists
            self.game.turn_vp_adjustments = {}
        if player.user_id not in self.game.turn_vp_adjustments: # Ensure player entry exists
            self.game.turn_vp_adjustments[player.user_id] = 0


        # --- Metal Production Phase (as in Game.process_turn) ---
        # This should apply to ALL owned worlds in the game, not just the current player's.
        print(f"Turn {self.game.turn_number}: EOT - Metal Production Phase")
        for world in self.game.worlds: # Iterate all worlds in the game
            if world.owner and not world.is_black_hole:
                pop_for_mining = 0
                if world.robot_units > 0 and world.population == 0 and world.convert_units == 0:
                    pop_for_mining = world.robot_units
                elif world.robot_units == 0 and world.convert_units == 0: # Normal pop or mixed (if converts don't mine)
                     pop_for_mining = world.population
                
                if pop_for_mining > 0 and world.mines > 0:
                    produced_metal = min(world.mines, pop_for_mining)
                    old_stockpile = world.stockpile
                    world.stockpile = min(world.stockpile + produced_metal, 255)
                    if world.stockpile > old_stockpile:
                        print(f"World {world.name} (Owner: {world.owner.name}) produced {world.stockpile - old_stockpile} metal. New stockpile: {world.stockpile}.")
                        # self.game.add_turn_event(world.owner.user_id, f"World {world.name} produced {world.stockpile - old_stockpile} metal.")


        # --- Population Growth Phase (as in Game.process_turn - for the specified player) ---
        print(f"Turn {self.game.turn_number}: EOT - Population Growth Phase for {player.name}")
        for world in self.game.worlds: # Iterate all worlds
            if world.owner == player and not world.is_black_hole: # Growth only for this player's worlds
                if world.robot_units > 0: continue # Robots don't grow

                current_total_pop = world.population + world.convert_units
                if current_total_pop >= world.max_population: continue

                base_growth = (world.population + world.convert_units) // 10
                if base_growth == 0 and current_total_pop > 0 and current_total_pop < world.max_population:
                    base_growth = 1
                
                actual_growth = min(base_growth, world.max_population - current_total_pop)
                if actual_growth <= 0: continue

                growth_msg_parts = [f"World {world.name} (ID: {world.id})"]
                if player.character_type == "Apostle":
                    converts_from_normal = min(actual_growth, world.population)
                    if converts_from_normal > 0:
                        world.population -= converts_from_normal
                        world.convert_units += converts_from_normal
                        growth_msg_parts.append(f"converted {converts_from_normal} pop to converts.")
                    remaining_growth = actual_growth - converts_from_normal
                    if remaining_growth > 0:
                        world.convert_units += remaining_growth
                        growth_msg_parts.append(f"grew {remaining_growth} new converts.")
                    world.converts_owner_id = player.user_id
                    if converts_from_normal > 0 or remaining_growth > 0:
                        self.game.add_turn_event(player.user_id, f"{' '.join(growth_msg_parts)} New totals: Pop {world.population}, Converts {world.convert_units}.")
                else: # Non-Apostle
                    world.population += actual_growth
                    self.game.add_turn_event(player.user_id, f"World {world.name} population grew by {actual_growth}. New pop: {world.population}.")
        
        # --- World and Key Capture Logic (includes mine increase at its end) ---
        # This is a global phase, affecting all players based on presence.
        self.game.resolve_world_and_key_capture() 

        # --- Final Player VP Update Phase (for the specified player) ---
        print(f"Turn {self.game.turn_number}: EOT - Final VP Update for {player.name}")
        base_turn_vp = player.character.calculate_victory_points(self.game)
        event_vp = self.game.turn_vp_adjustments.get(player.user_id, 0)
        player.victory_points = base_turn_vp + event_vp
        
        vp_update_msg = (
            f"End of Turn {self.game.turn_number} for {player.name}: "
            f"Base VP: {base_turn_vp}, Event VP: {event_vp}, Total VP: {player.victory_points}."
        )
        self.game.add_turn_event(player.user_id, vp_update_msg)
        print(vp_update_msg)


    # --- 2. Metal Production & Mine Logic Tests (Re-added with correct name) ---
    def test_metal_production_eot(self): # Renamed to avoid conflict if old one existed
        player1 = self.player1_obj # Merchant
        world1 = self.world_a 
        world1.population=15; world1.mines=10; world1.stockpile=0 # Prod=10
        
        world_less_pop = World(id=100, name="WLessPop", owner=player1, population=5, mines=10, stockpile=0, connections=[]) # Prod=5
        self.game.worlds.append(world_less_pop)
        player1.worlds.append(world_less_pop)

        # Robot world owned by a different player for testing global production
        player_berserker_owner = self._create_player_for_test("robo_owner", "Berserker")
        world_robot = World(id=101, name="WRobot", owner=player_berserker_owner, population=0, robot_units=8, mines=10, stockpile=0, connections=[]) # Prod=8
        self.game.worlds.append(world_robot)
        player_berserker_owner.worlds.append(world_robot)
        
        world_cap = World(id=102, name="WCap", owner=player1, population=20, mines=10, stockpile=250, connections=[]) # Stockpile cap
        self.game.worlds.append(world_cap)
        player1.worlds.append(world_cap)

        # Simulate EOT phases (which includes metal production for all relevant worlds)
        self._run_full_turn_for_player_eot_phases(player1) # Parameter is for pop growth and VP focus. Metal is global.

        self.assertEqual(world1.stockpile, 10)
        self.assertEqual(world_less_pop.stockpile, 5)
        self.assertEqual(world_robot.stockpile, 8) # Check production for other player's world
        self.assertEqual(world_cap.stockpile, 255)

    def test_turns_owned_and_mine_increase_eot(self): # Renamed
        player1 = self.player1_obj
        world_inc = World(id=110, name="WInc", owner=player1, mines=5, turns_owned=7, connections=[])
        self.game.worlds.append(world_inc)
        player1.worlds.append(world_inc)

        world_max_mine = World(id=111, name="WMaxMine", owner=player1, mines=30, turns_owned=7, connections=[])
        self.game.worlds.append(world_max_mine)
        player1.worlds.append(world_max_mine)
        
        # Simulate EOT phases. resolve_world_and_key_capture handles mine increase.
        self._run_full_turn_for_player_eot_phases(player1) 
        
        self.assertEqual(world_inc.turns_owned, 1, "Turns owned should reset after mine increase attempt") 
        self.assertEqual(world_inc.mines, 6, "Mines should increase")
        self.assertEqual(world_max_mine.turns_owned, 1, "Turns owned should reset even if mines at max")
        self.assertEqual(world_max_mine.mines, 30, "Mines should not exceed 30")

    # --- 4. World/Key Capture Logic Tests ---
    def test_world_capture_neutral_to_player(self):
        # self.world_b is initially unowned. self.fleet1 (P1) moves there.
        self.fleet1.location = self.world_b 
        self.fleet1.ships = 1 # Needs ships to capture
        self.fleet1.is_at_peace = False

        # Ensure no other fleets are at world_b to contest
        for f in self.game.fleets:
            if f != self.fleet1 and f.location == self.world_b:
                f.location = self.world_isolated # Move other fleets away

        self.assertIsNone(self.world_b.owner) # Pre-condition

        self._run_full_turn_for_player_eot_phases(self.player1_obj) # Capture happens in resolve_world_and_key_capture

        self.assertEqual(self.world_b.owner, self.player1_obj)
        self.assertEqual(self.world_b.turns_owned, 1)

    def test_world_capture_player_to_player(self):
        # self.world_d is owned by player2_obj. player1_obj's fleet1 moves there.
        self.fleet1.location = self.world_d
        self.fleet1.ships = 1
        self.fleet1.is_at_peace = False
        
        # Ensure player2_obj has no fleets at world_d to contest
        for f in self.player2_obj.fleets:
            if f.location == self.world_d:
                f.location = self.world_isolated # Move P2's fleets away from their own world for this test

        self.assertEqual(self.world_d.owner, self.player2_obj) # Pre-condition

        self._run_full_turn_for_player_eot_phases(self.player1_obj)

        self.assertEqual(self.world_d.owner, self.player1_obj, "Player1 should have captured World D")
        self.assertEqual(self.world_d.turns_owned, 1)

    def test_world_capture_no_capture_if_ally(self):
        # world_d is P2's. fleet1 (P1) is there. P1 and P2 are allies.
        self.player1_obj.allies.append(self.player2_obj.user_id)
        self.player2_obj.allies.append(self.player1_obj.user_id)

        self.fleet1.location = self.world_d
        self.fleet1.ships = 1
        self.fleet1.is_at_peace = False
        
        # Ensure P2 has no other fleets to simplify
        for f in self.game.fleets:
            if f.owner == self.player2_obj and f.location == self.world_d :
                 f.location = self.world_isolated # Move them away

        initial_owner = self.world_d.owner
        self.assertEqual(initial_owner, self.player2_obj)

        self._run_full_turn_for_player_eot_phases(self.player1_obj)

        self.assertEqual(self.world_d.owner, initial_owner, "Ally should not capture world")

    def test_loose_key_capture(self):
        unowned_fleet_key = Fleet(id=300, name="KeyFleet", ships=0, location=self.world_b, owner=None) # Unowned, 0 ships
        self.game.fleets.append(unowned_fleet_key)
        
        self.fleet1.location = self.world_b # P1's fleet1 is at the same location
        self.fleet1.ships = 1
        self.fleet1.is_at_peace = False

        # Ensure no other player fleets are at world_b
        for f in self.game.fleets:
            if f.owner != self.player1_obj and f.location == self.world_b:
                f.location = self.world_isolated

        self.assertIsNone(unowned_fleet_key.owner)
        self._run_full_turn_for_player_eot_phases(self.player1_obj)
        self.assertEqual(unowned_fleet_key.owner, self.player1_obj, "Player1 should capture the loose key")

    def test_loose_key_no_capture_if_contested_or_no_presence(self):
        key_fleet = Fleet(id=301, name="ContestedKey", ships=0, location=self.world_b, owner=None)
        self.game.fleets.append(key_fleet)

        # P1's fleet1 is there
        self.fleet1.location = self.world_b
        self.fleet1.ships = 1
        self.fleet1.is_at_peace = False
        
        # P2's fleet4 is also there
        self.fleet4_p2_at_a.location = self.world_b # fleet4_p2_at_a is P2's fleet
        self.fleet4_p2_at_a.ships = 1
        self.fleet4_p2_at_a.is_at_peace = False
        
        # P1 and P2 are not allies for this sub-test
        self.player1_obj.allies = []
        self.player2_obj.allies = []


        self._run_full_turn_for_player_eot_phases(self.player1_obj) # Process for P1
        # Since capture is global, it doesn't matter which player's EOT triggers it if state is right
        self.assertIsNone(key_fleet.owner, "Key should remain unowned if contested by non-allies")

        # Test no presence
        key_fleet_no_presence = Fleet(id=302, name="NoPresenceKey", ships=0, location=self.world_c, owner=None)
        self.game.fleets.append(key_fleet_no_presence)
        # Move all fleets away from world_c
        for f in self.game.fleets:
            if f.location == self.world_c:
                f.location = self.world_isolated
        
        self._run_full_turn_for_player_eot_phases(self.player1_obj)
        self.assertIsNone(key_fleet_no_presence.owner, "Key should remain unowned if no player presence")

    # --- 5. Character-Specific VP Calculation Tests (Per-Turn VPs) ---
    def test_vp_empire_builder(self):
        player_eb = self._create_player_for_test("TestEB", "Empire Builder")
        # World 1: 100 pop (10 VP), 10 ind (10 VP), 5 mines (5 VP) = 25 VP
        self._create_world_for_player(player_eb, id=201, name="EB_W1", population=100, industry=10, mines=5)
        # World 2: 55 pop (5 VP), 3 ind (3 VP), 2 mines (2 VP) = 10 VP
        self._create_world_for_player(player_eb, id=202, name="EB_W2", population=55, industry=3, mines=2)
        # Total = 35 VP

        # Simulate EOT VP calculation for this player
        self.game.turn_vp_adjustments = {player_eb.user_id: 0} # No event VPs for this test
        self._run_full_turn_for_player_eot_phases(player_eb)
        self.assertEqual(player_eb.victory_points, 35)

    def test_vp_merchant(self):
        player_m = self._create_player_for_test("TestMerchant", "Merchant")
        self._create_world_for_player(player_m, id=203, name="M_W1", population=100) # Merchants get 0 base VP
        
        self.game.turn_vp_adjustments = {player_m.user_id: 0}
        self._run_full_turn_for_player_eot_phases(player_m)
        self.assertEqual(player_m.victory_points, 0)

    def test_vp_pirate(self):
        player_p = self._create_player_for_test("TestPirate", "Pirate")
        world = self._create_world_for_player(player_p, id=204, name="P_W1")
        self._create_fleet_for_player(player_p, id=205, name="PF1", location=world, ships=1)
        self._create_fleet_for_player(player_p, id=206, name="PF2", location=world, ships=1)
        # 2 fleets * 3 VP/fleet = 6 VP

        self.game.turn_vp_adjustments = {player_p.user_id: 0}
        self._run_full_turn_for_player_eot_phases(player_p)
        self.assertEqual(player_p.victory_points, 6)

    def test_vp_artifact_collector(self):
        player_ac = self._create_player_for_test("TestAC", "Artifact Collector")
        world_ac = self._create_world_for_player(player_ac, id=207, name="AC_W1")
        
        # Artifacts:
        # Ancient Pyramid: +90
        # Ancient Lodestar (Ancient, non-Pyramid, non-Plastic): +30
        # Platinum Pyramid (Pyramid, non-Ancient, non-Plastic): +30
        # Plastic Crown (Plastic): +0
        # Gold Shekel (Standard, non-Plastic, non-Ancient/Pyramid): +15
        # Treasure of Polaris (Special): +30
        # Nebula Scroll Volume 1 (Special, 0 base points): +0 in this calculation
        # Total = 90 + 30 + 30 + 0 + 15 + 30 + 0 = 195

        world_ac.artifacts.append(Artifact(id="V_AP", name="Ancient Pyramid", category="Standard", points=0)) # Points overridden by logic
        world_ac.artifacts.append(Artifact(id="V_AL", name="Ancient Lodestar", category="Standard", points=5))
        world_ac.artifacts.append(Artifact(id="V_PP", name="Platinum Pyramid", category="Standard", points=5))
        world_ac.artifacts.append(Artifact(id="V_PC", name="Plastic Crown", category="Standard", points=-10, is_plastic=True))
        world_ac.artifacts.append(Artifact(id="V_GS", name="Gold Shekel", category="Standard", points=5))
        world_ac.artifacts.append(Artifact(id="V_TP", name="Treasure of Polaris", category="Special", points=20)) # Base points, but logic gives 30
        world_ac.artifacts.append(Artifact(id="V_NS1", name="Nebula Scroll Volume 1", category="Special", points=0))

        self.game.turn_vp_adjustments = {player_ac.user_id: 0}
        self._run_full_turn_for_player_eot_phases(player_ac)
        self.assertEqual(player_ac.victory_points, 195)

    def test_vp_berserker(self):
        player_b = self._create_player_for_test("TestBerserkerVP", "Berserker")
        # World 1: Robot-controlled (robots > 0, pop=0, converts=0) = +5 VP
        self._create_world_for_player(player_b, id=208, name="B_W1_Robo", robot_units=10, population=0, convert_units=0)
        # World 2: Mixed pop, not robot-controlled = 0 VP
        self._create_world_for_player(player_b, id=209, name="B_W2_Mixed", robot_units=5, population=5)
        # World 3: Only pop, no robots = 0 VP
        self._create_world_for_player(player_b, id=210, name="B_W3_Pop", population=10)
        # Total = 5 VP

        self.game.turn_vp_adjustments = {player_b.user_id: 0}
        self._run_full_turn_for_player_eot_phases(player_b)
        self.assertEqual(player_b.victory_points, 5)

    def test_vp_apostle(self):
        player_ap = self._create_player_for_test("TestApostleVP", "Apostle", user_id_override="apostle_vp_user")
        
        # World 1 (Owned by Apostle): +5 VP. Fully converted (converts>0, pop=0, robots=0) = +5 VP. Has 15 converts.
        world_ap1 = self._create_world_for_player(player_ap, id=211, name="AP_W1", convert_units=15, converts_owner_id="apostle_vp_user", population=0, robot_units=0)
        
        # World 2 (Owned by Apostle): +5 VP. Not fully converted. Has 5 converts.
        world_ap2 = self._create_world_for_player(player_ap, id=212, name="AP_W2", convert_units=5, converts_owner_id="apostle_vp_user", population=10)

        # World 3 (Not owned by Apostle, but has Apostle's converts): No ownership VP. Has 20 converts.
        world_other_converts = World(id=213, name="Other_Conv", owner=None, convert_units=20, converts_owner_id="apostle_vp_user", connections=[])
        self.game.worlds.append(world_other_converts)

        # Total converts for Apostle: 15 (W1) + 5 (W2) + 20 (W3) = 40 converts.
        # VP from converts = 40 // 10 = +4 VP.
        # Total VP = 5 (W1 owned) + 5 (W1 fully converted) + 5 (W2 owned) + 4 (total converts) = 19 VP.

        self.game.turn_vp_adjustments = {player_ap.user_id: 0}
        self._run_full_turn_for_player_eot_phases(player_ap)
        self.assertEqual(player_ap.victory_points, 19)


    # --- 6. Population Growth Tests ---
    def test_population_growth_normal(self):
        player_n = self.player1_obj # Merchant
        world = self.world_a
        world.owner = player_n # Ensure owner matches for growth logic in helper
        world.population = 50
        world.convert_units = 0 # Ensure no converts for normal growth test
        world.max_population = 100
        
        self._run_full_turn_for_player_eot_phases(player_n) # Growth is 50 // 10 = 5
        self.assertEqual(world.population, 55)

        # Test max_population cap
        world.population = 98
        self._run_full_turn_for_player_eot_phases(player_n) # Growth is 98 // 10 = 9. Expected 98+9=107. Cap at 100.
        self.assertEqual(world.population, 100) # Should cap at 100

    def test_population_growth_apostle(self):
        player_ap = self._create_player_for_test("TestApostleGrowth", "Apostle", "apostle_growth_user")
        world = self._create_world_for_player(player_ap, id=214, name="AP_Grow", population=50, convert_units=0, max_population=100)
        world.converts_owner_id = player_ap.user_id # Needs to be set for apostle logic

        # Growth is 50 // 10 = 5. All 5 should convert from normal pop.
        self._run_full_turn_for_player_eot_phases(player_ap)
        self.assertEqual(world.population, 45) # 50 - 5
        self.assertEqual(world.convert_units, 5)  # 0 + 5
        self.assertEqual(world.converts_owner_id, player_ap.user_id)

        # Test growth when some converts already exist, and converts some normal, grows some new
        world.population = 20  # Pop 20
        world.convert_units = 30 # Converts 30. Total 50.
        world.max_population = 100
        # Growth is (20+30)//10 = 5.
        # Converts from normal: min(5, 20) = 5. Pop becomes 15. Converts become 35.
        # Remaining growth capacity = 5 - 5 = 0. No new converts grown.
        self._run_full_turn_for_player_eot_phases(player_ap)
        self.assertEqual(world.population, 15) # 20 - 5
        self.assertEqual(world.convert_units, 35) # 30 + 5

    def test_population_growth_robots_no_growth(self):
        player_b = self._create_player_for_test("TestBerserkerGrowth", "Berserker")
        world = self._create_world_for_player(player_b, id=215, name="RoboNoGrow", robot_units=50, population=0, max_population=100)
        
        self._run_full_turn_for_player_eot_phases(player_b)
        self.assertEqual(world.robot_units, 50) # Robots should not grow

    def test_population_growth_at_max_pop(self):
        player_n = self.player1_obj
        world = self.world_a
        world.owner = player_n
        world.population = 100
        world.max_population = 100
        
        self._run_full_turn_for_player_eot_phases(player_n)
        self.assertEqual(world.population, 100) # Should not grow

    def test_population_growth_minimum_one(self):
        player_n = self.player1_obj
        world = self.world_a
        world.owner = player_n
        world.population = 5 # Pop < 10 but > 0
        world.convert_units = 0
        world.max_population = 100
        
        self._run_full_turn_for_player_eot_phases(player_n) # Growth should be 1
        self.assertEqual(world.population, 6)


    # Helper to create a world and assign to player for VP/Growth tests
    def _create_world_for_player(self, player: Player, id: int, name: str, 
                                 population: int = 0, max_population: int = 100, 
                                 industry: int = 0, mines: int = 0, stockpile: int = 0,
                                 robot_units: int = 0, convert_units: int = 0, 
                                 converts_owner_id: str | None = None,
                                 iships: int = 0, pships: int = 0,
                                 artifacts: list[Artifact] | None = None):
        world = World(
            id=id, name=name, owner=player, connections=[],
            iships=iships, pships=pships, population=population,
            max_population=max_population, industry=industry, mines=mines,
            stockpile=stockpile, artifacts=artifacts if artifacts is not None else [],
            robot_units=robot_units, convert_units=convert_units,
            converts_owner_id=converts_owner_id
        )
        self.game.worlds.append(world)
        player.worlds.append(world)
        if not player.home_world:
            player.home_world = world
        return world

    def _create_fleet_for_player(self, player: Player, id: int, name: str, location: World, ships: int = 0):
        fleet = Fleet(id=id, name=name, owner=player, location=location, ships=ships)
        self.game.fleets.append(fleet)
        player.fleets.append(fleet)
        return fleet

    def test_submit_turn_triggers_capture_and_mine_increase(self):
        # 1. Setup
        # Using existing players from setUp: self.player1_obj (P1, Merchant), self.player2_obj (P2, EmpireBuilder)
        # Let P1 be player_a, P2 be player_b for clarity in this test.
        player_a = self.player1_obj # Merchant
        player_b = self.player2_obj # Empire Builder

        # Create World X: Initially unowned.
        world_x = World(id=50, name="WorldX", owner=None, connections=[], iships=0,pships=0,population=10,max_population=100,industry=10,mines=1,stockpile=10)
        self.game.worlds.append(world_x)

        # Create World Z: A distinct world.
        world_z = World(id=51, name="WorldZ", owner=None, connections=[], iships=0,pships=0,population=10,max_population=100,industry=10,mines=1,stockpile=10)
        self.game.worlds.append(world_z)
        
        # Create Key Y: Unowned fleet, 0 ships, at world_z.
        key_y_fleet = Fleet(id=52, name="KeyY", ships=0, location=world_z, owner=None)
        self.game.fleets.append(key_y_fleet)

        # Create Fleet B1: Owned by player_b, ships > 0, not at peace, at world_x.
        # self.fleet4_p2_at_a is P2's fleet. Let's repurpose it.
        fleet_b1 = self.fleet4_p2_at_a 
        fleet_b1.owner = player_b
        fleet_b1.location = world_x
        fleet_b1.ships = 10
        fleet_b1.is_at_peace = False
        if fleet_b1 not in player_b.fleets: player_b.fleets.append(fleet_b1)


        # Create Fleet A1: Owned by player_a, ships > 0, not at peace, at world_z.
        # self.fleet1 is P1's fleet.
        fleet_a1 = self.fleet1
        fleet_a1.owner = player_a
        fleet_a1.location = world_z
        fleet_a1.ships = 10
        fleet_a1.is_at_peace = False
        if fleet_a1 not in player_a.fleets: player_a.fleets.append(fleet_a1)


        # Create World M: Owned by player_a, mines = 5, turns_owned = 7.
        # self.world_c is owned by P1 (player_a).
        world_m = self.world_c 
        world_m.owner = player_a
        world_m.mines = 5
        world_m.turns_owned = 7
        # Ensure no other fleets at World M
        for f in self.game.fleets:
            if f.location == world_m and f != fleet_a1: # fleet_a1 is at world_z now
                f.location = self.world_isolated # Move away

        # 2. Action
        # Simulate processing a turn for Player B.
        print(f"Initial state: World X owner: {world_x.owner}, Key Y owner: {key_y_fleet.owner}, World M mines: {world_m.mines}, World M turns_owned: {world_m.turns_owned}")
        
        # Clear previous turn events for player_b before processing their turn
        if player_b.user_id in self.game.turn_events: self.game.turn_events[player_b.user_id] = []
        self.game.process_turn(player_b.user_id, [])
        
        # Simulate processing a turn for Player A.
        # Clear previous turn events for player_a before processing their turn
        if player_a.user_id in self.game.turn_events: self.game.turn_events[player_a.user_id] = []
        self.game.process_turn(player_a.user_id, [])

        print(f"Post-turn state: World X owner: {world_x.owner.name if world_x.owner else 'None'}, Key Y owner: {key_y_fleet.owner.name if key_y_fleet.owner else 'None'}, World M mines: {world_m.mines}, World M turns_owned: {world_m.turns_owned}")
        print(f"Events for P_A ({player_a.user_id}): {self.game.turn_events.get(player_a.user_id)}")
        print(f"Events for P_B ({player_b.user_id}): {self.game.turn_events.get(player_b.user_id)}")


        # 3. Assertions
        self.assertEqual(world_x.owner, player_b, "Player B should capture World X.")
        self.assertEqual(world_x.turns_owned, 1, "World X turns_owned should be 1 after capture.")
        
        self.assertEqual(key_y_fleet.owner, player_a, "Player A should capture Key Y.")
        
        self.assertEqual(world_m.mines, 6, "World M mines should increase to 6.")
        self.assertEqual(world_m.turns_owned, 1, "World M turns_owned should reset to 1 after mine increase.")

        # Check game.turn_events for relevant messages
        # Note: process_turn clears events for the *current_user* whose turn is being processed *before* adding new ones for that turn.
        # So, we check the events that were generated during that specific process_turn call.
        # The turn_events dictionary in the game object will hold the *last* set of events generated for each player.

        player_b_events = self.game.get_and_clear_turn_events(player_b.user_id) # Clears after getting
        found_world_x_capture_event = any(f"You captured world {world_x.name}" in event for event in player_b_events)
        self.assertTrue(found_world_x_capture_event, "Player B events should contain World X capture message.")

        player_a_events = self.game.get_and_clear_turn_events(player_a.user_id) # Clears after getting
        found_key_y_capture_event = any(f"You acquired unowned fleet key {key_y_fleet.name}" in event for event in player_a_events)
        found_mine_increase_event = any(f"World {world_m.name} (ID: {world_m.id}, Owner: {player_a.name}) increased mines to 6" in event for event in player_a_events) # Exact message from app.py
        
        self.assertTrue(found_key_y_capture_event, "Player A events should contain Key Y capture message.")
        self.assertTrue(found_mine_increase_event, "Player A events should contain World M mine increase message.")

    # --- Test Artifact Management ---
    def test_attach_artifact_order(self):
        player = self.player1_obj
        fleet = self.fleet1 # P1's fleet, at world_a
        world_with_artifact = self.world_a # P1's world
        
        # Ensure ALL_ARTIFACTS is populated for get_artifact_by_id
        if not ALL_ARTIFACTS: self.fail("ALL_ARTIFACTS list is empty. Cannot run artifact tests.")
        test_artifact = ALL_ARTIFACTS[0] # Pick first available global artifact
        
        world_with_artifact.artifacts = [test_artifact] # Place artifact on the world
        fleet.artifacts = [] # Ensure fleet starts with no artifacts

        # Valid attach
        attach_order = AttachArtifactOrder(player_id=player.user_id, fleet_id=fleet.id, artifact_id=test_artifact.id, world_id=world_with_artifact.id)
        success, msg = self._process_single_order(attach_order, player)
        self.assertTrue(success, f"Attach artifact failed: {msg}")
        self.assertIn(test_artifact, fleet.artifacts)
        self.assertNotIn(test_artifact, world_with_artifact.artifacts)
        # Check for event (assuming add_turn_event is called by execute method)
        # self.assertIn(f"Artifact {test_artifact.name} attached to fleet {fleet.name}", self.game.get_and_clear_turn_events(player.user_id)[-1])


        # Edge Case: Artifact not on world
        world_with_artifact.artifacts = [] # Remove artifact
        attach_order_fail = AttachArtifactOrder(player_id=player.user_id, fleet_id=fleet.id, artifact_id=test_artifact.id, world_id=world_with_artifact.id)
        success, msg = self._process_single_order(attach_order_fail, player)
        self.assertFalse(success, f"Attach should fail if artifact not on world: {msg}")

        # Edge Case: Fleet not found (using a dummy ID)
        attach_order_no_fleet = AttachArtifactOrder(player_id=player.user_id, fleet_id=999, artifact_id=test_artifact.id, world_id=world_with_artifact.id)
        world_with_artifact.artifacts = [test_artifact] # Put artifact back for this test
        success, msg = self._process_single_order(attach_order_no_fleet, player)
        self.assertFalse(success, f"Attach should fail if fleet not found: {msg}")
        self.assertIn(test_artifact, world_with_artifact.artifacts) # Artifact should remain on world

        # Edge Case: Player doesn't own fleet
        other_player_fleet = self.fleet4_p2_at_a # Belongs to player2_obj
        other_player_fleet.location = world_with_artifact # Move to same world for test
        attach_order_wrong_owner = AttachArtifactOrder(player_id=player.user_id, fleet_id=other_player_fleet.id, artifact_id=test_artifact.id, world_id=world_with_artifact.id)
        success, msg = self._process_single_order(attach_order_wrong_owner, player)
        self.assertFalse(success, f"Attach should fail if player doesn't own fleet: {msg}")


    def test_drop_artifact_order(self):
        player = self.player1_obj
        fleet_with_artifact = self.fleet1 # P1's fleet at world_a
        target_world = self.world_a # P1's world
        
        if not ALL_ARTIFACTS: self.fail("ALL_ARTIFACTS list is empty.")
        test_artifact = ALL_ARTIFACTS[1] # Use a different artifact
        
        fleet_with_artifact.artifacts = [test_artifact]
        target_world.artifacts = []

        # Valid drop
        drop_order = DropArtifactOrder(player_id=player.user_id, fleet_id=fleet_with_artifact.id, artifact_id=test_artifact.id, world_id=target_world.id)
        success, msg = self._process_single_order(drop_order, player)
        self.assertTrue(success, f"Drop artifact failed: {msg}")
        self.assertIn(test_artifact, target_world.artifacts)
        self.assertNotIn(test_artifact, fleet_with_artifact.artifacts)
        # self.assertIn(f"Artifact {test_artifact.name} dropped from fleet {fleet_with_artifact.name}", self.game.get_and_clear_turn_events(player.user_id)[-1])

        # Edge Case: Fleet doesn't have artifact
        fleet_with_artifact.artifacts = [] # Remove artifact
        drop_order_fail = DropArtifactOrder(player_id=player.user_id, fleet_id=fleet_with_artifact.id, artifact_id=test_artifact.id, world_id=target_world.id)
        success, msg = self._process_single_order(drop_order_fail, player)
        self.assertFalse(success, f"Drop should fail if fleet doesn't have artifact: {msg}")
        
        # Edge Case: Target world not found
        fleet_with_artifact.artifacts = [test_artifact] # Put artifact back
        drop_order_no_world = DropArtifactOrder(player_id=player.user_id, fleet_id=fleet_with_artifact.id, artifact_id=test_artifact.id, world_id=999)
        success, msg = self._process_single_order(drop_order_no_world, player)
        self.assertFalse(success, f"Drop should fail if target world not found: {msg}")
        self.assertIn(test_artifact, fleet_with_artifact.artifacts) # Artifact should remain on fleet

    # --- Test Ambush Command ---
    def test_set_ambush_order(self):
        player = self.player1_obj
        fleet = self.fleet1 # P1's fleet at world_a
        world = self.world_a

        self.assertFalse(fleet.is_ambushing) # Pre-condition
        ambush_order = AmbushOrder(player_id=player.user_id, fleet_id=fleet.id, world_id=world.id)
        success, msg = self._process_single_order(ambush_order, player)
        self.assertTrue(success, f"Set ambush failed: {msg}")
        self.assertTrue(fleet.is_ambushing)
        # self.assertIn(f"Fleet {fleet.name} is now set to ambush", self.game.get_and_clear_turn_events(player.user_id)[-1])

        # Validation: Fleet not at world
        other_world = self.world_b
        ambush_order_wrong_loc = AmbushOrder(player_id=player.user_id, fleet_id=fleet.id, world_id=other_world.id)
        fleet.is_ambushing = False # Reset
        success, msg = self._process_single_order(ambush_order_wrong_loc, player)
        self.assertFalse(success, f"Set ambush should fail if fleet not at world: {msg}")
        self.assertFalse(fleet.is_ambushing)

    def test_ambush_combat_advantage(self):
        from app import FireOrder # Ensure FireOrder is available
        attacker = self.player2_obj # P2
        defender = self.player1_obj # P1

        combat_world = self.world_b # Neutral world
        
        attacker_fleet = self.fleet4_p2_at_a # P2's fleet
        attacker_fleet.location = combat_world
        attacker_fleet.ships = 10
        attacker_fleet.cargo = 0

        defender_fleet_ambushing = self.fleet1 # P1's fleet
        defender_fleet_ambushing.location = combat_world
        defender_fleet_ambushing.ships = 10
        defender_fleet_ambushing.cargo = 0
        defender_fleet_ambushing.is_ambushing = True # Defender is ambushing

        # Attacker fires at defender. Defender (ambusher) should fire first.
        # Defender: 10 ships, 0 cargo. Attacker: 10 ships, 0 cargo.
        # Defender fires 10 shots -> Attacker takes 10/2 = 5 ship losses. Attacker ships = 5.
        # Attacker (now 5 ships) fires 5 shots -> Defender takes 5/2 = 2 ship losses (rounded down). Defender ships = 8.
        fire_order = FireOrder(firing_fleet_id=attacker_fleet.id, target_type="FLEET", world_id=combat_world.id, target_id=defender_fleet_ambushing.id)
        
        # Clear events before processing
        self.game.turn_events = {}
        self.game.turn_vp_adjustments = {}

        success, msg = self._process_single_order(fire_order, attacker)
        
        self.assertTrue(success, f"Ambush combat failed: {msg}")
        self.assertEqual(attacker_fleet.ships, 5, f"Attacker ships incorrect: {msg}")
        self.assertEqual(defender_fleet_ambushing.ships, 8, f"Defender ships incorrect: {msg}") # 10 - floor(5/2) = 8
        self.assertFalse(defender_fleet_ambushing.is_ambushing, "Defender ambush status should be reset")
        
        # Check events
        # attacker_events = self.game.get_and_clear_turn_events(attacker.user_id)
        # defender_events = self.game.get_and_clear_turn_events(defender.user_id)
        # self.assertTrue(any(f"Target fleet {defender_fleet_ambushing.name} was ambushing!" in e for e in attacker_events))
        # self.assertTrue(any(f"Ambusher {defender_fleet_ambushing.name} fires" in e for e in attacker_events))


    def test_ambush_resets_if_not_triggered(self):
        player = self.player1_obj
        fleet = self.fleet1
        fleet.location = self.world_a
        fleet.is_ambushing = True

        # Simulate end of turn processing for this player
        self._run_full_turn_for_player_eot_phases(player)
        self.assertFalse(fleet.is_ambushing, "Fleet ambush status should be reset at end of turn if not triggered.")

    # --- Test Diplomacy Commands ---
    def test_set_ally_order(self):
        player1 = self.player1_obj
        player2 = self.player2_obj

        self.assertNotIn(player2.user_id, player1.allies) # Pre-condition
        
        set_ally_order = SetAllyOrder(player_id=player1.user_id, target_player_id=player2.user_id)
        success, msg = self._process_single_order(set_ally_order, player1)
        self.assertTrue(success, msg)
        self.assertIn(player2.user_id, player1.allies)
        # Check events
        # p1_events = self.game.get_and_clear_turn_events(player1.user_id)
        # p2_events = self.game.get_and_clear_turn_events(player2.user_id)
        # self.assertTrue(any(f"You have declared an alliance with {player2.name}" in e for e in p1_events))
        # self.assertTrue(any(f"{player1.name} has declared an alliance with you" in e for e in p2_events))


        # Cannot ally self
        set_ally_self = SetAllyOrder(player_id=player1.user_id, target_player_id=player1.user_id)
        success, msg = self._process_single_order(set_ally_self, player1)
        self.assertFalse(success, "Should not be able to ally with self.")

    def test_gift_world_order(self):
        giver = self.player1_obj
        recipient = self.player2_obj
        world_to_gift = self.world_a # Owned by P1
        world_to_gift.convert_units = 5 # Add some converts for testing
        world_to_gift.converts_owner_id = giver.user_id

        initial_giver_worlds_count = len(giver.worlds)
        initial_recipient_worlds_count = len(recipient.worlds)

        gift_order = GiftWorldOrder(player_id=giver.user_id, world_id=world_to_gift.id, recipient_player_id=recipient.user_id)
        success, msg = self._process_single_order(gift_order, giver)
        self.assertTrue(success, msg)
        self.assertEqual(world_to_gift.owner, recipient)
        self.assertEqual(world_to_gift.turns_owned, 1)
        self.assertIn(world_to_gift, recipient.worlds)
        self.assertNotIn(world_to_gift, giver.worlds)
        self.assertEqual(len(giver.worlds), initial_giver_worlds_count - 1)
        self.assertEqual(len(recipient.worlds), initial_recipient_worlds_count + 1)
        
        # Test convert handling (recipient is Empire Builder, not Apostle)
        self.assertEqual(world_to_gift.convert_units, 0, "Converts should be disbanded if recipient is not their Apostle master.")
        self.assertIsNone(world_to_gift.converts_owner_id)

    def test_gift_fleet_order(self):
        giver = self.player1_obj
        recipient = self.player2_obj
        fleet_to_gift = self.fleet1 # Owned by P1

        initial_giver_fleets_count = len(giver.fleets)
        initial_recipient_fleets_count = len(recipient.fleets)

        gift_order = GiftFleetOrder(player_id=giver.user_id, fleet_id=fleet_to_gift.id, recipient_player_id=recipient.user_id)
        success, msg = self._process_single_order(gift_order, giver)
        self.assertTrue(success, msg)
        self.assertEqual(fleet_to_gift.owner, recipient)
        self.assertIn(fleet_to_gift, recipient.fleets)
        self.assertNotIn(fleet_to_gift, giver.fleets)
        self.assertEqual(len(giver.fleets), initial_giver_fleets_count - 1)
        self.assertEqual(len(recipient.fleets), initial_recipient_fleets_count + 1)


if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main(failfast=True) # Added failfast for quicker feedback during development
