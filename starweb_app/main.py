import random # For assign_homeworld_to_player, assign_starting_fleets_to_player
import json 
from typing import Optional # Added for type hints

from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
# UserMixin is in models.User, werkzeug security functions are in models.User

import graphviz 

# Imports from the starweb_app package
from .game_engine import get_or_create_game, Game # Game is for type hinting
from .models import Player, User, World, Fleet, ALL_ARTIFACTS # World, Fleet, ALL_ARTIFACTS might be needed by moved utility functions or routes
# Character type classes are used by Player.create_character in models.py, not directly here.
# Order classes are used within game_engine.py's process_turn and order_from_dict

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'your_secret_key'  # TODO: Change this in production

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Name of the login route's view function
login_manager.login_message_category = 'info' # Bootstrap category for flash messages

# Global constants moved from app.py
character_types = {"Empire Builder", "Merchant", "Pirate", "Artifact Collector", "Berserker", "Apostle"}
player_commands = {"Transfer", "Build", "Move", "Fire", "Ambush", "Gift", "Trade", "Diplomacy", "Research", "End Turn", "ATTACH_ARTIFACT", "DROP_ARTIFACT", "AMBUSH", "SET_ALLY", "GIFT_WORLD", "GIFT_FLEET"}

# In-memory user store (moved from app.py)
users_db = {} # {username: UserObject}

class StarWeb:
    """This is a docstring for the StarWeb class"""
    # This class was a WSGI wrapper in the original app.py.
    # If Gunicorn or another WSGI server is used, it might target `app` directly from this file.
    # Or, if this wrapper is still desired, it would wrap `app` from this file.
    # For now, keeping its structure as it was.
    def __init__(self, application): # Changed 'app' to 'application' to avoid conflict with global `app`
        self.application = application

    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]: # user_id is username here
    return users_db.get(user_id)

# Utility functions moved from app.py (potentially legacy, review later)
def assign_homeworld_to_player(player_obj: Player, game_instance: Game):
    # This function now uses Player and Game from models and game_engine
    unowned_worlds = [world for world in game_instance.worlds if world.owner is None and not world.is_black_hole]
    if not unowned_worlds:
        raise Exception("No unowned, non-blackhole worlds available for new player!") 
    
    selected_homeworld = random.choice(unowned_worlds)
    
    selected_homeworld.owner = player_obj
    selected_homeworld.name = f"{player_obj.name}'s Homeworld"
    selected_homeworld.population = 50
    selected_homeworld.max_population = 100
    selected_homeworld.industry = 30
    selected_homeworld.mines = 2
    selected_homeworld.stockpile = 30
    selected_homeworld.iships = 1
    selected_homeworld.pships = 1
    selected_homeworld.turns_owned = 1
    selected_homeworld.robot_units = 0
    selected_homeworld.convert_units = 0
    selected_homeworld.converts_owner_id = None
    
    player_obj.home_world = selected_homeworld
    if selected_homeworld not in player_obj.worlds: # Should always be true if worlds list is managed correctly
        player_obj.worlds.append(selected_homeworld)
    
    print(f"Homeworld {selected_homeworld.name} (ID: {selected_homeworld.id}) assigned to player {player_obj.name}.")
    return selected_homeworld

def assign_starting_fleets_to_player(player_obj: Player, game_instance: Game):
    if not player_obj.home_world:
        raise Exception(f"Player {player_obj.name} has no homeworld to assign fleets to.")

    unowned_fleets = [fleet for fleet in game_instance.fleets if fleet.owner is None]
    
    fleets_to_assign_count = 5
    if len(unowned_fleets) < fleets_to_assign_count:
        print(f"Warning: Not enough unowned fleets ({len(unowned_fleets)}) for {player_obj.name}.")
        fleets_to_assign_count = len(unowned_fleets)
        if fleets_to_assign_count == 0:
            print(f"No unowned fleets to assign to player {player_obj.name}")
            return

    starting_fleets_assigned = 0
    for i in range(fleets_to_assign_count):
        fleet_to_assign = unowned_fleets[i] 
        fleet_to_assign.owner = player_obj
        fleet_to_assign.location = player_obj.home_world
        fleet_to_assign.ships = 0 
        fleet_to_assign.name = f"{player_obj.name}'s Fleet {starting_fleets_assigned + 1}"
        if fleet_to_assign not in player_obj.fleets: # Should always be true
            player_obj.fleets.append(fleet_to_assign)
        starting_fleets_assigned +=1
    
    print(f"{starting_fleets_assigned} starting fleets assigned to player {player_obj.name} at {player_obj.home_world.name}.")

# Legacy stream_... functions (move and review/remove later if unused)
# These used render_template, so they fit better here than in models/engine.
def stream_fleet(fleet: Fleet): # Type hint uses Fleet from .models
    # This function's direct usage might be obsolete if game.html iterates directly.
    # If it were still used by print(stream_fleet(fleet)), it would need to be:
    # return f"{fleet.name} {fleet.ships} ..." (a string representation)
    # Or, if it was meant to render a small HTML snippet:
    return render_template('fleet.html', fleet=fleet) # Requires fleet.html template

def stream_world(world: World): # Type hint uses World from .models
    # return render_template('world.html', world=world) # Requires world.html template
    # Simplified string representation if templates are not granular:
     return f"{world.name} Owner: {world.owner.name if world.owner else 'N/A'} Pop: {world.population}"

def stream_player(player: Player): # Type hint uses Player from .models
    # return render_template('player.html', player=player) # Requires player.html template
    return f"{player.name} Type: {player.character_type} VP: {player.victory_points}"

# Legacy command/transfer functions (move and review/remove later)
def is_valid_command(command: str) -> bool:
    return command in player_commands # player_commands is global here

# The following transfer_ships_* functions are likely superseded by Game.execute_transfer_order
# and should be reviewed for removal. They operate on objects directly, which is now encapsulated.
def transfer_ships_to_fleet(fleet1: Fleet, fleet2: Fleet, ships: int) -> bool:
    if fleet1.ships >= ships:
        fleet1.ships -= ships; fleet2.ships += ships
        return True
    return False

def transfer_ships_to_pships(fleet: Fleet, world: World, ships: int) -> bool:
    if fleet.ships >= ships:
        fleet.ships -= ships; world.pships += ships
        return True
    return False

def transfer_ships_to_iships(fleet: Fleet, world: World, ships: int) -> bool:
    if fleet.ships >= ships:
        fleet.ships -= ships; world.iships += ships
        return True
    return False

def transfer_iships_to_fleet(fleet: Fleet, world: World, ships: int) -> bool:
    if world.iships >= ships:
        world.iships -= ships; fleet.ships += ships
        return True
    return False

def transfer_pships_to_fleet(fleet: Fleet, world: World, ships: int) -> bool:
    if world.pships >= ships:
        world.pships -= ships; fleet.ships += ships
        return True
    return False

# Flask Routes
@app.route('/')
def hello_world():
    return 'Hello Starweb World! This is the new main.py speaking.'

@app.route('/game')
@login_required
def display_game():
    game_instance = get_or_create_game()
    current_player_ingame = None
    player_turn_events = []

    if current_user.is_authenticated: # current_user from flask_login
        current_player_ingame = game_instance.get_player_by_user_id(current_user.id)
        player_turn_events = game_instance.get_and_clear_turn_events(current_user.id)
    
    player_owned_worlds = current_player_ingame.worlds if current_player_ingame else []
    player_owned_fleets = current_player_ingame.fleets if current_player_ingame else []

    worlds_to_display = []
    fleets_to_display = []
    is_admin_view = False

    if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin:
        worlds_to_display = game_instance.worlds
        fleets_to_display = game_instance.fleets
        is_admin_view = True
    elif current_player_ingame:
        worlds_to_display = game_instance.get_visible_worlds_for_player(current_player_ingame)
        fleets_to_display = game_instance.get_visible_fleets_for_player(current_player_ingame)
    else:
        if current_user.is_authenticated:
            flash("Logged in, but not an active player. Limited view.", "warning")

    return render_template('game.html', 
                           game=game_instance, 
                           current_player_ingame=current_player_ingame,
                           worlds_to_display=worlds_to_display,
                           fleets_to_display=fleets_to_display,
                           player_owned_worlds=player_owned_worlds, # Added for dropdowns
                           player_owned_fleets=player_owned_fleets, # Added for dropdowns
                           is_admin_view=is_admin_view,
                           player_turn_events=player_turn_events,
                           all_artifacts=ALL_ARTIFACTS) # Pass ALL_ARTIFACTS for UI selectors

@app.route('/move_fleet', methods=['POST'])
@login_required
def move_fleet():
    # This route is now largely obsolete due to /submit_turn, but kept for now.
    flash("Direct /move_fleet is deprecated. Use 'Plan Your Turn'.", "info")
    return redirect(url_for('display_game'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('display_game'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            flash('Username, password, and confirmation are required!', 'danger')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        if username in users_db:
            flash('Username already exists.', 'warning')
            return redirect(url_for('register'))

        is_admin_user = (username.lower() == "admin") # Simple admin check
        
        # User model is from .models
        new_user = User(username=username, password=password, is_admin=is_admin_user)
        users_db[username] = new_user
        
        game_instance = get_or_create_game()
        ingame_player = None

        if not is_admin_user:
            character_type = request.form.get('character_type')
            if not character_type or character_type not in character_types:
                flash('Valid character type is required for players!', 'danger')
                users_db.pop(username, None) # Clean up
                return redirect(url_for('register'))
            
            existing_player = game_instance.get_player_by_user_id(new_user.id)
            if existing_player:
                flash(f'User {new_user.username} already has a player in game.', 'warning')
                return redirect(url_for('register')) # Or login
            
            # Player model from .models
            ingame_player = Player(name=new_user.username,
                                   character_type=character_type,
                                   user_id=new_user.id) # Ensure user_id is string if User.id is string
            game_instance.players.append(ingame_player)

            try:
                assign_homeworld_to_player(ingame_player, game_instance)
                assign_starting_fleets_to_player(ingame_player, game_instance)
                flash(f'Player {ingame_player.name} ({character_type}) created. Please login.', 'success')
            except Exception as e:
                flash(f'Error setting up player: {e}. User created, contact admin.', 'danger')
                if ingame_player in game_instance.players: game_instance.players.remove(ingame_player)
                # users_db.pop(username, None) # Keep user in users_db for login attempt
                return redirect(url_for('register'))
        else: # Admin user
            flash(f'Admin user {new_user.username} registered. Please login.', 'info')

        return redirect(url_for('login'))

    return render_template('register.html', character_types=character_types)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('display_game'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_db.get(username)
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('display_game'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/submit_turn', methods=['POST'])
@login_required
def submit_turn():
    game_instance = get_or_create_game()
    orders_json_str = request.form.get('orders_json')
    if not orders_json_str:
        flash("Error: No orders received.", "danger")
        return redirect(url_for('display_game'))
    try:
        raw_orders_list = json.loads(orders_json_str)
        if not isinstance(raw_orders_list, list):
            flash("Error: Orders format is invalid.", "danger")
            return redirect(url_for('display_game'))
    except json.JSONDecodeError:
        flash("Error: Could not decode orders JSON.", "danger")
        return redirect(url_for('display_game'))

    # game_instance.process_turn expects user_id (which is current_user.id)
    results_messages = game_instance.process_turn(current_user.id, raw_orders_list)
    for msg in results_messages: flash(msg) # Flash individual results
    if not results_messages and raw_orders_list: flash("Orders submitted, but no valid orders processed.", "warning")
    elif not raw_orders_list: flash("No orders submitted.", "info")
    return redirect(url_for('display_game'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/game_state_graph.svg')
@login_required
def admin_game_state_graph_svg():
    if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return "Unauthorized", 403

    game_instance = get_or_create_game()
    dot = graphviz.Digraph(comment='StarWeb Game State', graph_attr={'rankdir': 'LR', 'size': '12,8', 'ratio':'fill'})
    
    # Players
    for player_obj in game_instance.players: # Renamed to avoid conflict with Player model
        dot.node(f"player_{player_obj.user_id}", f"{player_obj.name}\n({player_obj.character_type})\nVP: {player_obj.victory_points}", 
                 shape="ellipse", style="filled", color="lightblue")
    # Worlds
    for world_obj in game_instance.worlds: # Renamed
        owner_name = world_obj.owner.name if world_obj.owner else "Unowned"
        label = f"W{world_obj.id}: {world_obj.name}\nOwner: {owner_name}\nPop: {world_obj.population} Ind: {world_obj.industry}\nStock: {world_obj.stockpile} Ships: I{world_obj.iships} P{world_obj.pships}"
        if world_obj.is_black_hole: label += "\n(Black Hole)"; dot.node(f"world_{world_obj.id}", label, shape="box", style="filled", color="black", fontcolor="white")
        else: dot.node(f"world_{world_obj.id}", label, shape="box", style="filled", color="lightgrey")
        if world_obj.owner: dot.edge(f"player_{world_obj.owner.user_id}", f"world_{world_obj.id}", label="owns", dir="forward", color="blue")
    # Fleets
    for fleet_obj in game_instance.fleets: # Renamed
        owner_name = fleet_obj.owner.name if fleet_obj.owner else "Unowned"
        label = f"F{fleet_obj.id}: {fleet_obj.name}\nOwner: {owner_name}\nShips: {fleet_obj.ships} Cargo: {fleet_obj.cargo}"
        if fleet_obj.is_ambushing: label += "\n(Ambush)"
        if fleet_obj.is_at_peace: label += "\n(Peace)"
        dot.node(f"fleet_{fleet_obj.id}", label, shape="septagon", style="filled", color="lightgreen")
        if fleet_obj.owner: dot.edge(f"player_{fleet_obj.owner.user_id}", f"fleet_{fleet_obj.id}", label="owns", dir="forward", color="green")
        if fleet_obj.location: dot.edge(f"fleet_{fleet_obj.id}", f"world_{fleet_obj.location.id}", label="at", dir="forward", color="darkgreen", style="dashed")
    # Connections
    processed_connections = set()
    for world_obj in game_instance.worlds: # Renamed
        for connected_world in world_obj.connections:
            if tuple(sorted((world_obj.id, connected_world.id))) not in processed_connections:
                dot.edge(f"world_{world_obj.id}", f"world_{connected_world.id}", dir="none", color="grey", style="bold")
                processed_connections.add(tuple(sorted((world_obj.id, connected_world.id))))
    try:
        svg_bytes = dot.pipe(format='svg')
        return Response(svg_bytes.decode('utf-8'), mimetype='image/svg+xml')
    except graphviz.backend.execute.ExecutableNotFound:
        app.logger.error("Graphviz not installed or not in PATH.")
        return Response("<svg><text>Error: Graphviz not found.</text></svg>", mimetype='image/svg+xml', status=500)
    except Exception as e:
        app.logger.error(f"SVG generation error: {e}")
        return Response(f"<svg><text>Error: {e}</text></svg>", mimetype='image/svg+xml', status=500)

# Entry point for running the Flask app (if this file is run directly)
# For Gunicorn or other WSGI servers, they would typically be pointed to `starweb_app.main:app`
if __name__ == '__main__':
    # The StarWeb WSGI wrapper might be applied here if still needed:
    # app.wsgi_app = StarWeb(app.wsgi_app) 
    # However, modern Flask development often doesn't require this custom wrapper.
    # Running with app.run() is for development.
    # Consider using `flask run` command or a proper WSGI server for production.
    app.run(debug=True) # debug=True for development, False for production
