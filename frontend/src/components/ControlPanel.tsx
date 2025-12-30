import type { Platform, Payload } from '../types';

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

export default function ControlPanel({
    platforms, payloads, selectedPlatformId, selectedPayloadId,
    month, duration, radius, margin, onChange, onSimulate, loading
}: ControlPanelProps) {
    return (
        <div className="bg-space-800 p-6 rounded-xl border border-space-700 shadow-2xl flex flex-col gap-6">
            <h2 className="text-xl font-bold text-accent-500 font-mono">Mission Configuration</h2>

            <div className="space-y-4">
                {/* Platform */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1">Platform</label>
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
                    <label className="block text-sm text-gray-400 mb-1">Payload</label>
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
                    <label className="block text-sm text-gray-400 mb-1">Month (Seasonality)</label>
                    <input
                        type="range" min="1" max="12" step="1"
                        value={month}
                        onChange={(e) => onChange('month', Number(e.target.value))}
                        className="w-full accent-accent-500"
                    />
                    <div className="text-xs text-right text-gray-500">Month: {month}</div>
                </div>

                {/* Duration */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1">Duration (Days)</label>
                    <input
                        type="number" min="7" max="180"
                        value={duration}
                        onChange={(e) => onChange('duration', Number(e.target.value))}
                        className="w-full bg-space-900 border border-space-700 rounded p-2 text-white outline-none"
                    />
                </div>

                {/* Radius */}
                <div>
                    <label className="block text-sm text-gray-400 mb-1">Target Radius (km)</label>
                    <input
                        type="range" min="10" max="200" step="10"
                        value={radius}
                        onChange={(e) => onChange('target_radius_km', Number(e.target.value))}
                        className="w-full accent-accent-500"
                    />
                    <div className="text-xs text-right text-gray-500">{radius} km</div>
                </div>
            </div>

            <button
                onClick={onSimulate}
                disabled={loading}
                className="w-full bg-accent-600 hover:bg-accent-500 text-white font-bold py-3 rounded transition shadow-lg disabled:opacity-50"
            >
                {loading ? "Simulating..." : "Run Simulation"}
            </button>
        </div>
    );
}
