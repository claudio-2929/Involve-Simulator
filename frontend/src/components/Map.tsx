import { MapContainer, TileLayer, Circle, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { LatLngTuple } from 'leaflet';
import { useEffect } from 'react';

interface MapProps {
    center: LatLngTuple;
    radiusKm: number;
    onLocationSelect: (lat: number, lon: number) => void;
}

function LocationMarker({ onSelect }: { onSelect: (lat: number, lon: number) => void }) {
    useMapEvents({
        click(e) {
            onSelect(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
}

function MapUpdater({ center }: { center: LatLngTuple }) {
    const map = useMapEvents({});
    useEffect(() => {
        map.setView(center);
    }, [center, map]);
    return null;
}

export default function SimulationMap({ center, radiusKm, onLocationSelect }: MapProps) {
    return (
        <MapContainer center={center} zoom={4} className="w-full h-full z-0">
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            <LocationMarker onSelect={onLocationSelect} />
            <MapUpdater center={center} />

            <Circle
                center={center}
                pathOptions={{ color: '#00D1FF', fillColor: '#00D1FF', fillOpacity: 0.2 }}
                radius={radiusKm * 1000}
            />
            <Marker position={center}>
                <Popup>Mission Target Center</Popup>
            </Marker>
        </MapContainer>
    );
}
