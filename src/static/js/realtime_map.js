/**
 * FleetVision - Lógica de Mapa em Tempo Real
 * Usa Leaflet.js + Django Channels (WebSockets)
 */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Inicializa o Mapa
    // Centraliza no Brasil inicialmente ou pega última posição conhecida
    const map = L.map('map-container').setView([-23.5505, -46.6333], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    const vehicleMarkers = {};

    // 2. Definição de Ícones
    const createIcon = (color) => {
        return L.divIcon({
            className: 'custom-vehicle-icon',
            html: `<div style="
                background-color: ${color};
                width: 14px;
                height: 14px;
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 0 4px rgba(0,0,0,0.5);
            "></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7],
            popupAnchor: [0, -10]
        });
    };

    const icons = {
        online: createIcon('#28a745'), // Verde
        offline: createIcon('#dc3545'), // Vermelho
        idle: createIcon('#ffc107')     // Amarelo
    };

    // 3. Conexão WebSocket
    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socketUrl = protocol + '//' + window.location.host + '/ws/fleet/live/';
        
        console.log(`📡 Conectando ao FleetVision Stream: ${socketUrl}`);
        const socket = new WebSocket(socketUrl);

        socket.onopen = function(e) {
            console.log("🟢 Conectado ao Rastreamento em Tempo Real");
        };

        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'vehicle_update') {
                updateVehicle(data.data);
            }
        };

        socket.onclose = function(e) {
            console.error("🔴 Desconectado. Tentando reconectar em 5s...");
            setTimeout(connect, 5000);
        };
        
        socket.onerror = function(err) {
            console.error("Erro no WebSocket:", err);
            socket.close();
        };
    }

    // 4. Atualiza Marcador no Mapa
    function updateVehicle(v) {
        const { id, lat, lng, name, speed, ignition, score } = v;

        // Define cor baseada no status
        let icon = icons.offline;
        let statusText = "Parado/Desligado";
        
        if (ignition) {
            if (speed > 0) {
                icon = icons.online;
                statusText = "Em Movimento";
            } else {
                icon = icons.idle;
                statusText = "Parado/Ligado";
            }
        }

        const popupContent = `
            <div class="p-2">
                <h6 class="fw-bold mb-1">${name}</h6>
                <div class="small text-muted mb-2">${statusText}</div>
                <table class="table table-sm table-borderless mb-0 small">
                    <tr><td>Velocidade:</td><td class="fw-bold text-end">${Math.round(speed)} km/h</td></tr>
                    <tr><td>Ignição:</td><td class="fw-bold text-end">${ignition ? 'ON' : 'OFF'}</td></tr>
                    ${score !== null ? `<tr><td>Score Hoje:</td><td class="fw-bold text-end">${score}</td></tr>` : ''}
                </table>
            </div>
        `;

        if (vehicleMarkers[id]) {
            // Atualiza existente
            const marker = vehicleMarkers[id];
            marker.setLatLng([lat, lng]);
            marker.setIcon(icon);
            marker.getPopup().setContent(popupContent);
        } else {
            // Cria novo
            const marker = L.marker([lat, lng], { icon: icon })
                .addTo(map)
                .bindPopup(popupContent);
            
            vehicleMarkers[id] = marker;
            
            // Opcional: Auto-fit se for o primeiro veículo
            if (Object.keys(vehicleMarkers).length === 1) {
                map.setView([lat, lng], 13);
            }
        }
    }

    // Iniciar
    connect();
});