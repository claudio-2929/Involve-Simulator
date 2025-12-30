import { useState, useEffect } from 'react';
import type { Platform, Payload } from '../types';
import axios from 'axios';
import { Info, HelpCircle, X } from 'lucide-react';

interface AssetManagerProps {
    onClose: () => void;
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

// Labeled Input Component
function LabeledInput({
    label,
    unit,
    tooltip,
    value,
    onChange,
    type = "number",
    step,
    required
}: {
    label: string;
    unit?: string;
    tooltip?: string;
    value: string | number;
    onChange: (value: string) => void;
    type?: string;
    step?: string;
    required?: boolean;
}) {
    return (
        <div className="space-y-1">
            <label className="text-xs text-gray-400 flex items-center">
                {label}
                {unit && <span className="text-accent-400 ml-1">({unit})</span>}
                {tooltip && <InfoTooltip text={tooltip} />}
            </label>
            <input
                type={type}
                step={step}
                className="w-full p-2 bg-space-700 rounded border border-space-600 focus:border-accent-500 outline-none"
                value={value}
                onChange={e => onChange(e.target.value)}
                required={required}
            />
        </div>
    );
}

export default function AssetManager({ onClose }: AssetManagerProps) {
    const [activeTab, setActiveTab] = useState<'platforms' | 'payloads'>('platforms');
    const [platforms, setPlatforms] = useState<Platform[]>([]);
    const [payloads, setPayloads] = useState<Payload[]>([]);
    const [editingPlatform, setEditingPlatform] = useState<Platform | null>(null);
    const [editingPayload, setEditingPayload] = useState<Payload | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const [showHelp, setShowHelp] = useState(false);

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
                    <div className="flex items-center gap-2">
                        <h2 className="text-xl font-bold text-accent-400">Asset Manager</h2>
                        <button
                            onClick={() => setShowHelp(true)}
                            className="p-1 hover:bg-space-700 rounded"
                            title="Come usare l'Asset Manager"
                        >
                            <HelpCircle size={18} className="text-gray-400 hover:text-accent-400" />
                        </button>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-space-700">
                    <button
                        className={`flex-1 py-3 text-center font-medium transition flex items-center justify-center gap-2 ${activeTab === 'platforms' ? 'bg-space-700 text-accent-400' : 'text-gray-400 hover:text-white'}`}
                        onClick={() => setActiveTab('platforms')}
                    >
                        Platforms ({platforms.length})
                        <InfoTooltip text="Piattaforme stratosferiche (palloni o pseudo-satelliti) che trasportano i sensori. Ogni piattaforma ha specifiche di potenza, capacità di carico e costi operativi." />
                    </button>
                    <button
                        className={`flex-1 py-3 text-center font-medium transition flex items-center justify-center gap-2 ${activeTab === 'payloads' ? 'bg-space-700 text-accent-400' : 'text-gray-400 hover:text-white'}`}
                        onClick={() => setActiveTab('payloads')}
                    >
                        Payloads ({payloads.length})
                        <InfoTooltip text="Sensori e strumenti montati sulla piattaforma (radar SAR, camere ottiche, iperspettrali). Ogni payload ha peso, consumo energetico e costi specifici." />
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
                                + Aggiungi Nuova Piattaforma
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
                                        <button onClick={() => setEditingPlatform(p)} className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-sm">Modifica</button>
                                        <button onClick={() => deletePlatform(p.id)} className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm">Elimina</button>
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
                                + Aggiungi Nuovo Payload
                            </button>
                            {payloads.map(p => (
                                <div key={p.id} className="bg-space-700 rounded-lg p-4 flex justify-between items-start">
                                    <div>
                                        <h3 className="font-semibold text-white">{p.name}</h3>
                                        <p className="text-sm text-accent-400">{p.market}</p>
                                        <div className="text-xs text-gray-500 mt-1">
                                            CAPEX: €{p.capex.toLocaleString()} | Massa: {p.mass}kg | Potenza: {p.power_consumption}W | GSD: {p.resolution_gsd}m
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => setEditingPayload(p)} className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-sm">Modifica</button>
                                        <button onClick={() => deletePayload(p.id)} className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm">Elimina</button>
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

                {/* Help Modal */}
                {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
            </div>
        </div>
    );
}

function HelpModal({ onClose }: { onClose: () => void }) {
    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[70] p-4">
            <div className="bg-space-800 rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-auto border border-space-600">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold text-accent-400">📘 Come Usare l'Asset Manager</h3>
                    <button onClick={onClose} className="p-1 hover:bg-space-700 rounded">
                        <X size={20} className="text-gray-400" />
                    </button>
                </div>

                <div className="space-y-4 text-sm text-gray-300">
                    <section>
                        <h4 className="font-bold text-white mb-2">🎈 Piattaforme</h4>
                        <p>Le piattaforme sono veicoli stratosferici (palloni o pseudo-satelliti) che volano tra 18-25km di quota. Ogni piattaforma ha:</p>
                        <ul className="list-disc list-inside mt-2 space-y-1 text-gray-400">
                            <li><strong>CAPEX</strong>: Costo di acquisto/costruzione della piattaforma</li>
                            <li><strong>Costo Lancio</strong>: Costo operativo per ogni lancio</li>
                            <li><strong>Consumabili</strong>: Costi ricorrenti (elio, zavorra, manutenzione)</li>
                            <li><strong>Potenza Giorno/Notte</strong>: Watt disponibili per il payload durante il giorno (pannelli solari) e notte (batteria)</li>
                            <li><strong>Capacità Batteria</strong>: Energia totale immagazzinata in Watt-ora</li>
                        </ul>
                    </section>

                    <section>
                        <h4 className="font-bold text-white mb-2">📡 Payloads (Sensori)</h4>
                        <p>I payload sono gli strumenti montati sulla piattaforma per raccogliere dati:</p>
                        <ul className="list-disc list-inside mt-2 space-y-1 text-gray-400">
                            <li><strong>Massa</strong>: Peso del sensore in kg (deve essere ≤ capacità piattaforma)</li>
                            <li><strong>Consumo Potenza</strong>: Watt richiesti dal sensore (deve essere ≤ potenza notturna piattaforma)</li>
                            <li><strong>GSD</strong>: Ground Sample Distance - risoluzione in metri/pixel</li>
                            <li><strong>FOV</strong>: Field of View - ampiezza del campo visivo in gradi</li>
                            <li><strong>Data Rate</strong>: GB di dati generati al giorno</li>
                        </ul>
                    </section>

                    <section>
                        <h4 className="font-bold text-white mb-2">💡 Consigli</h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-400">
                            <li>Passa il mouse sull'icona <Info size={12} className="inline text-accent-400" /> per vedere spiegazioni dettagliate</li>
                            <li>Verifica sempre che il consumo del payload sia compatibile con la potenza notturna della piattaforma</li>
                            <li>Un Duty Cycle {"<"} 100% indica operatività ridotta di notte</li>
                        </ul>
                    </section>
                </div>

                <button
                    onClick={onClose}
                    className="mt-6 w-full py-2 bg-accent-600 hover:bg-accent-500 rounded-lg font-medium transition"
                >
                    Ho Capito
                </button>
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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
            <form onSubmit={handleSubmit} className="bg-space-800 rounded-xl p-6 w-full max-w-lg max-h-[85vh] overflow-auto border border-space-600">
                <h3 className="text-lg font-bold mb-4 text-accent-400">
                    {isNew ? '🆕 Nuova Piattaforma' : '✏️ Modifica Piattaforma'}
                </h3>

                <div className="space-y-4">
                    {/* Basic Info */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Informazioni Base
                            <InfoTooltip text="Nome e tipologia della piattaforma. Il tipo influenza le performance di station-keeping." />
                        </h4>
                        <LabeledInput
                            label="Nome Piattaforma"
                            value={form.name}
                            onChange={v => setForm({ ...form, name: v })}
                            type="text"
                            required
                            tooltip="Nome identificativo univoco per questa piattaforma"
                        />
                        <LabeledInput
                            label="Tipo"
                            value={form.platform_type}
                            onChange={v => setForm({ ...form, platform_type: v })}
                            type="text"
                            tooltip="Es: Super-Pressure Variable Volume, Zero-Pressure with Ballast Control"
                        />
                    </div>

                    {/* Costs */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Costi
                            <InfoTooltip text="Costi in Euro. CAPEX viene ammortizzato su più voli, i costi operativi sono per singolo lancio." />
                        </h4>
                        <div className="grid grid-cols-3 gap-3">
                            <LabeledInput
                                label="CAPEX"
                                unit="€"
                                value={form.capex}
                                onChange={v => setForm({ ...form, capex: +v })}
                                tooltip="Capital Expenditure: costo di acquisto/costruzione, ammortizzato su N voli"
                            />
                            <LabeledInput
                                label="Costo Lancio"
                                unit="€"
                                value={form.launch_cost}
                                onChange={v => setForm({ ...form, launch_cost: +v })}
                                tooltip="Costo operativo per ogni lancio (team, logistica, permessi)"
                            />
                            <LabeledInput
                                label="Consumabili"
                                unit="€"
                                value={form.consumables_cost}
                                onChange={v => setForm({ ...form, consumables_cost: +v })}
                                tooltip="Costi ricorrenti: elio, zavorra, manutenzione per missione"
                            />
                        </div>
                    </div>

                    {/* Physical Specs */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Specifiche Fisiche
                            <InfoTooltip text="Capacità di carico e durata massima di volo della piattaforma." />
                        </h4>
                        <div className="grid grid-cols-2 gap-3">
                            <LabeledInput
                                label="Max Payload"
                                unit="kg"
                                value={form.max_payload_mass}
                                onChange={v => setForm({ ...form, max_payload_mass: +v })}
                                tooltip="Massa massima del payload che può essere trasportato"
                            />
                            <LabeledInput
                                label="Durata Max"
                                unit="giorni"
                                value={form.max_duration_days}
                                onChange={v => setForm({ ...form, max_duration_days: +v })}
                                tooltip="Durata massima della missione in condizioni ottimali"
                            />
                        </div>
                    </div>

                    {/* Power */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Sistema Energetico
                            <InfoTooltip text="Potenza disponibile per il payload. Di giorno i pannelli solari forniscono più potenza, di notte si usa la batteria." />
                        </h4>
                        <div className="grid grid-cols-3 gap-3">
                            <LabeledInput
                                label="Potenza Giorno"
                                unit="W"
                                value={form.day_power}
                                onChange={v => setForm({ ...form, day_power: +v })}
                                tooltip="Watt disponibili per il payload durante le ore di sole (pannelli solari + carica batteria)"
                            />
                            <LabeledInput
                                label="Potenza Notte"
                                unit="W"
                                value={form.night_power}
                                onChange={v => setForm({ ...form, night_power: +v })}
                                tooltip="Watt disponibili per il payload durante la notte (solo batteria). CRITICO: deve essere ≥ consumo payload!"
                            />
                            <LabeledInput
                                label="Batteria"
                                unit="Wh"
                                value={form.battery_capacity}
                                onChange={v => setForm({ ...form, battery_capacity: +v })}
                                tooltip="Capacità totale della batteria in Watt-ora. Deve coprire consumo × ore di notte"
                            />
                        </div>
                    </div>

                    {/* Amortization */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Ammortamento
                            <InfoTooltip text="Su quanti voli viene distribuito il costo CAPEX della piattaforma." />
                        </h4>
                        <LabeledInput
                            label="Voli per Ammortamento"
                            unit="voli"
                            value={form.amortization_flights}
                            onChange={v => setForm({ ...form, amortization_flights: +v })}
                            tooltip="Numero di voli su cui ammortizzare il CAPEX. Es: 5 = CAPEX/5 per missione"
                        />
                    </div>
                </div>

                <div className="flex gap-2 mt-6">
                    <button type="submit" className="flex-1 py-2 bg-accent-600 hover:bg-accent-500 rounded font-medium">Salva</button>
                    <button type="button" onClick={onCancel} className="flex-1 py-2 bg-gray-600 hover:bg-gray-500 rounded font-medium">Annulla</button>
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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
            <form onSubmit={handleSubmit} className="bg-space-800 rounded-xl p-6 w-full max-w-lg max-h-[85vh] overflow-auto border border-space-600">
                <h3 className="text-lg font-bold mb-4 text-accent-400">
                    {isNew ? '🆕 Nuovo Payload' : '✏️ Modifica Payload'}
                </h3>

                <div className="space-y-4">
                    {/* Basic Info */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Informazioni Base
                            <InfoTooltip text="Nome del sensore e mercato target per questa tipologia di dati." />
                        </h4>
                        <LabeledInput
                            label="Nome Payload"
                            value={form.name}
                            onChange={v => setForm({ ...form, name: v })}
                            type="text"
                            required
                            tooltip="Nome identificativo del sensore (es: SAR X-Band, PhaseOne iXM-100)"
                        />
                        <LabeledInput
                            label="Mercato Target"
                            value={form.market}
                            onChange={v => setForm({ ...form, market: v })}
                            type="text"
                            tooltip="Settore applicativo: Maritime, Agriculture, Urban Mapping, etc."
                        />
                    </div>

                    {/* Cost */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Costo
                            <InfoTooltip text="Il CAPEX del payload viene ammortizzato su 10 missioni nel calcolo del preventivo." />
                        </h4>
                        <LabeledInput
                            label="CAPEX Payload"
                            unit="€"
                            value={form.capex}
                            onChange={v => setForm({ ...form, capex: +v })}
                            tooltip="Costo di acquisto del sensore. Ammortizzato su 10 missioni nel preventivo"
                        />
                    </div>

                    {/* Physical Specs */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Specifiche Fisiche
                            <InfoTooltip text="Peso e consumo energetico. Devono essere compatibili con la piattaforma selezionata." />
                        </h4>
                        <div className="grid grid-cols-2 gap-3">
                            <LabeledInput
                                label="Massa"
                                unit="kg"
                                value={form.mass}
                                onChange={v => setForm({ ...form, mass: +v })}
                                tooltip="Peso del sensore. Deve essere ≤ max_payload_mass della piattaforma"
                            />
                            <LabeledInput
                                label="Consumo Potenza"
                                unit="W"
                                value={form.power_consumption}
                                onChange={v => setForm({ ...form, power_consumption: +v })}
                                tooltip="Potenza richiesta dal sensore. Se > night_power della piattaforma, il Duty Cycle viene ridotto"
                            />
                        </div>
                    </div>

                    {/* Imaging Specs */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Parametri Imaging
                            <InfoTooltip text="Caratteristiche ottiche/radar del sensore che influenzano la qualità dei dati." />
                        </h4>
                        <div className="grid grid-cols-2 gap-3">
                            <LabeledInput
                                label="GSD (Risoluzione)"
                                unit="m"
                                value={form.resolution_gsd}
                                onChange={v => setForm({ ...form, resolution_gsd: +v })}
                                step="0.01"
                                tooltip="Ground Sample Distance: dimensione in metri di ogni pixel. Più basso = più dettagliato"
                            />
                            <LabeledInput
                                label="FOV"
                                unit="°"
                                value={form.fov}
                                onChange={v => setForm({ ...form, fov: +v })}
                                tooltip="Field of View: ampiezza del campo visivo in gradi. Maggiore = più copertura"
                            />
                        </div>
                    </div>

                    {/* Data */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-400 border-b border-space-700 pb-1 flex items-center">
                            Dati
                            <InfoTooltip text="Volume di dati generato dal sensore. Influenza i costi di trasmissione satellite." />
                        </h4>
                        <LabeledInput
                            label="Data Rate Giornaliero"
                            unit="GB/giorno"
                            value={form.daily_data_rate_gb}
                            onChange={v => setForm({ ...form, daily_data_rate_gb: +v })}
                            tooltip="GB di dati prodotti al giorno. Usato per calcolare i costi di downlink satellite"
                        />
                    </div>
                </div>

                <div className="flex gap-2 mt-6">
                    <button type="submit" className="flex-1 py-2 bg-accent-600 hover:bg-accent-500 rounded font-medium">Salva</button>
                    <button type="button" onClick={onCancel} className="flex-1 py-2 bg-gray-600 hover:bg-gray-500 rounded font-medium">Annulla</button>
                </div>
            </form>
        </div>
    );
}
