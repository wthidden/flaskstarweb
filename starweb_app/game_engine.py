import random
import json # For order_from_dict if it handles JSON strings directly (though it takes dicts)
from typing import List, Optional, Dict, Tuple # For type hints

# Imports from local packages (starweb_app)
from .models import (
    World, Fleet, Player, Artifact, ALL_ARTIFACTS,
    EmpireBuilder, Merchant, Pirate, ArtifactCollector, Berserker, Apostle # Character classes for Player.create_character
)
from .orders import (
    Order, # Simpler base Order from app.py
    MoveOrder, TransferOrder, LoadCargoOrder, UnloadCargoOrder, BuildOrder, FireOrder, # Orders from app.py
    # Original orders (now inheriting from OrderWithPlayerId)
    OrderWithPlayerId, # Base class for original orders
    AttachArtifactOrder, DropArtifactOrder, AmbushOrder, SetAllyOrder, GiftWorldOrder, GiftFleetOrder
)

# Global game instance, managed by get_or_create_game()
game = None # Moved from app.py

class Game:
    """This is a docstring for the Game class"""

    def __init__(self, worlds: List[World], fleets: List[Fleet], players: List[Player]):
        self.worlds = worlds
        self.fleets = fleets
        self.players = players
        self.turn_events: Dict[str, List[str]] = {} 
        self.turn_number = 0
        self.turn_vp_adjustments: Dict[str, int] = {} # For VPs gained/lost during order processing

    def add_turn_event(self, user_id_to_notify: str, message: str):
        if user_id_to_notify not in self.turn_events:
            self.turn_events[user_id_to_notify] = []
        self.turn_events[user_id_to_notify].append(message)

    def get_and_clear_turn_events(self, user_id: str) -> List[str]:
        events = self.turn_events.get(user_id, [])
        if user_id in self.turn_events:
            self.turn_events[user_id] = [] # Clear after retrieval
        return events

    # Helper methods for entity resolution
    def get_fleet(self, fleet_id: int) -> Optional[Fleet]:
        return next((f for f in self.fleets if f.id == fleet_id), None)

    def get_world(self, world_id: int) -> Optional[World]:
        return next((w for w in self.worlds if w.id == world_id), None)
    
    def get_player_by_user_id(self, user_id: str) -> Optional[Player]:
        return next((p for p in self.players if p.user_id == user_id), None)

    def get_artifact_by_id(self, artifact_id: str) -> Optional[Artifact]:
        return next((art for art in ALL_ARTIFACTS if art.id == artifact_id), None)

    def get_visible_worlds_for_player(self, current_player: Player) -> List[World]:
        if not current_player:
            return []
        visible_worlds = set()
        for world in self.worlds:
            if world.owner == current_player:
                visible_worlds.add(world)
        for fleet in self.fleets:
            if fleet.owner == current_player and fleet.location:
                visible_worlds.add(fleet.location)
        return list(visible_worlds)

    def get_visible_fleets_for_player(self, current_player: Player) -> List[Fleet]:
        if not current_player:
            return []
        visible_fleets_set = set()
        player_owned_world_ids = {world.id for world in self.worlds if world.owner == current_player}
        player_fleet_location_ids = set()
        for p_fleet in self.fleets:
            if p_fleet.owner == current_player and p_fleet.location:
                player_fleet_location_ids.add(p_fleet.location.id)

        for fleet_to_check in self.fleets:
            if fleet_to_check.owner == current_player:
                visible_fleets_set.add(fleet_to_check)
                continue
            if fleet_to_check.location:
                if fleet_to_check.location.id in player_owned_world_ids:
                    visible_fleets_set.add(fleet_to_check)
                    continue
                if fleet_to_check.location.id in player_fleet_location_ids:
                    visible_fleets_set.add(fleet_to_check)
                    continue
        return list(visible_fleets_set)

    # Order execution methods
    def execute_move_order(self, order: MoveOrder) -> Tuple[bool, str]:
        if not isinstance(order, MoveOrder):
            return False, "Invalid order type provided to execute_move_order."
        fleet_to_move = self.get_fleet(order.fleet_id)
        if not fleet_to_move:
            return False, f"Error: Fleet with ID {order.fleet_id} not found."
        if fleet_to_move.ships <= 0:
            return False, f"Error: Fleet {fleet_to_move.name} (ID: {order.fleet_id}) has no ships and cannot move."
        if not fleet_to_move.location:
             return False, f"Error: Fleet {fleet_to_move.name} (ID: {order.fleet_id}) has no current location."
        if not order.target_world_ids:
            return False, f"Error: No target worlds specified for fleet {fleet_to_move.name} (ID: {order.fleet_id})."
        if len(order.target_world_ids) > 2:
            return False, f"Error: Fleet {fleet_to_move.name} (ID: {order.fleet_id}) path too long (max 2 segments)."

        path_world_objects = []
        for world_id in order.target_world_ids:
            if world_id is None: 
                if len(path_world_objects) == 0:
                     return False, f"Error: First target world ID is null for fleet {fleet_to_move.name}."
                continue
            world_obj = self.get_world(world_id)
            if not world_obj:
                return False, f"Error: Target world with ID {world_id} not found for fleet {fleet_to_move.name}."
            path_world_objects.append(world_obj)
        
        if not path_world_objects:
             return False, f"Error: No valid target worlds for fleet {fleet_to_move.name}."

        current_location = fleet_to_move.location
        full_path_for_validation = [current_location] + path_world_objects 
        for i in range(len(full_path_for_validation) - 1):
            world1 = full_path_for_validation[i]
            world2 = full_path_for_validation[i+1]
            if world2 not in world1.connections and world1 not in world2.connections:
                return False, f"Error: World {world1.name} (ID: {world1.id}) is not connected to {world2.name} (ID: {world2.id})."
        
        final_destination_world = path_world_objects[-1]
        for i in range(len(path_world_objects)):
            intermediate_world_object = path_world_objects[i]
            is_intermediate_stop = (intermediate_world_object != final_destination_world)
            if is_intermediate_stop:
                world_owner = intermediate_world_object.owner
                moving_fleet_owner = fleet_to_move.owner
                if world_owner and world_owner != moving_fleet_owner and world_owner.user_id:
                    event_message = (
                        f"ALERT: Your world {intermediate_world_object.name} (ID: {intermediate_world_object.id}) "
                        f"was passed through by Fleet ID: {fleet_to_move.id} "
                        f"(Name: {fleet_to_move.name}, Owner: {moving_fleet_owner.name if moving_fleet_owner else 'Unowned'})."
                    )
                    self.add_turn_event(world_owner.user_id, event_message)
        fleet_to_move.location = final_destination_world
        return True, f"Fleet {fleet_to_move.name} (ID: {order.fleet_id}) moved to {final_destination_world.name} (ID: {final_destination_world.id})."

    def execute_transfer_order(self, order: TransferOrder) -> Tuple[bool, str]:
        if not isinstance(order, TransferOrder):
            return False, "Invalid order type for execute_transfer_order."
        if order.ship_count <= 0:
            return False, "Ship count must be positive."
        from_type = order.from_entity_type.upper()
        to_type = order.to_entity_type.upper()

        if from_type == "FLEET" and to_type == "FLEET":
            source_fleet = self.get_fleet(order.from_id)
            target_fleet = self.get_fleet(order.to_id)
            if not source_fleet or not target_fleet: return False, "Source or target fleet not found."
            if source_fleet.location != target_fleet.location: return False, "Fleets not in same location."
            if source_fleet.ships < order.ship_count: return False, f"Source fleet {source_fleet.name} has insufficient ships."
            if source_fleet.owner and target_fleet.owner and source_fleet.owner is not target_fleet.owner: return False, "Ownership mismatch."
            if source_fleet.cargo > 0: source_fleet.cargo = 0 
            source_fleet.ships -= order.ship_count
            target_fleet.ships += order.ship_count
            return True, f"Transferred {order.ship_count} ships from {source_fleet.name} to {target_fleet.name}."
        elif from_type == "FLEET" and (to_type == "PSHIP" or to_type == "ISHIP"):
            source_fleet = self.get_fleet(order.from_id)
            target_world = self.get_world(order.to_id)
            if not source_fleet or not target_world: return False, "Source fleet or target world not found."
            if source_fleet.location != target_world: return False, "Fleet not at world."
            if source_fleet.ships < order.ship_count: return False, f"Fleet {source_fleet.name} has insufficient ships."
            if source_fleet.owner and target_world.owner and source_fleet.owner is not target_world.owner: return False, "Ownership mismatch."
            if source_fleet.cargo > 0: source_fleet.cargo = 0
            source_fleet.ships -= order.ship_count
            if to_type == "PSHIP": target_world.pships += order.ship_count
            else: target_world.iships += order.ship_count
            return True, f"Transferred {order.ship_count} ships from {source_fleet.name} to {to_type}S at {target_world.name}."
        elif (from_type == "PSHIP" or from_type == "ISHIP") and to_type == "FLEET":
            source_world = self.get_world(order.from_id)
            target_fleet = self.get_fleet(order.to_id)
            if not source_world or not target_fleet: return False, "Source world or target fleet not found."
            if target_fleet.location != source_world: return False, "Fleet not at world."
            if source_world.owner and target_fleet.owner and source_world.owner is not target_fleet.owner: return False, "Ownership mismatch."
            if from_type == "PSHIP":
                if source_world.pships < order.ship_count: return False, f"{source_world.name} has insufficient PSHIPS."
                source_world.pships -= order.ship_count
            else: # ISHIP
                if source_world.iships < order.ship_count: return False, f"{source_world.name} has insufficient ISHIPS."
                source_world.iships -= order.ship_count
            target_fleet.ships += order.ship_count
            return True, f"Transferred {order.ship_count} {from_type.lower()}s from {source_world.name} to {target_fleet.name}."
        elif (from_type == "PSHIP" and to_type == "ISHIP") or (from_type == "ISHIP" and to_type == "PSHIP"):
            if order.from_id != order.to_id: return False, "PSHIP/ISHIP transfers must be at same world."
            world = self.get_world(order.from_id)
            if not world: return False, "World not found."
            if from_type == "PSHIP":
                if world.pships < order.ship_count: return False, f"{world.name} has insufficient PSHIPS."
                world.pships -= order.ship_count
                world.iships += order.ship_count
            else: # ISHIP to PSHIP
                if world.iships < order.ship_count: return False, f"{world.name} has insufficient ISHIPS."
                world.iships -= order.ship_count
                world.pships += order.ship_count
            return True, f"Transferred {order.ship_count} {from_type.lower()}s to {to_type.lower()}s at {world.name}."
        else:
            return False, f"Invalid transfer: {from_type} to {to_type}."

    def execute_unload_cargo_order(self, order: UnloadCargoOrder) -> Tuple[bool, str]:
        if not isinstance(order, UnloadCargoOrder): return False, "Invalid order type."
        fleet = self.get_fleet(order.fleet_id)
        world = self.get_world(order.world_id)
        if not fleet or not world: return False, "Fleet or world not found."
        if fleet.location != world: return False, "Fleet not at world."
        if fleet.owner and world.owner and fleet.owner is not world.owner: return False, "Ownership mismatch."
        
        amount_to_unload = fleet.cargo if order.metal_amount == -1 else order.metal_amount
        if amount_to_unload < 0: return False, "Cannot unload negative metal."
        if amount_to_unload > fleet.cargo: return False, f"Fleet {fleet.name} has insufficient cargo."

        fleet.cargo -= amount_to_unload
        msg_action = ""; event_message_suffix = ""
        vp_gain_for_unload = 0

        if fleet.owner and fleet.owner.character_type == "Merchant":
            if not order.as_consumer_goods:
                if world.owner != fleet.owner and world.owner is not None and world.industry > 0:
                    metal_for_points = min(amount_to_unload, world.industry * 2)
                    vp_gain_for_unload = metal_for_points * 8
                    if vp_gain_for_unload > 0:
                        self.turn_vp_adjustments[fleet.owner.user_id] = self.turn_vp_adjustments.get(fleet.owner.user_id, 0) + vp_gain_for_unload
                        event_message_suffix = f" Merchant {fleet.owner.name} gained {vp_gain_for_unload} VP."
                        self.add_turn_event(fleet.owner.user_id, f"Gained {vp_gain_for_unload} VP for unloading {metal_for_points} metal at {world.name}.")
                world.stockpile += amount_to_unload
                msg_action = f"to stockpile at {world.name}."
            else: # As consumer goods
                world.cg_unloads_count += 1
                cg_vp_map = {1: 10, 2: 8, 3: 5, 4: 3}
                vp_gain_for_unload = cg_vp_map.get(world.cg_unloads_count, 1)
                if vp_gain_for_unload > 0:
                    self.turn_vp_adjustments[fleet.owner.user_id] = self.turn_vp_adjustments.get(fleet.owner.user_id, 0) + vp_gain_for_unload
                    event_message_suffix = f" Merchant {fleet.owner.name} gained {vp_gain_for_unload} VP."
                    self.add_turn_event(fleet.owner.user_id, f"Gained {vp_gain_for_unload} VP for unloading CGs at {world.name} (Unload #{world.cg_unloads_count}).")
                msg_action = f"as consumer goods at {world.name}."
        else: # Not a merchant
            if not order.as_consumer_goods:
                world.stockpile += amount_to_unload
                msg_action = f"to stockpile at {world.name}."
            else:
                world.cg_unloads_count += 1 
                msg_action = f"as consumer goods at {world.name}."
        
        return True, f"Unloaded {amount_to_unload} metal from {fleet.name} {msg_action}{event_message_suffix}"

    def execute_load_cargo_order(self, order: LoadCargoOrder) -> Tuple[bool, str]:
        if not isinstance(order, LoadCargoOrder): return False, "Invalid order type."
        fleet = self.get_fleet(order.fleet_id)
        world = self.get_world(order.world_id)
        if not fleet or not world: return False, "Fleet or world not found."
        if fleet.location != world: return False, "Fleet not at world."
        if world.owner and (not fleet.owner or fleet.owner is not world.owner): return False, "Cannot load from world not owned by fleet owner (unless unowned - future rule)."

        max_cargo_capacity = fleet.get_max_cargo_capacity()
        can_load_more = max_cargo_capacity - fleet.cargo
        if can_load_more <= 0 and order.metal_amount != 0 :
             if order.metal_amount != -1 or fleet.cargo >= max_cargo_capacity:
                return False, f"Fleet {fleet.name} is full or cannot load more."

        amount_to_load = min(world.stockpile, can_load_more) if order.metal_amount == -1 else order.metal_amount
        if amount_to_load < 0: return False, "Cannot load negative metal."
        if amount_to_load > can_load_more: return False, f"Fleet {fleet.name} has insufficient capacity."
        if amount_to_load > world.stockpile: return False, f"World {world.name} has insufficient stockpile."

        fleet.cargo += amount_to_load
        world.stockpile -= amount_to_load
        return True, f"Loaded {amount_to_load} metal onto {fleet.name} from {world.name}."

    def execute_fire_order(self, order: FireOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, FireOrder): return False, "Invalid order type."
        firing_fleet = self.get_fleet(order.firing_fleet_id)
        world = self.get_world(order.world_id)
        if not firing_fleet or not world: return False, "Firing fleet or world not found."
        if firing_fleet.owner != current_player: return False, "Fleet not owned by player."
        if firing_fleet.location != world: return False, "Fleet not at firing world."
        if firing_fleet.is_at_peace: return False, "Fleet is at peace."
        if firing_fleet.is_ambushing: firing_fleet.is_ambushing = False # Attacking removes ambush
        if order.is_conditional: return True, "Conditional fire order noted (no fire under current rules)."

        num_effective_ships = firing_fleet.ships
        if firing_fleet.owner.character_type == "Merchant":
            ships_carrying_extra_load = 0
            if firing_fleet.cargo > firing_fleet.ships:
                ships_carrying_extra_load = firing_fleet.cargo - firing_fleet.ships
            num_effective_ships = firing_fleet.ships - ships_carrying_extra_load
        
        num_shots = num_effective_ships
        if num_shots <= 0: return False, f"Fleet {firing_fleet.name} has 0 effective ships to fire."

        if current_player.character_type == "Apostle":
            apostle_penalty_vp = num_shots * -1
            self.turn_vp_adjustments[current_player.user_id] = self.turn_vp_adjustments.get(current_player.user_id, 0) + apostle_penalty_vp
            self.add_turn_event(current_player.user_id, f"Lost {abs(apostle_penalty_vp)} VP for firing as Apostle.")

        message_parts = [f"Fleet {firing_fleet.name} (Player {current_player.name}) fires {num_shots} shots at {world.name} targeting {order.target_type}."]
        shots_remaining = num_shots

        if order.target_type == "FLEET":
            if order.target_id is None: return False, "No target_id for FLEET target."
            target_fleet = self.get_fleet(order.target_id)
            if not target_fleet: return False, f"Target fleet ID {order.target_id} not found."
            if target_fleet.location != world: return False, "Target fleet not at world."
            if target_fleet.owner == current_player: return False, "Cannot target own fleet."
            if target_fleet.is_at_peace: return False, "Cannot target fleet at peace."

            if target_fleet.is_ambushing and target_fleet.owner and target_fleet.owner != current_player:
                message_parts.append(f"Target fleet {target_fleet.name} was ambushing!")
                num_ambush_shots = target_fleet.ships
                if num_ambush_shots > 0:
                    ambush_hits_per_ship = 1 if firing_fleet.cargo > 0 else 2
                    ambush_ships_destroyed_potential = num_ambush_shots // ambush_hits_per_ship
                    actual_ambush_ships_lost_by_attacker = min(ambush_ships_destroyed_potential, firing_fleet.ships)
                    firing_fleet.ships -= actual_ambush_ships_lost_by_attacker
                    message_parts.append(f"Ambusher {target_fleet.name} fires {num_ambush_shots} shots, destroying {actual_ambush_ships_lost_by_attacker} of {firing_fleet.name}'s ships.")
                    if firing_fleet.ships <= 0:
                        firing_fleet.owner = None
                        message_parts.append(f"Attacking fleet {firing_fleet.name} destroyed by ambush!")
                        target_fleet.is_ambushing = False
                        return True, " ".join(message_parts)
                target_fleet.is_ambushing = False
            
            # Recalculate attacker's shots if they took damage
            num_effective_ships_after_ambush = firing_fleet.ships
            if firing_fleet.owner.character_type == "Merchant":
                ships_carrying_extra_load_after_ambush = 0
                if firing_fleet.cargo > firing_fleet.ships: ships_carrying_extra_load_after_ambush = firing_fleet.cargo - firing_fleet.ships
                num_effective_ships_after_ambush = firing_fleet.ships - ships_carrying_extra_load_after_ambush
            num_shots = num_effective_ships_after_ambush # Update shots_remaining as well
            shots_remaining = num_shots 
            if num_shots <= 0:
                message_parts.append(f"Attacking fleet {firing_fleet.name} has no ships capable of firing after ambush.")
                return True, " ".join(message_parts)
            
            hits_per_ship = 1 if target_fleet.cargo > 0 else 2
            ships_destroyed_potential = shots_remaining // hits_per_ship
            actual_ships_lost = min(ships_destroyed_potential, target_fleet.ships)
            target_fleet.ships -= actual_ships_lost
            message_parts.append(f"Hit {target_fleet.name}, destroying {actual_ships_lost} ships.")
            if target_fleet.ships <= 0:
                original_owner_before_destruction = target_fleet.owner
                target_fleet.owner = None 
                message_parts.append(f"Target fleet {target_fleet.name} is now unowned.")
                if current_player.character_type == "Berserker" and original_owner_before_destruction and original_owner_before_destruction != current_player:
                    vp_gain = actual_ships_lost * 2
                    self.turn_vp_adjustments[current_player.user_id] = self.turn_vp_adjustments.get(current_player.user_id, 0) + vp_gain
                    message_parts.append(f"Berserker {current_player.name} gained {vp_gain} VP.")
                    self.add_turn_event(current_player.user_id, f"Gained {vp_gain} VP for destroying ships of {target_fleet.name}.")
        
        elif order.target_type == "INDUSTRY":
            iships_destroyed = min(world.iships, shots_remaining // 2)
            if iships_destroyed > 0:
                world.iships -= iships_destroyed; shots_remaining -= iships_destroyed * 2
                message_parts.append(f"Destroyed {iships_destroyed} ISHIPS.")
            industry_destroyed = min(world.industry, shots_remaining // 2)
            if industry_destroyed > 0:
                world.industry -= industry_destroyed
                message_parts.append(f"Destroyed {industry_destroyed} industry.")
            if iships_destroyed == 0 and industry_destroyed == 0: message_parts.append("No ISHIPS or industry destroyed.")

        elif order.target_type == "POPULATION":
            pships_destroyed = min(world.pships, shots_remaining // 2)
            if pships_destroyed > 0:
                world.pships -= pships_destroyed; shots_remaining -= pships_destroyed * 2
                message_parts.append(f"Destroyed {pships_destroyed} PSHIPS.")
            
            pop_killed_potential = shots_remaining // 2
            total_killable_pop = world.population + world.convert_units + world.robot_units
            actual_total_pop_killed = min(total_killable_pop, pop_killed_potential)
            
            if actual_total_pop_killed > 0:
                killed_normal = min(world.population, actual_total_pop_killed)
                world.population -= killed_normal; message_parts.append(f"Killed {killed_normal} normal pop.")
                remaining_to_kill = actual_total_pop_killed - killed_normal
                
                if remaining_to_kill > 0:
                    killed_converts = min(world.convert_units, remaining_to_kill)
                    world.convert_units -= killed_converts; message_parts.append(f"Killed {killed_converts} converts.")
                    if killed_converts > 0 and world.converts_owner_id and world.converts_owner_id != current_player.user_id:
                        martyr_apostle = self.get_player_by_user_id(world.converts_owner_id)
                        if martyr_apostle and martyr_apostle.character_type == "Apostle":
                            martyr_vp = killed_converts * 1
                            self.turn_vp_adjustments[martyr_apostle.user_id] = self.turn_vp_adjustments.get(martyr_apostle.user_id, 0) + martyr_vp
                            message_parts.append(f"Apostle {martyr_apostle.name} gained {martyr_vp} VP for martyrs.")
                    if world.convert_units == 0: world.converts_owner_id = None
                    remaining_to_kill -= killed_converts

                if remaining_to_kill > 0:
                    killed_robots = min(world.robot_units, remaining_to_kill)
                    world.robot_units -= killed_robots; message_parts.append(f"Killed {killed_robots} robots.")

                if current_player.character_type == "Berserker":
                    vp_change = actual_total_pop_killed * 2
                    self.turn_vp_adjustments[current_player.user_id] = self.turn_vp_adjustments.get(current_player.user_id, 0) + vp_change
                    message_parts.append(f"Berserker {current_player.name} gained {vp_change} VP for killing population.")
                else:
                    vp_change = actual_total_pop_killed * -1 # Penalty for non-Berserker
                    self.turn_vp_adjustments[current_player.user_id] = self.turn_vp_adjustments.get(current_player.user_id, 0) + vp_change
                    message_parts.append(f"Player {current_player.name} lost {abs(vp_change)} VP for killing population.")
            elif pships_destroyed == 0 : message_parts.append("No PSHIPS or population destroyed.")


        elif order.target_type == "HOME_FLEETS":
            iships_destroyed = min(world.iships, shots_remaining // 2)
            if iships_destroyed > 0:
                world.iships -= iships_destroyed; shots_remaining -= iships_destroyed * 2
                message_parts.append(f"Destroyed {iships_destroyed} ISHIPS.")
            pships_destroyed = min(world.pships, shots_remaining // 2)
            if pships_destroyed > 0:
                world.pships -= pships_destroyed; shots_remaining -= pships_destroyed * 2
                message_parts.append(f"Destroyed {pships_destroyed} PSHIPS.")
            
            if world.iships == 0 and world.pships == 0 and shots_remaining >= 2 : # Assuming 2 shots to neutralize if empty
                if world.owner is not None:
                    message_parts.append(f"World {world.name} neutralized, now unowned.")
                    world.owner = None; world.turns_owned = 0
                else: message_parts.append(f"World {world.name} home fleets destroyed (was already unowned).")
            elif iships_destroyed == 0 and pships_destroyed == 0: message_parts.append("No home fleets destroyed.")
        else:
            return False, f"Unknown target_type '{order.target_type}'."
        return True, " ".join(message_parts)

    def execute_build_order(self, order: BuildOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, BuildOrder): return False, "Invalid order type."
        world = self.get_world(order.world_id)
        if not world: return False, "World not found."
        if world.owner != current_player: return False, "Player does not own world."
        if world.is_black_hole: return False, "Cannot build in black hole."

        build_type = order.build_type.upper()
        qty = order.quantity
        if qty <= 0: return False, "Quantity must be positive."

        if build_type == "SHIP_FLEET":
            cost_m, cost_p, req_i = qty * 1, qty * 1, qty * 1
            if world.stockpile < cost_m or world.population < cost_p or world.industry < req_i: return False, "Insufficient resources/industry for SHIP_FLEET."
            target_fleet = self.get_fleet(order.target_entity_id) if order.target_entity_id else None
            if not target_fleet or target_fleet.location != world or target_fleet.owner != current_player: return False, "Invalid target fleet."
            world.stockpile -= cost_m; world.population -= cost_p
            target_fleet.ships += qty
            return True, f"Built {qty} ships for fleet {target_fleet.name}."
        
        elif build_type == "SHIP_ISHOP" or build_type == "SHIP_PSHIP":
            cost_m, cost_p, req_i = qty * 1, qty * 1, qty * 1
            if world.stockpile < cost_m or world.population < cost_p or world.industry < req_i: return False, f"Insufficient resources/industry for {build_type}."
            world.stockpile -= cost_m; world.population -= cost_p
            if build_type == "SHIP_ISHOP": world.iships += qty
            else: world.pships += qty
            return True, f"Built {qty} {build_type}."

        elif build_type == "INDUSTRY" or build_type == "POP_LIMIT":
            cost_factor = 4 if current_player.character_type == "Empire Builder" else 5
            cost_m, cost_p, req_i = qty * cost_factor, qty * cost_factor, qty * cost_factor
            if world.stockpile < cost_m or world.population < cost_p or world.industry < req_i: return False, f"Insufficient resources/industry for {build_type}."
            world.stockpile -= cost_m; world.population -= cost_p
            if build_type == "INDUSTRY": world.industry += qty
            else: world.max_population += qty
            return True, f"Built {qty} {build_type.lower()}."

        elif build_type == "MIGRATE_POP":
            cost_m, req_i = qty * 1, qty * 1
            if world.stockpile < cost_m or world.industry < req_i: return False, "Insufficient resources/industry for MIGRATE_POP."
            target_world = self.get_world(order.target_entity_id) if order.target_entity_id else None
            if not target_world or target_world.is_black_hole or (target_world not in world.connections and world not in target_world.connections): return False, "Invalid target world for migration."
            
            pop_type = order.migration_pop_type.upper() if order.migration_pop_type else ""
            source_pop_count = 0
            if pop_type == "NORMAL": source_pop_count = world.population
            elif pop_type == "ROBOT": source_pop_count = world.robot_units
            elif pop_type == "CONVERT":
                source_pop_count = world.convert_units
                if world.converts_owner_id != current_player.user_id: return False, "Cannot migrate converts not controlled by player."
            else: return False, "Invalid population type for migration."
            if source_pop_count < qty: return False, f"Insufficient {pop_type} population at source."
            if pop_type == "NORMAL" and target_world.population + qty > target_world.max_population: return False, "Target world lacks capacity for normal population."

            world.stockpile -= cost_m
            if pop_type == "NORMAL": world.population -= qty; target_world.population += qty
            elif pop_type == "ROBOT": world.robot_units -= qty; target_world.robot_units += qty
            elif pop_type == "CONVERT":
                world.convert_units -= qty
                if target_world.converts_owner_id != current_player.user_id:
                    target_world.converts_owner_id = current_player.user_id
                    target_world.convert_units = qty 
                else: target_world.convert_units += qty
            return True, f"Migrated {qty} {pop_type} pop from {world.name} to {target_world.name}."

        elif build_type == "ROBOTS":
            if current_player.character_type != "Berserker": return False, "Only Berserkers can build robots."
            if not (world.robot_units > 0 and world.population == 0 and world.convert_units == 0 and world.owner == current_player): return False, "World not robot-controlled by player."
            cost_m_per_effort, req_i_per_effort, robots_per_effort, ops_robots_per_effort = 1, 1, 2, 1
            needed_m, needed_i, needed_ops_robots = qty*cost_m_per_effort, qty*req_i_per_effort, qty*ops_robots_per_effort
            if world.stockpile < needed_m or world.industry < needed_i or world.robot_units < needed_ops_robots: return False, "Insufficient resources/industry/operator robots."
            world.stockpile -= needed_m
            world.robot_units += qty * robots_per_effort
            return True, f"Built {qty * robots_per_effort} robots."
        else:
            return False, f"Unknown build_type '{build_type}'."

    def execute_attach_artifact_order(self, order: AttachArtifactOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, AttachArtifactOrder): return False, "Invalid order type."
        fleet = self.get_fleet(order.fleet_id)
        artifact = self.get_artifact_by_id(order.artifact_id) # Uses game's ALL_ARTIFACTS
        if not fleet or not artifact: return False, "Fleet or artifact not found."
        if fleet.owner != current_player: return False, "Fleet not owned by player."

        source_world = self.get_world(order.world_id) if order.world_id is not None else None
        source_fleet = None

        if source_world:
            if artifact not in source_world.artifacts: return False, "Artifact not at source world."
            if source_world.owner != current_player and source_world.owner is not None: return False, "Player does not own source world."
            if fleet.location != source_world: return False, "Fleet not at source world."
            source_world.artifacts.remove(artifact)
            fleet.artifacts.append(artifact)
            return True, f"Artifact {artifact.name} attached to {fleet.name} from {source_world.name}."
        else: # Artifact from another fleet (AC only)
            if current_player.character_type != "Artifact Collector": return False, "Only AC can transfer artifacts between own fleets."
            found_on_other_fleet = False
            for other_fleet in current_player.fleets:
                if other_fleet.id == fleet.id: continue
                if artifact in other_fleet.artifacts:
                    if other_fleet.location == fleet.location:
                        source_fleet = other_fleet; found_on_other_fleet = True; break
                    else: return False, "Source fleet not at same location."
            if not found_on_other_fleet: return False, "Artifact not found on player's other fleets at location."
            source_fleet.artifacts.remove(artifact)
            fleet.artifacts.append(artifact)
            return True, f"Artifact {artifact.name} transferred to {fleet.name} from {source_fleet.name}."
        return False, "Attach artifact error." # Should be covered

    def execute_drop_artifact_order(self, order: DropArtifactOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, DropArtifactOrder): return False, "Invalid order type."
        fleet = self.get_fleet(order.fleet_id)
        artifact = self.get_artifact_by_id(order.artifact_id)
        target_world = self.get_world(order.world_id)
        if not fleet or not artifact or not target_world: return False, "Fleet, artifact, or target world not found."
        if fleet.owner != current_player: return False, "Fleet not owned by player."
        if artifact not in fleet.artifacts: return False, "Artifact not on fleet."
        if fleet.location != target_world: return False, "Fleet not at target world."
        if target_world.is_black_hole: return False, "Cannot drop artifacts into black hole."
        
        fleet.artifacts.remove(artifact)
        target_world.artifacts.append(artifact)
        return True, f"Artifact {artifact.name} dropped from {fleet.name} to {target_world.name}."

    def execute_ambush_order(self, order: AmbushOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, AmbushOrder): return False, "Invalid order type."
        fleet = self.get_fleet(order.fleet_id)
        world = self.get_world(order.world_id)
        if not fleet or not world: return False, "Fleet or world not found."
        if fleet.owner != current_player: return False, "Fleet not owned by player."
        if fleet.location != world: return False, "Fleet not at ambush world."
        if fleet.ships <= 0: return False, "Fleet has no ships to ambush."
        if fleet.is_at_peace: return False, "Fleet at peace cannot ambush."
        fleet.is_ambushing = True
        return True, f"Fleet {fleet.name} set to ambush at {world.name}."

    def execute_set_ally_order(self, order: SetAllyOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, SetAllyOrder): return False, "Invalid order type."
        target_player = self.get_player_by_user_id(order.target_player_id)
        if not target_player: return False, "Target player not found."
        if current_player.user_id == order.target_player_id: return False, "Cannot ally with self."
        if order.target_player_id not in current_player.allies:
            current_player.allies.append(order.target_player_id)
            self.add_turn_event(current_player.user_id, f"You declared alliance with {target_player.name}.")
            self.add_turn_event(target_player.user_id, f"{current_player.name} declared alliance with you.")
            return True, f"{current_player.name} allied with {target_player.name}."
        return False, f"{current_player.name} already allied with {target_player.name}."

    def execute_gift_world_order(self, order: GiftWorldOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, GiftWorldOrder): return False, "Invalid order type."
        world = self.get_world(order.world_id)
        recipient = self.get_player_by_user_id(order.recipient_player_id)
        if not world or not recipient: return False, "World or recipient not found."
        if world.owner != current_player: return False, "Player does not own world."
        if current_player.user_id == recipient.user_id: return False, "Cannot gift to self."
        if world.is_black_hole: return False, "Cannot gift black hole."

        world.owner = recipient; world.turns_owned = 1
        if world.convert_units > 0:
            if recipient.character_type == "Apostle" and world.converts_owner_id == recipient.user_id: pass
            elif recipient.character_type == "Apostle": world.converts_owner_id = recipient.user_id
            else: world.convert_units = 0; world.converts_owner_id = None # Disband
        if world not in recipient.worlds: recipient.worlds.append(world)
        if world in current_player.worlds: current_player.worlds.remove(world)
        self.add_turn_event(current_player.user_id, f"You gifted {world.name} to {recipient.name}.")
        self.add_turn_event(recipient.user_id, f"{current_player.name} gifted {world.name} to you.")
        return True, f"{world.name} gifted from {current_player.name} to {recipient.name}."

    def execute_gift_fleet_order(self, order: GiftFleetOrder, current_player: Player) -> Tuple[bool, str]:
        if not isinstance(order, GiftFleetOrder): return False, "Invalid order type."
        fleet = self.get_fleet(order.fleet_id)
        recipient = self.get_player_by_user_id(order.recipient_player_id)
        if not fleet or not recipient: return False, "Fleet or recipient not found."
        if fleet.owner != current_player: return False, "Player does not own fleet."
        if current_player.user_id == recipient.user_id: return False, "Cannot gift to self."

        fleet.owner = recipient
        if fleet not in recipient.fleets: recipient.fleets.append(fleet)
        if fleet in current_player.fleets: current_player.fleets.remove(fleet)
        self.add_turn_event(current_player.user_id, f"You gifted {fleet.name} to {recipient.name}.")
        self.add_turn_event(recipient.user_id, f"{current_player.name} gifted {fleet.name} to you.")
        return True, f"{fleet.name} gifted from {current_player.name} to {recipient.name}."

    def process_turn(self, user_id: str, raw_orders_list: List[Dict]) -> List[str]:
        self.turn_number += 1
        print(f"Processing Turn {self.turn_number} for user: {user_id}")
        self.turn_vp_adjustments = {} # Reset for the turn

        current_player = self.get_player_by_user_id(user_id)
        if not current_player:
            return [f"Critical Error: Player not found for user_id {user_id}."]

        typed_orders: List[Order | OrderWithPlayerId] = [] # Union of possible order types
        for order_dict in raw_orders_list:
            # Pass player_id to order_from_dict for original orders that need it
            order_obj = order_from_dict(order_dict, player_id_for_original_orders=current_player.user_id) 
            if order_obj:
                typed_orders.append(order_obj)
            else:
                print(f"Warning: Could not create order from dict: {order_dict}")
        
        # Sort by priority. All order objects should have a .priority
        typed_orders.sort(key=lambda o: o.priority)

        results_messages: List[str] = []
        for order_obj in typed_orders:
            success, message = False, "Unknown order type or execution error."
            # Dispatch based on actual object type
            if isinstance(order_obj, MoveOrder): success, message = self.execute_move_order(order_obj)
            elif isinstance(order_obj, TransferOrder): success, message = self.execute_transfer_order(order_obj)
            elif isinstance(order_obj, LoadCargoOrder): success, message = self.execute_load_cargo_order(order_obj)
            elif isinstance(order_obj, UnloadCargoOrder): success, message = self.execute_unload_cargo_order(order_obj)
            elif isinstance(order_obj, BuildOrder): success, message = self.execute_build_order(order_obj, current_player)
            elif isinstance(order_obj, FireOrder): success, message = self.execute_fire_order(order_obj, current_player)
            # Original orders (now using OrderWithPlayerId)
            elif isinstance(order_obj, AttachArtifactOrder): success, message = self.execute_attach_artifact_order(order_obj, current_player)
            elif isinstance(order_obj, DropArtifactOrder): success, message = self.execute_drop_artifact_order(order_obj, current_player)
            elif isinstance(order_obj, AmbushOrder): success, message = self.execute_ambush_order(order_obj, current_player)
            elif isinstance(order_obj, SetAllyOrder): success, message = self.execute_set_ally_order(order_obj, current_player)
            elif isinstance(order_obj, GiftWorldOrder): success, message = self.execute_gift_world_order(order_obj, current_player)
            elif isinstance(order_obj, GiftFleetOrder): success, message = self.execute_gift_fleet_order(order_obj, current_player)
            else: message = f"Order type {type(order_obj).__name__} not recognized by process_turn."
            results_messages.append(f"Order ({order_obj.order_type} P{order_obj.priority}): {message} (Success: {success})")

        # Metal Production
        for world in self.worlds:
            if world.owner and not world.is_black_hole:
                pop_for_mining = 0
                if world.robot_units > 0 and world.population == 0 and world.convert_units == 0: pop_for_mining = world.robot_units
                elif world.robot_units == 0 and world.convert_units == 0: pop_for_mining = world.population
                if pop_for_mining > 0 and world.mines > 0:
                    produced = min(world.mines, pop_for_mining)
                    old_stockpile = world.stockpile
                    world.stockpile = min(world.stockpile + produced, 255)
                    if world.stockpile > old_stockpile: print(f"World {world.name} produced {world.stockpile - old_stockpile} metal.")
        
        # Reset Ambush Statuses
        for fleet_obj in self.fleets:
            if fleet_obj.is_ambushing: fleet_obj.is_ambushing = False

        # Population Growth (only for current player's worlds this turn for now)
        for world in self.worlds:
            if world.owner == current_player and not world.is_black_hole:
                if world.robot_units > 0: continue # Robots don't grow
                current_pop = world.population + world.convert_units
                if current_pop >= world.max_population: continue
                base_growth = current_pop // 10 if current_pop >= 10 else (1 if current_pop > 0 else 0)
                actual_growth = min(base_growth, world.max_population - current_pop)
                if actual_growth > 0:
                    if world.owner.character_type == "Apostle":
                        # Simplified: convert existing first, then grow new converts
                        converted_from_normal = min(actual_growth, world.population)
                        world.population -= converted_from_normal
                        world.convert_units += converted_from_normal
                        grew_new_converts = actual_growth - converted_from_normal
                        world.convert_units += grew_new_converts
                        world.converts_owner_id = world.owner.user_id
                        self.add_turn_event(user_id, f"{world.name} converted/grew {actual_growth} converts.")
                    else:
                        world.population += actual_growth
                        self.add_turn_event(user_id, f"{world.name} population grew by {actual_growth}.")

        self.resolve_world_and_key_capture()

        # Final VP Update for the current player
        base_vp = current_player.character.calculate_victory_points(self) # Pass game instance
        event_vp = self.turn_vp_adjustments.get(user_id, 0)
        current_player.victory_points = base_vp + event_vp
        vp_update_msg = f"End of Turn {self.turn_number} for {current_player.name}: Base VP: {base_vp}, Event VP: {event_vp}, Total VP: {current_player.victory_points}."
        self.add_turn_event(user_id, vp_update_msg)
        print(vp_update_msg)
        
        return results_messages

    def resolve_world_and_key_capture(self) -> List[str]:
        results_messages: List[str] = []
        print(f"Turn {self.turn_number}: Resolving world/key capture and mine increases...")
        # World Capture
        for world in self.worlds:
            if world.is_black_hole: continue
            eligible_fleets = [f for f in self.fleets if f.location == world and f.ships > 0 and not f.is_at_peace and f.owner]
            if not eligible_fleets: continue
            
            owners_present = {f.owner for f in eligible_fleets} # Set of Player objects
            if len(owners_present) == 1:
                new_owner = owners_present.pop()
                is_capturing_from_ally = False
                if world.owner and world.owner != new_owner:
                    if world.owner.user_id in new_owner.allies or new_owner.user_id in world.owner.allies:
                        is_capturing_from_ally = True
                
                if not is_capturing_from_ally and world.owner != new_owner:
                    old_owner_name = world.owner.name if world.owner else "Unowned"
                    capture_msg = f"World {world.name} captured by {new_owner.name} from {old_owner_name}."
                    results_messages.append(capture_msg); print(capture_msg)
                    if world.owner: self.add_turn_event(world.owner.user_id, f"Lost {world.name} to {new_owner.name}.")
                    self.add_turn_event(new_owner.user_id, f"Captured {world.name} from {old_owner_name}.")
                    world.owner = new_owner; world.turns_owned = 1
                    if new_owner.character_type != "Apostle" or world.converts_owner_id != new_owner.user_id:
                        if world.convert_units > 0: world.convert_units = 0; world.converts_owner_id = None
            
        # Key Capture
        for key_fleet in self.fleets:
            if key_fleet.owner is None and key_fleet.ships == 0 and key_fleet.location and not key_fleet.location.is_black_hole:
                world_of_key = key_fleet.location
                capturing_fleets = [f for f in self.fleets if f.location == world_of_key and f.ships > 0 and not f.is_at_peace and f.owner]
                capturing_owners = {f.owner for f in capturing_fleets}
                if len(capturing_owners) == 1:
                    new_owner_of_key = capturing_owners.pop()
                    key_fleet.owner = new_owner_of_key
                    key_msg = f"Unowned fleet key {key_fleet.name} at {world_of_key.name} now owned by {new_owner_of_key.name}."
                    results_messages.append(key_msg); print(key_msg)
                    self.add_turn_event(new_owner_of_key.user_id, f"Acquired key {key_fleet.name} at {world_of_key.name}.")

        # Turns Owned & Mine Increase
        for world in self.worlds:
            if world.owner and not world.is_black_hole:
                world.turns_owned += 1
                if world.turns_owned % 8 == 0: # Increase every 8 turns of continuous ownership
                    if world.mines > 0 and world.mines < 30: # Max 30 mines
                        world.mines += 1
                        mine_msg = f"{world.name} (Owner: {world.owner.name}) increased mines to {world.mines}."
                        results_messages.append(mine_msg); print(mine_msg)
                        self.add_turn_event(world.owner.user_id, mine_msg)
        return results_messages

def connect_all_worlds(worlds: List[World], min_connections_per_world: int = 1, avg_connections_per_world: int = 3):
    if not worlds: return
    num_worlds = len(worlds)
    for world in worlds: world.connections = [] # Reset connections

    connected_set = set()
    unconnected_set = set(worlds)
    if not unconnected_set: return # All worlds somehow processed or list empty

    start_world = unconnected_set.pop()
    connected_set.add(start_world)

    while unconnected_set:
        w1 = random.choice(list(connected_set))
        w2 = random.choice(list(unconnected_set))
        if w2 not in w1.connections: w1.connections.append(w2)
        if w1 not in w2.connections: w2.connections.append(w1)
        unconnected_set.remove(w2)
        connected_set.add(w2)

    current_edges = sum(len(w.connections) for w in worlds) // 2
    desired_total_edges = (num_worlds * avg_connections_per_world) // 2
    
    attempts_b = 0; max_attempts_b = num_worlds * num_worlds
    while current_edges < desired_total_edges and attempts_b < max_attempts_b:
        w_a, w_b = random.sample(worlds, 2)
        attempts_b += 1
        if w_b not in w_a.connections:
            w_a.connections.append(w_b); w_b.connections.append(w_a)
            current_edges += 1
            
    for world in worlds:
        attempts_c = 0; max_attempts_c_world = num_worlds * 10
        while len(world.connections) < min_connections_per_world and attempts_c < max_attempts_c_world:
            attempts_c +=1
            other_world = random.choice(worlds)
            if world is not other_world and other_world not in world.connections:
                world.connections.append(other_world)
                other_world.connections.append(world)

# Global helper function (moved from app.py)
def order_from_dict(order_dict: Dict, player_id_for_original_orders: Optional[str] = None) -> Optional[Order | OrderWithPlayerId]:
    order_type = order_dict.get('order_type')
    # player_id from order_dict is used if present (for original orders)
    # otherwise, player_id_for_original_orders is used for those that need it.
    # This logic assumes that simpler orders (MoveOrder etc.) do not have player_id in their dict.
    
    data = {k: v for k, v in order_dict.items() if k not in ['order_type', 'player_id']}

    try:
        # Simpler orders (subclassing simple Order from app.py)
        if order_type == "MOVE":
            raw_ids = data.get('target_world_ids', [])
            processed_ids = [int(id_val) for id_val in raw_ids if id_val is not None]
            if not processed_ids: return None
            data['target_world_ids'] = processed_ids
            return MoveOrder(**data)
        elif order_type == "TRANSFER": return TransferOrder(**data)
        elif order_type == "LOAD_CARGO": return LoadCargoOrder(**data)
        elif order_type == "UNLOAD_CARGO": return UnloadCargoOrder(**data)
        elif order_type == "BUILD":
            data['quantity'] = int(data['quantity'])
            if 'target_entity_id' in data and data['target_entity_id'] is not None:
                data['target_entity_id'] = int(data['target_entity_id'])
            return BuildOrder(**data)
        elif order_type == "FIRE":
            if 'is_conditional' in data: data['is_conditional'] = bool(data['is_conditional'])
            return FireOrder(**data)
        
        # Original orders (subclassing OrderWithPlayerId)
        # These need player_id, passed as player_id_for_original_orders
        elif player_id_for_original_orders is not None:
            # Ensure player_id_for_original_orders is int if it's numeric user ID, or handle as string if username.
            # The OrderWithPlayerId expects int. User.id from Flask-Login is usually string.
            # This needs careful handling. Assuming user_id (string) is okay if Player model's user_id is string.
            # The Player model has user_id: str. OrderWithPlayerId expects player_id: int.
            # For now, let's assume player_id_for_original_orders is the correct type or can be cast.
            # This is a potential type mismatch if original orders.py truly expected int player_id.
            # The original orders.py used player_id: int. Current Player.user_id is str.
            # This needs alignment. For now, I'll assume player_id from current_user.id (string) is used,
            # and the OrderWithPlayerId and its subclasses will handle this.
            # This part of the logic might need review based on how player IDs are stored and used.
            # Let's assume for now that order_dict might contain 'player_id' for these original orders.
            
            pid_to_use = order_dict.get('player_id', player_id_for_original_orders)
            # Attempt to cast to int if that's what OrderWithPlayerId expects
            try:
                pid_to_use = int(pid_to_use) 
            except ValueError:
                 print(f"Warning: player_id '{pid_to_use}' could not be cast to int for original order type {order_type}")
                 # Fallback or error based on how critical int player_id is for those old orders.
                 # If OrderWithPlayerId strictly needs int, this will fail.
                 # For now, let's assume it's meant to be an int, consistent with original orders.py.

            if order_type == "ATTACH_ARTIFACT":
                # world_id can be None, artifact_id is str
                data['world_id'] = data.get('world_id') # Ensure it's None if missing, not error
                return AttachArtifactOrder(player_id=pid_to_use, **data)
            elif order_type == "DROP_ARTIFACT": return DropArtifactOrder(player_id=pid_to_use, **data)
            elif order_type == "AMBUSH": return AmbushOrder(player_id=pid_to_use, **data)
            elif order_type == "SET_ALLY": return SetAllyOrder(player_id=pid_to_use, **data)
            elif order_type == "GIFT_WORLD": return GiftWorldOrder(player_id=pid_to_use, **data)
            elif order_type == "GIFT_FLEET": return GiftFleetOrder(player_id=pid_to_use, **data)
        
        else:
            print(f"Warning: Unknown order type '{order_type}' or missing player_id for original order.")
            return None
            
    except (TypeError, ValueError) as e:
        print(f"Error creating order {order_type} from dict {data} (player_id_for_original_orders: {player_id_for_original_orders}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error creating order {order_type}: {e}")
        return None


def create_game() -> Game:
    new_game = Game(worlds=[], fleets=[], players=[])
    for i in range(1, 256): # W1 to W255
        world = World(id=i, name=f"World {i}", owner=None, connections=[], iships=0, pships=0,
                      population=random.randint(0,20), max_population=random.randint(50,150),
                      industry=random.randint(0,5), mines=random.randint(0,3), stockpile=random.randint(0,50),
                      artifacts=[], robot_units=0, convert_units=0, converts_owner_id=None)
        new_game.worlds.append(world)
    
    connect_all_worlds(new_game.worlds)

    if ALL_ARTIFACTS and new_game.worlds:
        shuffled_artifacts = list(ALL_ARTIFACTS)
        random.shuffle(shuffled_artifacts)
        for artifact_instance in shuffled_artifacts:
            random.choice(new_game.worlds).artifacts.append(artifact_instance)

    for i in range(1, 256): # F1 to F255
        initial_location = random.choice(new_game.worlds) if new_game.worlds else None
        fleet = Fleet(id=i, name=f"Fleet {i}", ships=0, location=initial_location, owner=None, cargo=0, artifacts=[])
        new_game.fleets.append(fleet)

    for world_obj in new_game.worlds:
        if random.random() < 0.05: # 5% chance of black hole
            world_obj.is_black_hole = True
            world_obj.owner = None; world_obj.population = 0; world_obj.max_population = 0
            world_obj.industry = 0; world_obj.mines = 0; world_obj.stockpile = 0
            world_obj.iships = 0; world_obj.pships = 0; world_obj.artifacts = []
            world_obj.robot_units = 0; world_obj.convert_units = 0; world_obj.converts_owner_id = None
            world_obj.name = f"Black Hole W{world_obj.id}"
            # Consider clearing connections for black holes if they shouldn't be part of network
            # world_obj.connections = [] 
    return new_game

def get_or_create_game() -> Game:
    global game
    if game is None:
        game = create_game()
    return game
