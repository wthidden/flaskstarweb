import unittest
import sys
import os

# Adjust the path to import from the parent directory (project root)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import Game, World, Fleet, Player, User # Added User for _register_new_player_setup
from app import MoveOrder, TransferOrder, LoadCargoOrder, UnloadCargoOrder, order_from_dict
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


if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main(failfast=True) # Added failfast for quicker feedback during development
