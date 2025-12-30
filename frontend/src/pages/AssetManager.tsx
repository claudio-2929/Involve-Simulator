import { useState, useEffect } from 'react';
import type { Platform, Payload } from '../types';
import axios from 'axios';

interface AssetManagerProps {
    onClose: () => void;
}

export default function AssetManager({ onClose }: AssetManagerProps) {
    const [activeTab, setActiveTab] = useState<'platforms' | 'payloads'>('platforms');
    const [platforms, setPlatforms] = useState<Platform[]>([]);
    const [payloads, setPayloads] = useState<Payload[]>([]);
    const [editingPlatform, setEditingPlatform] = useState<Platform | null>(null);
    const [editingPayload, setEditingPayload] = useState<Payload | null>(null);
    const [isCreating, setIsCreating] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        const [platformsRes, payloadsRes] = await Promise.all([
            axios.get('/api/platforms/'),
            axios.get('/api/payloads/')
        ]);
        setPlatforms(platformsRes.data);
        setPayloads(payloadsRes.data);
    };

    const deletePlatform = async (id: number) => {
        if (!confirm('Delete this platform?')) return;
        await axios.delete(`/api/platforms/${id}`);
        fetchData();
    };

    const deletePayload = async (id: number) => {
        if (!confirm('Delete this payload?')) return;
        await axios.delete(`/api/payloads/${id}`);
        fetchData();
    };

    const savePlatform = async (data: Partial<Platform>) => {
        if (editingPlatform?.id) {
            await axios.put(`/api/platforms/${editingPlatform.id}`, data);
        } else {
            await axios.post('/api/platforms/', data);
        }
        setEditingPlatform(null);
        setIsCreating(false);
        fetchData();
    };

    const savePayload = async (data: Partial<Payload>) => {
        if (editingPayload?.id) {
            await axios.put(`/api/payloads/${editingPayload.id}`, data);
        } else {
            await axios.post('/api/payloads/', data);
        }
        setEditingPayload(null);
        setIsCreating(false);
        fetchData();
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-space-800 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-space-700 flex justify-between items-center">
                    <h2 className="text-xl font-bold text-accent-400">Asset Manager</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-space-700">
                    <button
                        className={`flex-1 py-3 text-center font-medium transition ${activeTab === 'platforms' ? 'bg-space-700 text-accent-400' : 'text-gray-400 hover:text-white'}`}
                        onClick={() => setActiveTab('platforms')}
                    >
                        Platforms ({platforms.length})
                    </button>
                    <button
                        className={`flex-1 py-3 text-center font-medium transition ${activeTab === 'payloads' ? 'bg-space-700 text-accent-400' : 'text-gray-400 hover:text-white'}`}
                        onClick={() => setActiveTab('payloads')}
                    >
                        Payloads ({payloads.length})
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-4">
                    {activeTab === 'platforms' && (
                        <div className="space-y-3">
                            <button
                                className="w-full py-2 bg-accent-600 hover:bg-accent-500 rounded-lg font-medium transition"
                                onClick={() => { setIsCreating(true); setEditingPlatform({} as Platform); }}
                            >
                                + Add New Platform
                            </button>
                            {platforms.map(p => (
                                <div key={p.id} className="bg-space-700 rounded-lg p-4 flex justify-between items-start">
                                    <div>
                                        <h3 className="font-semibold text-white">{p.name}</h3>
                                        <p className="text-sm text-gray-400">{p.platform_type}</p>
                                        <div className="text-xs text-gray-500 mt-1">
                                            CAPEX: €{p.capex.toLocaleString()} | Payload: {p.max_payload_mass}kg | Power: {p.day_power}W/{p.night_power}W
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => setEditingPlatform(p)} className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-sm">Edit</button>
                                        <button onClick={() => deletePlatform(p.id)} className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm">Delete</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {activeTab === 'payloads' && (
                        <div className="space-y-3">
                            <button
                                className="w-full py-2 bg-accent-600 hover:bg-accent-500 rounded-lg font-medium transition"
                                onClick={() => { setIsCreating(true); setEditingPayload({} as Payload); }}
                            >
                                + Add New Payload
                            </button>
                            {payloads.map(p => (
                                <div key={p.id} className="bg-space-700 rounded-lg p-4 flex justify-between items-start">
                                    <div>
                                        <h3 className="font-semibold text-white">{p.name}</h3>
                                        <p className="text-sm text-accent-400">{p.market}</p>
                                        <div className="text-xs text-gray-500 mt-1">
                                            CAPEX: €{p.capex.toLocaleString()} | Mass: {p.mass}kg | Power: {p.power_consumption}W | GSD: {p.resolution_gsd}m
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => setEditingPayload(p)} className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-sm">Edit</button>
                                        <button onClick={() => deletePayload(p.id)} className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm">Delete</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Edit Modal for Platform */}
                {editingPlatform && (
                    <PlatformForm
                        platform={editingPlatform}
                        onSave={savePlatform}
                        onCancel={() => { setEditingPlatform(null); setIsCreating(false); }}
                        isNew={isCreating}
                    />
                )}

                {/* Edit Modal for Payload */}
                {editingPayload && (
                    <PayloadForm
                        payload={editingPayload}
                        onSave={savePayload}
                        onCancel={() => { setEditingPayload(null); setIsCreating(false); }}
                        isNew={isCreating}
                    />
                )}
            </div>
        </div>
    );
}

function PlatformForm({ platform, onSave, onCancel, isNew }: { platform: Platform; onSave: (data: Partial<Platform>) => void; onCancel: () => void; isNew: boolean }) {
    const [form, setForm] = useState({
        name: platform.name || '',
        platform_type: platform.platform_type || 'Super-Pressure',
        capex: platform.capex || 30000,
        launch_cost: platform.launch_cost || 2000,
        consumables_cost: platform.consumables_cost || 1000,
        max_payload_mass: platform.max_payload_mass || 15,
        min_altitude: platform.min_altitude || 18,
        max_altitude: platform.max_altitude || 23,
        max_duration_days: platform.max_duration_days || 60,
        amortization_flights: platform.amortization_flights || 5,
        day_power: platform.day_power || 100,
        night_power: platform.night_power || 40,
        battery_capacity: platform.battery_capacity || 1500,
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(form);
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-60">
            <form onSubmit={handleSubmit} className="bg-space-800 rounded-xl p-6 w-full max-w-md max-h-[80vh] overflow-auto">
                <h3 className="text-lg font-bold mb-4">{isNew ? 'New Platform' : 'Edit Platform'}</h3>
                <div className="space-y-3">
                    <input className="w-full p-2 bg-space-700 rounded" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
                    <input className="w-full p-2 bg-space-700 rounded" placeholder="Type" value={form.platform_type} onChange={e => setForm({ ...form, platform_type: e.target.value })} />
                    <div className="grid grid-cols-2 gap-2">
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="CAPEX (€)" value={form.capex} onChange={e => setForm({ ...form, capex: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Launch Cost (€)" value={form.launch_cost} onChange={e => setForm({ ...form, launch_cost: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Consumables (€)" value={form.consumables_cost} onChange={e => setForm({ ...form, consumables_cost: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Max Payload (kg)" value={form.max_payload_mass} onChange={e => setForm({ ...form, max_payload_mass: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Day Power (W)" value={form.day_power} onChange={e => setForm({ ...form, day_power: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Night Power (W)" value={form.night_power} onChange={e => setForm({ ...form, night_power: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Battery (Wh)" value={form.battery_capacity} onChange={e => setForm({ ...form, battery_capacity: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Max Duration (days)" value={form.max_duration_days} onChange={e => setForm({ ...form, max_duration_days: +e.target.value })} />
                    </div>
                </div>
                <div className="flex gap-2 mt-4">
                    <button type="submit" className="flex-1 py-2 bg-accent-600 hover:bg-accent-500 rounded font-medium">Save</button>
                    <button type="button" onClick={onCancel} className="flex-1 py-2 bg-gray-600 hover:bg-gray-500 rounded font-medium">Cancel</button>
                </div>
            </form>
        </div>
    );
}

function PayloadForm({ payload, onSave, onCancel, isNew }: { payload: Payload; onSave: (data: Partial<Payload>) => void; onCancel: () => void; isNew: boolean }) {
    const [form, setForm] = useState({
        name: payload.name || '',
        capex: payload.capex || 10000,
        mass: payload.mass || 3,
        power_consumption: payload.power_consumption || 30,
        resolution_gsd: payload.resolution_gsd || 1,
        fov: payload.fov || 20,
        daily_data_rate_gb: payload.daily_data_rate_gb || 50,
        market: payload.market || 'General',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(form);
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-60">
            <form onSubmit={handleSubmit} className="bg-space-800 rounded-xl p-6 w-full max-w-md">
                <h3 className="text-lg font-bold mb-4">{isNew ? 'New Payload' : 'Edit Payload'}</h3>
                <div className="space-y-3">
                    <input className="w-full p-2 bg-space-700 rounded" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
                    <input className="w-full p-2 bg-space-700 rounded" placeholder="Market" value={form.market} onChange={e => setForm({ ...form, market: e.target.value })} />
                    <div className="grid grid-cols-2 gap-2">
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="CAPEX (€)" value={form.capex} onChange={e => setForm({ ...form, capex: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Mass (kg)" value={form.mass} onChange={e => setForm({ ...form, mass: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Power (W)" value={form.power_consumption} onChange={e => setForm({ ...form, power_consumption: +e.target.value })} />
                        <input type="number" step="0.01" className="p-2 bg-space-700 rounded" placeholder="GSD (m)" value={form.resolution_gsd} onChange={e => setForm({ ...form, resolution_gsd: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="FOV (°)" value={form.fov} onChange={e => setForm({ ...form, fov: +e.target.value })} />
                        <input type="number" className="p-2 bg-space-700 rounded" placeholder="Data Rate (GB/day)" value={form.daily_data_rate_gb} onChange={e => setForm({ ...form, daily_data_rate_gb: +e.target.value })} />
                    </div>
                </div>
                <div className="flex gap-2 mt-4">
                    <button type="submit" className="flex-1 py-2 bg-accent-600 hover:bg-accent-500 rounded font-medium">Save</button>
                    <button type="button" onClick={onCancel} className="flex-1 py-2 bg-gray-600 hover:bg-gray-500 rounded font-medium">Cancel</button>
                </div>
            </form>
        </div>
    );
}
