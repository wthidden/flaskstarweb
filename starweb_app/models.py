import random
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Forward declarations for type hints if necessary (though often not needed with string literals)
# class Player: pass
# class World: pass
# class Fleet: pass
# class Artifact: pass
# class Game: pass # If Game methods are type-hinted within these models, which they aren't directly.


class World:
    """This is a docstring for the World class"""

    def __init__(self, id, name, owner: 'Player | None', connections: list, iships: int, pships: int, 
                 population: int, max_population: int, industry: int, mines: int,
                 stockpile: int,
                 artifacts: list['Artifact'] | None = None, # Type hint for artifacts
                 turns_owned: int = 0, is_black_hole: bool = False,
                 robot_units: int = 0, convert_units: int = 0, converts_owner_id: str | None = None,
                 cg_unloads_count: int = 0,
                 times_plundered_this_game: int = 0, recovering_from_plunder_turns: int = 0,
                 is_destroyed_by_pbb: bool = False): 
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
        self.cg_unloads_count = cg_unloads_count
        self.times_plundered_this_game = times_plundered_this_game
        self.recovering_from_plunder_turns = recovering_from_plunder_turns
        self.is_destroyed_by_pbb = is_destroyed_by_pbb


class Fleet:
    """This is a docstring for the Fleet class"""

    def __init__(self, id, name, ships: int, location: World | None, owner: 'Player | None', 
                 cargo: int, artifacts: list['Artifact'] | None = None, # Type hint for artifacts
                 is_at_peace: bool = False, has_pbb: bool = False): 
        self.id = id
        self.name = name
        self.ships = ships
        self.location: World | None = location
        self.owner: Player | None = owner
        self.cargo = cargo
        self.artifacts: list[Artifact] = artifacts if artifacts is not None else []
        self.is_at_peace = is_at_peace
        self.is_ambushing = False # Added for Ambush orders
        self.has_pbb = has_pbb

    def get_max_cargo_capacity(self) -> int:
        """Calculates max cargo based on ship count and owner type."""
        if self.owner and self.owner.character_type == "Merchant":
            return self.ships * 2
        return self.ships * 1 # Default for non-Merchants or unowned fleets


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

        # Artifact VPs for Empire Builder
        # Preferred: "Platinum", "Crown". Greatest Treasure: "Platinum Crown"
        artifact_vp = 0
        owned_artifacts: list[Artifact] = []
        for world in self.player.worlds:
            if world.owner == self.player:
                owned_artifacts.extend(world.artifacts)
        for fleet in self.player.fleets:
            if fleet.owner == self.player:
                owned_artifacts.extend(fleet.artifacts)

        for artifact in owned_artifacts:
            if artifact.name == "Platinum Crown":
                artifact_vp += 15
                continue
            if artifact.is_plastic:
                artifact_vp -= 10
                continue
            
            # Preferred categories
            if artifact.first_word == "Platinum" or artifact.second_word == "Crown":
                artifact_vp += 5
                continue # Already processed as preferred

            # Special Artifacts (non-AC specific points)
            if artifact.name == "Treasure of Polaris":
                artifact_vp += 20
            elif artifact.name == "Slippers of Venus":
                artifact_vp += 10
            elif artifact.name == "Radioactive Isotope":
                artifact_vp -= 30
            elif artifact.name == "Lesser of Two Evils":
                artifact_vp -= 15
            # "The Black Box" and Nebula Scrolls give 0 VP in this general calculation

        vp += artifact_vp
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
        vp = 0 # Base VPs for Merchant are 0, will be based on actions.

        # Artifact VPs for Merchant
        # Preferred: "Gold", "Shekel". Greatest Treasure: "Gold Shekel"
        artifact_vp = 0
        owned_artifacts: list[Artifact] = []
        for world in self.player.worlds:
            if world.owner == self.player:
                owned_artifacts.extend(world.artifacts)
        for fleet in self.player.fleets:
            if fleet.owner == self.player:
                owned_artifacts.extend(fleet.artifacts)

        for artifact in owned_artifacts:
            if artifact.name == "Gold Shekel": # Greatest Treasure
                artifact_vp += 15
                continue
            if artifact.is_plastic:
                artifact_vp -= 10
                continue
            
            if artifact.first_word == "Gold" or artifact.second_word == "Shekel": # Preferred
                artifact_vp += 5
                continue

            # Special Artifacts
            if artifact.name == "Treasure of Polaris":
                artifact_vp += 20
            elif artifact.name == "Slippers of Venus":
                artifact_vp += 10
            elif artifact.name == "Radioactive Isotope":
                artifact_vp -= 30
            elif artifact.name == "Lesser of Two Evils":
                artifact_vp -= 15
        
        vp += artifact_vp
        return vp


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

        # Artifact VPs for Pirate
        # Preferred: "Silver", "Lodestar". Greatest Treasure: "Silver Lodestar"
        artifact_vp = 0
        owned_artifacts: list[Artifact] = []
        for world in self.player.worlds:
            if world.owner == self.player:
                owned_artifacts.extend(world.artifacts)
        for fleet in self.player.fleets:
            if fleet.owner == self.player:
                owned_artifacts.extend(fleet.artifacts)

        for artifact in owned_artifacts:
            if artifact.name == "Silver Lodestar": # Greatest Treasure
                artifact_vp += 15
                continue
            if artifact.is_plastic:
                artifact_vp -= 10
                continue
            
            if artifact.first_word == "Silver" or artifact.second_word == "Lodestar": # Preferred
                artifact_vp += 5
                continue

            # Special Artifacts
            if artifact.name == "Treasure of Polaris":
                artifact_vp += 20
            elif artifact.name == "Slippers of Venus":
                artifact_vp += 10
            elif artifact.name == "Radioactive Isotope":
                artifact_vp -= 30
            elif artifact.name == "Lesser of Two Evils":
                artifact_vp -= 15
        
        vp += artifact_vp
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
        
        # Artifact VPs for Berserker
        # Preferred: "Titanium", "Sword". Greatest Treasure: "Titanium Sword"
        artifact_vp = 0
        owned_artifacts: list[Artifact] = []
        for world in self.player.worlds:
            if world.owner == self.player:
                owned_artifacts.extend(world.artifacts)
        for fleet in self.player.fleets:
            if fleet.owner == self.player:
                owned_artifacts.extend(fleet.artifacts)

        for artifact in owned_artifacts:
            if artifact.name == "Titanium Sword": # Greatest Treasure
                artifact_vp += 15
                continue
            if artifact.is_plastic:
                artifact_vp -= 10
                continue
            
            if artifact.first_word == "Titanium" or artifact.second_word == "Sword": # Preferred
                artifact_vp += 5
                continue

            # Special Artifacts
            if artifact.name == "Treasure of Polaris":
                artifact_vp += 20
            elif artifact.name == "Slippers of Venus":
                artifact_vp += 10
            elif artifact.name == "Radioactive Isotope":
                artifact_vp -= 30
            elif artifact.name == "Lesser of Two Evils":
                artifact_vp -= 15
        
        vp += artifact_vp
        return vp


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
        # This requires access to the 'game' object, which is passed as an argument.
        for world_in_game in game.worlds: # Iterate all worlds in the game
            if world_in_game.converts_owner_id == self.player.user_id:
                total_apostle_converts += world_in_game.convert_units
        
        vp += total_apostle_converts // 10

        # Artifact VPs for Apostle
        # Preferred: "Blessed", "Sepulchre". Greatest Treasure: "Blessed Sepulchre"
        artifact_vp = 0
        owned_artifacts: list[Artifact] = []
        for world in self.player.worlds:
            if world.owner == self.player:
                owned_artifacts.extend(world.artifacts)
        for fleet in self.player.fleets:
            if fleet.owner == self.player:
                owned_artifacts.extend(fleet.artifacts)

        for artifact in owned_artifacts:
            if artifact.name == "Blessed Sepulchre": # Greatest Treasure
                artifact_vp += 15
                continue
            if artifact.is_plastic:
                artifact_vp -= 10
                continue
            
            if artifact.first_word == "Blessed" or artifact.second_word == "Sepulchre": # Preferred
                artifact_vp += 5
                continue

            # Special Artifacts
            if artifact.name == "Treasure of Polaris":
                artifact_vp += 20
            elif artifact.name == "Slippers of Venus":
                artifact_vp += 10
            elif artifact.name == "Radioactive Isotope":
                artifact_vp -= 30
            elif artifact.name == "Lesser of Two Evils":
                artifact_vp -= 15
        
        vp += artifact_vp
        return vp


class Player:
    def __init__(self, name: str, character_type: str, user_id: str, home_world: World | None = None, 
                 diplomacy: dict | None = None, worlds: list[World] | None = None, fleets: list[Fleet] | None = None,
                 victory_points: int = 0, allies: list[str] | None = None,
                 jihad_target_player_id: str | None = None): # Added for Apostle Jihad
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
        self.jihad_target_player_id = jihad_target_player_id # Added for Apostle Jihad
        self.character = self.create_character()

    def create_character(self):
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
            print(f"Warning: Player {self.name} has unhandled character_type: {self.character_type}")
            return None


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

# Constants related to character types and commands, if they are closely tied to models.
# However, character_types and player_commands from app.py seem more like game logic/configuration
# rather than part of the data models themselves. For now, not moving them here.
# If they were used directly by, e.g., Player.create_character() in a way that required them
# to be co-located, then they would be moved.
# character_types = {"Empire Builder", "Merchant", "Pirate", "Artifact Collector", "Berserker", "Apostle"}
# player_commands = {"Transfer", "Build", "Move", "Fire", "Ambush", "Gift", "Trade", "Diplomacy", "Research", "End Turn", "ATTACH_ARTIFACT", "DROP_ARTIFACT", "AMBUSH", "SET_ALLY", "GIFT_WORLD", "GIFT_FLEET"}
# These are better left in app.py or a new config.py or game_rules.py.
