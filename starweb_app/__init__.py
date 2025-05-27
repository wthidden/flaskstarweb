# This __init__.py file makes key components available at the package level.

from .main import app
from .game_engine import get_or_create_game
# For convenience, one might also expose Game, order_from_dict, create_game from game_engine
# from .game_engine import Game, order_from_dict, create_game

from .models import User, Player, World, Fleet, Artifact, ALL_ARTIFACTS
from .models import EmpireBuilder, Merchant, Pirate, ArtifactCollector, Berserker, Apostle

# It can also be useful to expose specific order classes if they are frequently used
# from .orders import MoveOrder, BuildOrder # etc.

# For now, keeping the top-level API concise as per the specific request.
# The Flask 'app' object is the most critical export for WSGI servers.
# Game-related singletons or core functions like get_or_create_game are also useful.
# Key models are good to have for type hinting or direct use if the app grows.
