import type { Platform, Payload } from '../types';
import { Info } from 'lucide-react';
import { useState } from 'react';

interface ControlPanelProps {
    platforms: Platform[];
    payloads: Payload[];
    selectedPlatformId: number;
    selectedPayloadId: number;
    month: number;
    duration: number;
    radius: number;
    margin: number;
    onChange: (field: string, value: number) => void;
    onSimulate: () => void;
    loading: boolean;
}

// Info Tooltip Component
function InfoTooltip({ text }: { text: string }) {
    const [show, setShow] = useState(false);
    return (
        <span className="relative inline-block ml-1">
            <Info
                size={14}
                className="text-gray-500 hover:text-accent-400 cursor-help inline"
                onMouseEnter={() => setShow(true)}
                onMouseLeave={() => setShow(false)}
                onClick={() => setShow(!show)}
            />
            {show && (
                <div className="absolute z-50 left-6 top-0 w-64 p-2 bg-space-900 border border-space-600 rounded-lg shadow-xl text-xs text-gray-300">
                    {text}
                </div>
            )}
        </span>
    );
}

export default function ControlPanel({
    platforms, payloads, selectedPlatformId, selectedPayloadId,
    month, duration, radius, margin, onChange, onSimulate, loading
}: ControlPanelProps) {
    const months = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];

    return (
        <div className="bg-space-800 p-6 rounded-xl border border-space-700 shadow-2xl flex flex-col gap-6">
            <h2 className="text-xl font-bold text-accent-500 font-mono flex items-center">
                Configurazione Missione
                <InfoTooltip text="Configura i parametri della missione: seleziona piattaforma e payload, scegli la durata e il margine desiderato." />
            </h2>

            <div className="space-y-4">
                {/* Platform */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1 flex items-center">
                        Piattaforma
                        <InfoTooltip text="Seleziona la piattaforma stratoferica da utilizzare. Mostra la capacità massima di payload in kg." />
                    </label>
                    <select
                        value={selectedPlatformId}
                        onChange={(e) => onChange('platform_id', Number(e.target.value))}
                        className="w-full bg-space-900 border border-space-700 rounded p-2 text-white focus:border-accent-500 outline-none"
                    >
                        {platforms.map(p => (
                            <option key={p.id} value={p.id}>{p.name} (Max {p.max_payload_mass}kg)</option>
                        ))}
                    </select>
                </div>

                {/* Payload */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1 flex items-center">
                        Payload
                        <InfoTooltip text="Seleziona il sensore da montare sulla piattaforma. Mostra il consumo energetico in Watt." />
                    </label>
                    <select
                        value={selectedPayloadId}
                        onChange={(e) => onChange('payload_id', Number(e.target.value))}
                        className="w-full bg-space-900 border border-space-700 rounded p-2 text-white focus:border-accent-500 outline-none"
                    >
                        {payloads.map(p => (
                            <option key={p.id} value={p.id}>{p.name} ({p.power_consumption}W)</option>
                        ))}
                    </select>
                </div>

                {/* Month */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1 flex items-center">
                        Mese (Stagionalità)
                        <InfoTooltip text="Il mese influenza le ore di luce (per ricarica solare) e la volatilità dei venti stratosferici. I mesi invernali hanno più vento e meno sole." />
                    </label>
                    <input
                        type="range" min="1" max="12" step="1"
                        value={month}
                        onChange={(e) => onChange('month', Number(e.target.value))}
                        className="w-full accent-accent-500"
                    />
                    <div className="text-xs text-right text-gray-500">{months[month - 1]} (Mese {month})</div>
                </div>

                {/* Duration */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1 flex items-center">
                        Durata (Giorni)
                        <InfoTooltip text="Durata totale della missione in giorni. Influenza i costi operativi e di trasmissione dati." />
                    </label>
                    <input
                        type="number" min="7" max="180"
                        value={duration}
                        onChange={(e) => onChange('duration', Number(e.target.value))}
                        className="w-full bg-space-900 border border-space-700 rounded p-2 text-white outline-none"
                    />
                </div>

                {/* Radius */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1 flex items-center">
                        Raggio Target (km)
                        <InfoTooltip text="Raggio dell'area di copertura. Un raggio più piccolo richiede station-keeping più preciso e può aumentare il fattore di overprovisioning." />
                    </label>
                    <input
                        type="range" min="10" max="200" step="10"
                        value={radius}
                        onChange={(e) => onChange('target_radius_km', Number(e.target.value))}
                        className="w-full accent-accent-500"
                    />
                    <div className="text-xs text-right text-gray-500">{radius} km</div>
                </div>

                {/* Margin */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1 flex items-center">
                        Margine Target (%)
                        <InfoTooltip text="Margine di profitto desiderato sul preventivo. Il prezzo finale = Costo / (1 - Margine%). Es: 30% margine su €10.000 costo = €14.286 prezzo." />
                    </label>
                    <input
                        type="range" min="10" max="50" step="5"
                        value={margin}
                        onChange={(e) => onChange('margin', Number(e.target.value))}
                        className="w-full accent-accent-500"
                    />
                    <div className="text-xs text-right text-gray-500">{margin}%</div>
                </div>
            </div>

            <button
                onClick={onSimulate}
                disabled={loading}
                className="w-full bg-accent-600 hover:bg-accent-500 text-white font-bold py-3 rounded transition shadow-lg disabled:opacity-50"
            >
                {loading ? "Simulazione in corso..." : "🚀 Esegui Simulazione"}
            </button>
        </div>
    );
}
