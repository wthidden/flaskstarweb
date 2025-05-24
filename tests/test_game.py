import unittest
import sys
import os

# Adjust the path to import from the parent directory (project root)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import Game, World, Fleet, Player
from app import MoveOrder, TransferOrder, LoadCargoOrder, UnloadCargoOrder, order_from_dict

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
        
        raw_orders = [valid_move_dict, invalid_load_dict]
        results = self.game.process_turn(raw_orders)
        
        self.assertEqual(len(results), 2)
        self.assertIn("(Success: True)", results[1]) # Move is P60, Load is P40. Load happens first.
        self.assertIn("(Success: False)", results[0]) # Load should fail
        self.assertIn("LOAD_CARGO", results[0])
        self.assertIn("MOVE", results[1])


if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main(failfast=True) # Added failfast for quicker feedback during development
