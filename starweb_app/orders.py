from typing import List, Optional

# Original Order class from the initial orders.py, renamed to avoid conflict
# and to ensure original orders (AttachArtifactOrder etc.) use this.
class OrderWithPlayerId:
    def __init__(self, player_id: int, order_type: str, priority: int):
        self.player_id = player_id
        self.order_type = order_type
        self.priority = priority

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "order_type": self.order_type,
            "priority": self.priority,
        }

class AttachArtifactOrder(OrderWithPlayerId):
    def __init__(self, player_id: int, fleet_id: int, artifact_id: str, world_id: Optional[int] = None): # artifact_id is str, world_id optional
        super().__init__(player_id, "ATTACH_ARTIFACT", 2)
        self.fleet_id = fleet_id
        self.artifact_id = artifact_id
        self.world_id = world_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "fleet_id": self.fleet_id,
            "artifact_id": self.artifact_id,
        })
        if self.world_id is not None:
            data["world_id"] = self.world_id
        return data

class DropArtifactOrder(OrderWithPlayerId):
    def __init__(self, player_id: int, fleet_id: int, artifact_id: str, world_id: int): # artifact_id is str
        super().__init__(player_id, "DROP_ARTIFACT", 2)
        self.fleet_id = fleet_id
        self.artifact_id = artifact_id
        self.world_id = world_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "fleet_id": self.fleet_id,
            "artifact_id": self.artifact_id,
            "world_id": self.world_id,
        })
        return data

class SetAllyOrder(OrderWithPlayerId):
    def __init__(self, player_id: int, target_player_id: str): 
        super().__init__(player_id, "SET_ALLY", 10) 
        self.target_player_id = target_player_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "target_player_id": self.target_player_id,
        })
        return data

class GiftWorldOrder(OrderWithPlayerId):
    def __init__(self, player_id: int, world_id: int, recipient_player_id: str): 
        super().__init__(player_id, "GIFT_WORLD", 15)
        self.world_id = world_id
        self.recipient_player_id = recipient_player_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "world_id": self.world_id,
            "recipient_player_id": self.recipient_player_id,
        })
        return data

class GiftFleetOrder(OrderWithPlayerId):
    def __init__(self, player_id: int, fleet_id: int, recipient_player_id: str): 
        super().__init__(player_id, "GIFT_FLEET", 15)
        self.fleet_id = fleet_id
        self.recipient_player_id = recipient_player_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "fleet_id": self.fleet_id,
            "recipient_player_id": self.recipient_player_id,
        })
        return data

class AmbushOrder(OrderWithPlayerId):
    def __init__(self, player_id: int, fleet_id: int, world_id: int):
        super().__init__(player_id, "AMBUSH", 55)
        self.fleet_id = fleet_id
        self.world_id = world_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "fleet_id": self.fleet_id,
            "world_id": self.world_id,
        })
        return data

# --- Appended classes from app.py ---

# Order base class from app.py (this is the "simpler Order base class" that new orders will use)
class Order:
    """Base class for player orders."""
    def __init__(self, order_type: str, priority: int):
        self.order_type = order_type
        self.priority = priority

class MoveOrder(Order):
    """Represents a fleet movement order."""
    def __init__(self, fleet_id: int, target_world_ids: List[int]):
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
                 target_entity_id: Optional[int] = None, migration_pop_type: Optional[str] = None):
        super().__init__(order_type="BUILD", priority=30)
        self.world_id = world_id
        self.build_type = build_type 
        self.quantity = quantity
        self.target_entity_id = target_entity_id 
        self.migration_pop_type = migration_pop_type

class FireOrder(Order):
    """Represents a fire order for a fleet."""
    def __init__(self, firing_fleet_id: int, target_type: str, world_id: int, 
                 target_id: Optional[int] = None, is_conditional: bool = False):
        super().__init__(order_type="FIRE", priority=50)
        self.firing_fleet_id = firing_fleet_id
        self.target_type = target_type  
        self.world_id = world_id 
        self.target_id = target_id 
        self.is_conditional = is_conditional

class PlunderOrder(Order):
    """Represents a Pirate plunder order."""
    def __init__(self, world_id: int): # player_id will be derived from the user submitting the order
        super().__init__(order_type="PLUNDER", priority=7) # Priority 7 as requested
        self.world_id = world_id

class BuildPBBOrder(Order):
    """Represents an order to build a Planet Buster Bomb on a fleet."""
    def __init__(self, fleet_id: int):
        super().__init__(order_type="BUILD_PBB", priority=3) # Build phase priority
        self.fleet_id = fleet_id

class DropPBBOrder(Order):
    """Represents an order to drop a Planet Buster Bomb on a world."""
    def __init__(self, fleet_id: int, world_id: int):
        super().__init__(order_type="DROP_PBB", priority=6) # Combat phase, before movement
        self.fleet_id = fleet_id
        self.world_id = world_id

class DeclareJihadOrder(Order):
    """Represents an Apostle's order to declare Jihad against another player."""
    def __init__(self, target_player_id: str):
        super().__init__(order_type="DECLARE_JIHAD", priority=1) # Early phase priority
        self.target_player_id = target_player_id

class ScrapISHPsForIndustryOrder(Order):
    """Represents an Empire Builder order to scrap ISHPs for Industry."""
    def __init__(self, world_id: int, quantity: int):
        super().__init__(order_type="SCRAP_ISHPS_FOR_INDUSTRY", priority=3) # Build phase priority
        self.world_id = world_id
        self.quantity = quantity # Number of new industry units to create

class RobotAttackOrder(Order):
    """Represents a Berserker's robot attack order."""
    def __init__(self, fleet_id: int, num_ships_to_convert: int):
        super().__init__(order_type="ROBOT_ATTACK", priority=6) # Combat phase priority, similar to PBB drop
        self.fleet_id = fleet_id
        self.num_ships_to_convert = num_ships_to_convert
