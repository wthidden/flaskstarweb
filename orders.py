class Order:
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

class AttachArtifactOrder(Order):
    def __init__(self, player_id: int, fleet_id: int, artifact_id: int, world_id: int = None):
        super().__init__(player_id, "ATTACH_ARTIFACT", 2)  # Example priority
        self.fleet_id = fleet_id
        self.artifact_id = artifact_id
        self.world_id = world_id  # world_id is optional, artifact might be on another fleet

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "fleet_id": self.fleet_id,
            "artifact_id": self.artifact_id,
        })
        if self.world_id is not None:
            data["world_id"] = self.world_id
        return data

class DropArtifactOrder(Order):
    def __init__(self, player_id: int, fleet_id: int, artifact_id: int, world_id: int):
        super().__init__(player_id, "DROP_ARTIFACT", 2)  # Example priority
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

class SetAllyOrder(Order):
    def __init__(self, player_id: int, target_player_id: str): # target_player_id is user_id string
        super().__init__(player_id, "SET_ALLY", 10) 
        self.target_player_id = target_player_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "target_player_id": self.target_player_id,
        })
        return data

class GiftWorldOrder(Order):
    def __init__(self, player_id: int, world_id: int, recipient_player_id: str): # recipient_player_id is user_id string
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

class GiftFleetOrder(Order):
    def __init__(self, player_id: int, fleet_id: int, recipient_player_id: str): # recipient_player_id is user_id string
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

class AmbushOrder(Order):
    def __init__(self, player_id: int, fleet_id: int, world_id: int):
        super().__init__(player_id, "AMBUSH", 55)  # Priority example: 55 (between FIRE (50) and MOVE (60))
        self.fleet_id = fleet_id
        self.world_id = world_id

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "fleet_id": self.fleet_id,
            "world_id": self.world_id,
        })
        return data
