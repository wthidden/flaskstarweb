// Data passed from Flask/Jinja - these will be defined in the <script> tag in game.html
// const playerOwnedWorlds = {{ player_owned_worlds|tojson|safe if player_owned_worlds else [] }};
// const playerOwnedFleets = {{ player_owned_fleets|tojson|safe if player_owned_fleets else [] }};
// const currentPlayerId = {{ current_player_ingame.user_id|tojson|safe if current_player_ingame else 'null' }};

document.addEventListener('DOMContentLoaded', function () {
    const orderTypeSelect = document.getElementById('orderType');
    const addOrderBtn = document.getElementById('addOrderBtn');
    const queuedOrdersListDiv = document.getElementById('queuedOrdersList');
    const turnForm = document.getElementById('turnForm');
    const ordersJsonInput = document.getElementById('ordersJsonInput');

    // Order specific input fieldsets
    const inputGroups = {
        'MOVE': document.getElementById('moveInputs'),
        'TRANSFER': document.getElementById('transferInputs'),
        'LOAD_CARGO': document.getElementById('loadInputs'),
        'UNLOAD_CARGO': document.getElementById('unloadInputs'),
        'BUILD': document.getElementById('buildInputs'),
        'FIRE': document.getElementById('fireInputs'),
        'ATTACH_ARTIFACT': document.getElementById('attachArtifactInputs'),
        'DROP_ARTIFACT': document.getElementById('dropArtifactInputs'),
        'AMBUSH': document.getElementById('ambushInputs'),
        'SET_ALLY': document.getElementById('setAllyInputs'),
        'GIFT_WORLD': document.getElementById('giftWorldInputs'),
        'GIFT_FLEET': document.getElementById('giftFleetInputs')
    };
    
    const fieldsToReplaceConfig = {
        'moveFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' },
        'transferFromId': { conditional: true, selectElementId: 'transferFromId' }, 
        'transferToId': { conditional: true, selectElementId: 'transferToId' },     
        'loadFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' },
        'loadWorldId': { data: playerOwnedWorlds, prefix: 'World', idField: 'id' },
        'unloadFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' },
        'unloadWorldId': { data: playerOwnedWorlds, prefix: 'World', idField: 'id' },
        'buildWorldId': { data: playerOwnedWorlds, prefix: 'World', idField: 'id' },
        'buildTargetEntityId': { conditional: true, selectElementId: 'buildTargetEntityId' }, 
        'fireFiringFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' },
        'attachArtifactFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' },
        'attachArtifactSourceWorldId': { data: playerOwnedWorlds, prefix: 'World', idField: 'id' },
        'dropArtifactFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' },
        'dropArtifactTargetWorldId': { data: playerOwnedWorlds, prefix: 'World', idField: 'id' }, 
        'ambushFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' },
        'ambushWorldId': { data: playerOwnedWorlds, prefix: 'World', idField: 'id' }, 
        'giftWorldId': { data: playerOwnedWorlds, prefix: 'World', idField: 'id' },
        'giftFleetId': { data: playerOwnedFleets, prefix: 'Fleet', idField: 'id' }
    };

    let queuedOrders = [];

    function populateSelect(selectElement, items, _valueField, textFieldPrefix, idFieldToUse) { 
        if (!selectElement) {
            return;
        }
        const currentValue = selectElement.value; // Preserve current value if possible
        selectElement.innerHTML = '<option value="">Select...</option>'; 
        if (items && Array.isArray(items)) {
            items.forEach(item => {
                if (item && typeof item === 'object' && item.hasOwnProperty(idFieldToUse) && item.hasOwnProperty('name')) {
                    const option = document.createElement('option');
                    option.value = item[idFieldToUse]; 
                    
                    let textContent = `${textFieldPrefix} ${item.name} (ID: ${item[idFieldToUse]})`;
                    if (item.ships !== undefined) {
                        textContent += ` - Ships: ${item.ships}`;
                    }
                    if (item.location && typeof item.location === 'object' && item.location.name && item.location.id) {
                         textContent += ` - Loc: W${item.location.id} (${item.location.name})`;
                    }
                    option.textContent = textContent;
                    if (item[idFieldToUse].toString() === currentValue) {
                        option.selected = true;
                    }
                    selectElement.appendChild(option);
                }
            });
        }
    }

    for (const fieldId in fieldsToReplaceConfig) {
        const originalInput = document.getElementById(fieldId);
        if (originalInput && originalInput.tagName.toUpperCase() === 'INPUT' && originalInput.type.toUpperCase() === 'NUMBER') { 
            const newSelect = document.createElement('select');
            newSelect.id = fieldId;
            newSelect.className = originalInput.className; // Preserve classes
            
            originalInput.parentNode.replaceChild(newSelect, originalInput);

            const fieldConfig = fieldsToReplaceConfig[fieldId];
            if (!fieldConfig.conditional) { 
                populateSelect(newSelect, fieldConfig.data, fieldConfig.idField, fieldConfig.prefix, fieldConfig.idField);
            }
        } else if (originalInput && originalInput.tagName.toUpperCase() === 'SELECT' && fieldsToReplaceConfig[fieldId].conditional) {
            // This handles cases where the field might already be a select (e.g. transferFromId)
            // and ensures it's correctly configured for dynamic population.
        }
    }
    
    const transferFromEntityTypeSelect = document.getElementById('transferFromEntityType');
    const transferFromIdSelect = document.getElementById('transferFromId'); 
    const transferToEntityTypeSelect = document.getElementById('transferToEntityType');
    const transferToIdSelect = document.getElementById('transferToId');     

    if (transferFromEntityTypeSelect && transferFromIdSelect) {
        transferFromEntityTypeSelect.addEventListener('change', function() {
            if (this.value === 'FLEET') {
                populateSelect(transferFromIdSelect, playerOwnedFleets, 'id', 'Fleet', 'id');
            } else { 
                populateSelect(transferFromIdSelect, playerOwnedWorlds, 'id', 'World', 'id');
            }
        });
        if(transferFromEntityTypeSelect.value) transferFromEntityTypeSelect.dispatchEvent(new Event('change'));
    }

    if (transferToEntityTypeSelect && transferToIdSelect) {
        transferToEntityTypeSelect.addEventListener('change', function() {
            if (this.value === 'FLEET') {
                populateSelect(transferToIdSelect, playerOwnedFleets, 'id', 'Fleet', 'id');
            } else { 
                populateSelect(transferToIdSelect, playerOwnedWorlds, 'id', 'World', 'id');
            }
        });
        if(transferToEntityTypeSelect.value) transferToEntityTypeSelect.dispatchEvent(new Event('change'));
    }

    const buildTypeSelect = document.getElementById('buildTypeSelect');
    const buildTargetEntityIdSelect = document.getElementById('buildTargetEntityId'); 
    const buildTargetEntityIdNumericInput = document.getElementById('buildTargetEntityIdNumeric'); 

    if (buildTypeSelect && buildTargetEntityIdSelect && buildTargetEntityIdNumericInput) {
        buildTypeSelect.addEventListener('change', function() {
            if (this.value === 'SHIP_FLEET') {
                buildTargetEntityIdSelect.style.display = 'block';
                buildTargetEntityIdNumericInput.style.display = 'none';
                populateSelect(buildTargetEntityIdSelect, playerOwnedFleets, 'id', 'Fleet', 'id');
            } else if (this.value === 'MIGRATE_POP') {
                buildTargetEntityIdSelect.style.display = 'none'; 
                buildTargetEntityIdNumericInput.style.display = 'block';
                buildTargetEntityIdSelect.innerHTML = '<option value="">Select...</option>'; 
            } else {
                buildTargetEntityIdSelect.style.display = 'none';
                buildTargetEntityIdNumericInput.style.display = 'none';
                buildTargetEntityIdSelect.innerHTML = '<option value="">Select...</option>'; 
            }
        });
        if(buildTypeSelect.value) buildTypeSelect.dispatchEvent(new Event('change'));
    }


    function updateOrderFormInputs() {
        const selectedType = orderTypeSelect.value;
        for (const type in inputGroups) {
            if (inputGroups[type]) {
                inputGroups[type].style.display = (type === selectedType) ? 'block' : 'none';
            }
        }
        if (selectedType === 'BUILD' && buildTypeSelect) { 
            buildTypeSelect.dispatchEvent(new Event('change'));
        }
    }

    function renderQueuedOrders() {
        queuedOrdersListDiv.innerHTML = '';
        if (queuedOrders.length === 0) {
            queuedOrdersListDiv.innerHTML = '<p>No orders queued yet.</p>';
            return;
        }
        queuedOrders.forEach((order, index) => {
            const orderDiv = document.createElement('div');
            let desc = `Order ${index + 1}: [${order.order_type}] `;
            switch(order.order_type) {
                case 'MOVE':
                    desc += `Fleet ${order.fleet_id} to World ${order.target_world_ids[0]}`;
                    if (order.target_world_ids.length > 1 && order.target_world_ids[1] !== null && order.target_world_ids[1] !== undefined) {
                        desc += ` then to World ${order.target_world_ids[1]}`;
                    }
                    break;
                case 'TRANSFER':
                    desc += `${order.ship_count} ships from ${order.from_entity_type} ID ${order.from_id} to ${order.to_entity_type} ID ${order.to_id}`;
                    break;
                case 'LOAD_CARGO':
                    desc += `Fleet ${order.fleet_id} load ${order.metal_amount === -1 ? 'all' : order.metal_amount} metal from World ${order.world_id}`;
                    break;
                case 'UNLOAD_CARGO':
                    desc += `Fleet ${order.fleet_id} unload ${order.metal_amount === -1 ? 'all' : order.metal_amount} metal at World ${order.world_id}`;
                    if (order.as_consumer_goods) desc += ' as Consumer Goods';
                    break;
                case 'BUILD':
                    desc += `World ${order.world_id} build ${order.quantity} of ${order.build_type}`;
                    if (order.target_entity_id !== null && order.target_entity_id !== undefined) desc += ` -> Target ID: ${order.target_entity_id}`;
                    if (order.migration_pop_type) desc += ` (Type: ${order.migration_pop_type})`;
                    break;
                case 'FIRE':
                    desc += `Fleet ${order.firing_fleet_id} at World ${order.world_id} fire at ${order.target_type}`;
                    if (order.target_id !== null && order.target_id !== undefined) desc += ` ID: ${order.target_id}`;
                    if (order.is_conditional) desc += ' (Conditional)';
                    break;
                case 'ATTACH_ARTIFACT':
                    desc += `Fleet ${order.fleet_id} attach artifact ${order.artifact_id}`;
                    if (order.world_id !== null && order.world_id !== undefined && order.world_id !== "") {
                        desc += ` from World ${order.world_id}`;
                    } else {
                        desc += ` from another fleet at same location`;
                    }
                    break;
                case 'DROP_ARTIFACT':
                    desc += `Fleet ${order.fleet_id} drop artifact ${order.artifact_id} at World ${order.world_id}`;
                    break;
                case 'AMBUSH':
                    desc += `Fleet ${order.fleet_id} will ambush at World ${order.world_id}`;
                    break;
                case 'SET_ALLY':
                    desc += `Declare alliance with Player ${order.target_player_id}`;
                    break;
                case 'GIFT_WORLD':
                    desc += `Gift World ${order.world_id} to Player ${order.recipient_player_id}`;
                    break;
                case 'GIFT_FLEET':
                    desc += `Gift Fleet ${order.fleet_id} to Player ${order.recipient_player_id}`;
                    break;
                default:
                    desc += 'Unknown order parameters';
            }
            orderDiv.textContent = desc;
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.type = 'button';
            removeBtn.dataset.index = index;
            removeBtn.addEventListener('click', function() {
                queuedOrders.splice(parseInt(this.dataset.index), 1);
                renderQueuedOrders();
            });
            orderDiv.appendChild(removeBtn);
            queuedOrdersListDiv.appendChild(orderDiv);
        });
    }

    addOrderBtn.addEventListener('click', function () {
        const selectedType = orderTypeSelect.value;
        let newOrder = { order_type: selectedType };
        let valid = true;

        function getSelectedValue(elementId) {
            const element = document.getElementById(elementId);
            return element ? element.value : null;
        }
        function getIntValue(elementId) {
            const val = getSelectedValue(elementId);
            if (val === "" || val === null) return NaN; 
            return parseInt(val);
        }
         function getOptionalIntValue(elementId) { 
            const val = getSelectedValue(elementId);
            if (val === "" || val === null) return null; 
            const num = parseInt(val);
            return isNaN(num) ? null : num; 
        }


        switch (selectedType) {
            case 'MOVE':
                newOrder.fleet_id = getIntValue('moveFleetId');
                const moveWorld1Id = getIntValue('moveWorld1Id'); 
                const moveWorld2Id = getOptionalIntValue('moveWorld2Id'); 
                if (isNaN(newOrder.fleet_id) || isNaN(moveWorld1Id)) { valid = false; alert("Fleet and World 1 ID are required."); break;}
                newOrder.target_world_ids = [moveWorld1Id];
                if (moveWorld2Id !== null) newOrder.target_world_ids.push(moveWorld2Id);
                break;
            case 'TRANSFER':
                newOrder.ship_count = getIntValue('transferShipCount');
                newOrder.from_entity_type = getSelectedValue('transferFromEntityType');
                newOrder.from_id = getIntValue('transferFromId');
                newOrder.to_entity_type = getSelectedValue('transferToEntityType');
                newOrder.to_id = getIntValue('transferToId');
                if (isNaN(newOrder.ship_count) || newOrder.ship_count <= 0 || isNaN(newOrder.from_id) || isNaN(newOrder.to_id)) { valid = false; alert("Valid Ship Count, From/To IDs required."); break; }
                break;
            case 'LOAD_CARGO':
                newOrder.fleet_id = getIntValue('loadFleetId');
                newOrder.world_id = getIntValue('loadWorldId');
                newOrder.metal_amount = getIntValue('loadMetalAmount');
                if (isNaN(newOrder.fleet_id) || isNaN(newOrder.world_id) || isNaN(newOrder.metal_amount)) { valid = false; alert("Valid Fleet, World, and Amount required."); break; }
                break;
            case 'UNLOAD_CARGO':
                newOrder.fleet_id = getIntValue('unloadFleetId');
                newOrder.world_id = getIntValue('unloadWorldId');
                newOrder.metal_amount = getIntValue('unloadMetalAmount');
                newOrder.as_consumer_goods = document.getElementById('unloadAsCG').checked;
                if (isNaN(newOrder.fleet_id) || isNaN(newOrder.world_id) || isNaN(newOrder.metal_amount)) { valid = false; alert("Valid Fleet, World, and Amount required."); break; }
                break;
            case 'BUILD':
                newOrder.world_id = getIntValue('buildWorldId');
                newOrder.build_type = getSelectedValue('buildTypeSelect');
                newOrder.quantity = getIntValue('buildQuantity');
                
                if (newOrder.build_type === 'SHIP_FLEET') {
                    newOrder.target_entity_id = getIntValue('buildTargetEntityId');
                } else if (newOrder.build_type === 'MIGRATE_POP') {
                    newOrder.target_entity_id = getIntValue('buildTargetEntityIdNumeric'); 
                    newOrder.migration_pop_type = getSelectedValue('buildMigrationPopType');
                } else {
                    newOrder.target_entity_id = null;
                }

                if (isNaN(newOrder.world_id) || isNaN(newOrder.quantity) || newOrder.quantity <= 0) { valid = false; alert("Valid World ID and positive Quantity required."); break; }
                if ((newOrder.build_type === 'SHIP_FLEET' || newOrder.build_type === 'MIGRATE_POP') && (newOrder.target_entity_id === null || isNaN(newOrder.target_entity_id))) { 
                    valid = false; alert("Target ID is required and must be a number for this build type."); break; 
                }
                break;
            case 'FIRE':
                newOrder.firing_fleet_id = getIntValue('fireFiringFleetId');
                newOrder.target_type = getSelectedValue('fireTargetTypeSelect');
                newOrder.world_id = getIntValue('fireWorldId'); 
                newOrder.target_id = newOrder.target_type === 'FLEET' ? getOptionalIntValue('fireTargetFleetId') : null; 
                newOrder.is_conditional = document.getElementById('fireIsConditional').checked;
                if (isNaN(newOrder.firing_fleet_id) || isNaN(newOrder.world_id)) { valid = false; alert("Firing Fleet and World ID required."); break; }
                if (newOrder.target_type === 'FLEET' && (newOrder.target_id === null || isNaN(newOrder.target_id))) { valid = false; alert("Target Fleet ID required for FLEET target type."); break; }
                break;
            case 'ATTACH_ARTIFACT':
                newOrder.fleet_id = getIntValue('attachArtifactFleetId');
                newOrder.artifact_id = getSelectedValue('attachArtifactId'); 
                newOrder.world_id = getOptionalIntValue('attachArtifactSourceWorldId'); 
                if (isNaN(newOrder.fleet_id) || !newOrder.artifact_id) { valid = false; alert("Fleet ID and Artifact ID required."); break; }
                break;
            case 'DROP_ARTIFACT':
                newOrder.fleet_id = getIntValue('dropArtifactFleetId');
                newOrder.artifact_id = getSelectedValue('dropArtifactId'); 
                newOrder.world_id = getIntValue('dropArtifactTargetWorldId');
                if (isNaN(newOrder.fleet_id) || !newOrder.artifact_id || isNaN(newOrder.world_id)) { valid = false; alert("Fleet ID, Artifact ID, and Target World ID required."); break; }
                break;
            case 'AMBUSH':
                newOrder.fleet_id = getIntValue('ambushFleetId');
                newOrder.world_id = getIntValue('ambushWorldId');
                if (isNaN(newOrder.fleet_id) || isNaN(newOrder.world_id)) { valid = false; alert("Fleet ID and World ID required."); break; }
                break;
             case 'SET_ALLY':
                newOrder.target_player_id = getSelectedValue('setAllyTargetPlayerId'); 
                if (!newOrder.target_player_id) { valid = false; alert("Target Player User ID is required."); break; }
                break;
            case 'GIFT_WORLD':
                newOrder.world_id = getIntValue('giftWorldId');
                newOrder.recipient_player_id = getSelectedValue('giftWorldRecipientPlayerId'); 
                if (isNaN(newOrder.world_id) || !newOrder.recipient_player_id) { valid = false; alert("World ID and Recipient Player User ID required."); break; }
                break;
            case 'GIFT_FLEET':
                newOrder.fleet_id = getIntValue('giftFleetId');
                newOrder.recipient_player_id = getSelectedValue('giftFleetRecipientPlayerId'); 
                if (isNaN(newOrder.fleet_id) || !newOrder.recipient_player_id) { valid = false; alert("Fleet ID and Recipient Player User ID required."); break; }
                break;
            default:
                valid = false;
                alert('Unknown order type selected.');
                break;
        }

        if (valid) {
            queuedOrders.push(newOrder);
            renderQueuedOrders();
        }
    });

    turnForm.addEventListener('submit', function (event) {
        ordersJsonInput.value = JSON.stringify(queuedOrders);
    });

    // Initial setup
    updateOrderFormInputs();
    renderQueuedOrders();
    orderTypeSelect.addEventListener('change', updateOrderFormInputs);
    
    // Initial population of dropdowns that don't depend on other selections
    for (const fieldId in fieldsToReplaceConfig) {
        const fieldConfig = fieldsToReplaceConfig[fieldId];
        const selectElement = document.getElementById(fieldId);
        if (selectElement && selectElement.tagName === 'SELECT' && !fieldConfig.conditional) {
             populateSelect(selectElement, fieldConfig.data, fieldConfig.idField, fieldConfig.prefix, fieldConfig.idField);
        }
    }
    // Trigger initial population for conditional dropdowns based on their default selected type
    if (transferFromEntityTypeSelect && transferFromEntityTypeSelect.value) transferFromEntityTypeSelect.dispatchEvent(new Event('change'));
    if (transferToEntityTypeSelect && transferToEntityTypeSelect.value) transferToEntityTypeSelect.dispatchEvent(new Event('change'));
    if (buildTypeSelect && buildTypeSelect.value) buildTypeSelect.dispatchEvent(new Event('change'));

});
</script>
