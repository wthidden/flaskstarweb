import unittest
import sys
import os

# Adjust the path to import from the parent directory (project root)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import Game, World, Fleet

class TestGameCommands(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, create a new game instance for each test."""
        self.game = Game(worlds=[], fleets=[], players=[])

        # Create Worlds
        self.world_a = World(id=1, name="World A", owner=None, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        self.world_b = World(id=2, name="World B", owner=None, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        self.world_c = World(id=3, name="World C", owner=None, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        self.world_d = World(id=4, name="World D", owner=None, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        # A world not connected to anything initially, for specific tests
        self.world_isolated = World(id=5, name="World Isolated", owner=None, connections=[], iships=0, pships=0, population=10, max_population=100, industry=10, mines=1, stockpile=10, artifacts=[])
        
        self.game.worlds.extend([self.world_a, self.world_b, self.world_c, self.world_d, self.world_isolated])

        # Connect worlds: A <-> B, B <-> C, C <-> D
        self.world_a.connections.append(self.world_b)
        self.world_b.connections.append(self.world_a)

        self.world_b.connections.append(self.world_c)
        self.world_c.connections.append(self.world_b)

        self.world_c.connections.append(self.world_d)
        self.world_d.connections.append(self.world_c)

        # Create Fleets
        self.fleet1 = Fleet(id=1, name="Fleet 1", ships=10, location=self.world_a, owner="Player1", cargo=[], artifacts=[])
        self.fleet2_no_ships = Fleet(id=2, name="Fleet 2", ships=0, location=self.world_a, owner="Player1", cargo=[], artifacts=[])
        # Fleet in a different location for some tests
        self.fleet3_at_b = Fleet(id=3, name="Fleet 3", ships=5, location=self.world_b, owner="Player1", cargo=[], artifacts=[])

        self.game.fleets.extend([self.fleet1, self.fleet2_no_ships, self.fleet3_at_b])

    def test_move_fleet_single_step_valid(self):
        """Test valid single-step fleet movement."""
        initial_location = self.fleet1.location
        self.assertTrue(self.world_b in initial_location.connections, "Pre-condition failed: World B not connected to World A")
        
        result = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=[self.world_b])
        
        self.assertTrue(result, "MoveCommand should return True for a valid single step move.")
        self.assertEqual(self.fleet1.location, self.world_b, "Fleet location should be updated to World B.")

    def test_move_fleet_multi_step_valid(self):
        """Test valid multi-step fleet movement."""
        initial_location = self.fleet1.location # Starts at World A
        self.assertTrue(self.world_b in initial_location.connections, "Pre-condition failed: World B not connected to World A")
        self.assertTrue(self.world_c in self.world_b.connections, "Pre-condition failed: World C not connected to World B")

        result = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=[self.world_b, self.world_c])
        
        self.assertTrue(result, "MoveCommand should return True for a valid multi-step move.")
        self.assertEqual(self.fleet1.location, self.world_c, "Fleet location should be updated to World C.")

    def test_move_fleet_invalid_fleet_not_found(self):
        """Test movement with a non-existent fleet ID."""
        non_existent_fleet_id = 999
        result = self.game.MoveCommand(fleet_id=non_existent_fleet_id, target_world_ids=[self.world_b])
        
        self.assertFalse(result, "MoveCommand should return False if fleet ID is not found.")

    def test_move_fleet_invalid_no_ships(self):
        """Test movement with a fleet that has no ships."""
        initial_location = self.fleet2_no_ships.location
        result = self.game.MoveCommand(fleet_id=self.fleet2_no_ships.id, target_world_ids=[self.world_b])
        
        self.assertFalse(result, "MoveCommand should return False if the fleet has no ships.")
        self.assertEqual(self.fleet2_no_ships.location, initial_location, "Fleet location should not change if it has no ships.")

    def test_move_fleet_invalid_path_too_long(self):
        """Test movement with a path that is too long (more than 2 steps)."""
        initial_location = self.fleet1.location # World A
        # Path A -> B -> C -> D (3 target worlds)
        path_too_long = [self.world_b, self.world_c, self.world_d]
        
        result = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=path_too_long)
        
        self.assertFalse(result, "MoveCommand should return False for a path longer than 2 steps.")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change if path is too long.")

    def test_move_fleet_invalid_disconnected_first_step(self):
        """Test movement to a world not connected to the fleet's current location."""
        initial_location = self.fleet1.location # World A
        # World C is not directly connected to World A
        self.assertFalse(self.world_c in initial_location.connections, "Pre-condition failed: World C should not be connected to World A for this test.")
        
        result = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=[self.world_c])
        
        self.assertFalse(result, "MoveCommand should return False if the first target world is not connected.")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change if first step is disconnected.")

    def test_move_fleet_invalid_disconnected_second_step(self):
        """Test movement where the second step in a path is to a disconnected world."""
        initial_location = self.fleet1.location # World A
        # World A is connected to B, but World D is not connected to B
        self.assertTrue(self.world_b in initial_location.connections, "Pre-condition: World B must be connected to A.")
        self.assertFalse(self.world_d in self.world_b.connections, "Pre-condition: World D must NOT be connected to B.")

        path_with_disconnected_second_step = [self.world_b, self.world_d]
        
        result = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=path_with_disconnected_second_step)
        
        self.assertFalse(result, "MoveCommand should return False if the second target world is not connected to the first.")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change if second step is disconnected.")

    def test_move_fleet_invalid_target_world_object_is_none(self):
        """Test movement if a world object in the path is None (simulating a failed lookup before call)."""
        initial_location = self.fleet1.location
        # This tests if MoveCommand handles a None in the path,
        # which could happen if the calling code (like a route) fails to find a world by ID
        # but still passes a list perhaps containing None.
        
        # Scenario 1: First target is None
        result1 = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=[None])
        self.assertFalse(result1, "MoveCommand should return False if a target world in path is None (first step).")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change.")

        # Scenario 2: Second target is None
        result2 = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=[self.world_b, None])
        self.assertFalse(result2, "MoveCommand should return False if a target world in path is None (second step).")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change.")

    def test_move_fleet_to_current_location_not_allowed_by_path_validation(self):
        """Test moving to current location. Path validation should catch this as no valid 'next' world."""
        # MoveCommand's path validation logic: path = [current_location] + target_world_ids
        # If target_world_ids = [current_location], then path = [current_location, current_location]
        # The loop for i in range(len(path) - 1) will check connections from path[0] to path[1]
        # i.e. world_a to world_a. This should fail as world_a is not in world_a.connections.
        initial_location = self.fleet1.location # World A
        
        result = self.game.MoveCommand(fleet_id=self.fleet1.id, target_world_ids=[self.world_a])
        
        self.assertFalse(result, "MoveCommand should return False if attempting to move to current location (fails connection check).")
        self.assertEqual(self.fleet1.location, initial_location, "Fleet location should not change.")


if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main(failfast=True) # Added failfast for quicker feedback during development
