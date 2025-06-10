// Initialize Leaflet map
const map = L.map('map').setView([-25, 135], 4);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Load GeoJSON of Australia states
fetch('/static/australia-cities.geojson')
    .then(res => res.json())
    .then(data => {
        L.geoJSON(data, {
            pointToLayer: function(feature, latlng) {
                return L.marker(latlng);
            },
            onEachFeature: (feature, layer) => {
                const cityName = feature.properties.name;
                layer.bindTooltip(cityName);
                layer.on('click', () => {
                    sendMessage(`Tell me about ${cityName}, ${feature.properties.state}.`);
                });
            }
        }).addTo(map);
    });


// Chat UI helpers
const chatWindow = document.getElementById('chat-window');
const input = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.textContent = text;
    chatWindow.append(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}


async function sendMessage(msg) {
    addMessage(msg, 'user');
    input.value = '';
    const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    addMessage(data.reply, 'bot');
}

// Handle manual sends
sendBtn.addEventListener('click', () => {
    const text = input.value.trim();
    if (text) sendMessage(text);
});
input.addEventListener('keypress', e => {
    if (e.key === 'Enter' && input.value.trim()) sendMessage(input.value.trim());
});
