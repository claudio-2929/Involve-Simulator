import type { SimulationResponse } from '../types';
import { AlertTriangle, CheckCircle, Wind, Battery, Users, Gauge, Info } from 'lucide-react';
import { useState } from 'react';

interface QuoteCardProps {
    result: SimulationResponse | null;
}

// Info Tooltip Component
function InfoTooltip({ text }: { text: string }) {
    const [show, setShow] = useState(false);
    return (
        <span className="relative inline-block ml-1">
            <Info
                size={12}
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

export default function QuoteCard({ result }: QuoteCardProps) {
    if (!result) {
        return (
            <div className="bg-space-800 p-6 rounded-xl border border-space-700 h-full flex items-center justify-center text-gray-500 font-mono">
                Esegui la simulazione per generare un preventivo
            </div>
        );
    }

    const { quote, warnings, is_feasible, power_analysis, flight_analysis } = result;

    return (
        <div className="bg-space-800 p-6 rounded-xl border border-space-700 shadow-xl flex flex-col gap-4 animate-in fade-in zoom-in duration-500">
            {/* Status Header */}
            <div className={`p-4 rounded-lg flex items-center gap-3 ${is_feasible ? 'bg-green-900/30 border border-green-700/50' : 'bg-red-900/30 border border-red-700/50'}`}>
                {is_feasible ? <CheckCircle className="text-green-500" /> : <AlertTriangle className="text-red-500" />}
                <div>
                    <h3 className={`font-bold ${is_feasible ? 'text-green-400' : 'text-red-400'}`}>
                        {is_feasible ? 'Missione Fattibile' : 'Vincoli Superati'}
                    </h3>
                    {warnings.map((w, i) => (
                        <p key={i} className="text-xs text-gray-300">{w}</p>
                    ))}
                </div>
            </div>

            {/* Physics Stats - Enhanced */}
            <div className="grid grid-cols-2 gap-3 text-xs">
                {/* Power / Duty Cycle */}
                <div className="bg-space-900 p-3 rounded border border-space-700">
                    <div className="flex items-center gap-2 mb-1 text-gray-400">
                        <Battery size={14} /> Potenza
                        <InfoTooltip text="Analisi energetica basata su: consumo payload, potenza notturna piattaforma, e durata della notte per la latitudine/mese selezionati." />
                    </div>
                    <div className={power_analysis.is_feasible ? 'text-green-400' : 'text-red-400'}>
                        {power_analysis.status}
                    </div>
                    <div className="flex items-center gap-1 mt-1 text-gray-500">
                        <Gauge size={12} /> Duty Cycle: <span className={power_analysis.duty_cycle_percent < 100 ? 'text-yellow-400' : 'text-green-400'}>{power_analysis.duty_cycle_percent}%</span>
                    </div>
                    <div className="text-gray-600 text-xs mt-1">
                        Notte: {power_analysis.night_hours}h | Margine: {power_analysis.margin_wh}Wh
                    </div>
                </div>

                {/* Wind / Drift */}
                <div className="bg-space-900 p-3 rounded border border-space-700">
                    <div className="flex items-center gap-2 mb-1 text-gray-400">
                        <Wind size={14} /> Deriva
                        <InfoTooltip text="Analisi dei venti stratosferici. Se la velocità media supera la capacità di correzione ACS, è necessario un overprovisioning della flotta." />
                    </div>
                    <div className={flight_analysis.drift_warning ? 'text-red-400' : flight_analysis.drift_risk === "High" ? 'text-orange-400' : 'text-blue-400'}>
                        {flight_analysis.drift_warning ? '⚠ Allarme Deriva' : `Rischio ${flight_analysis.drift_risk}`}
                    </div>
                    <div className="text-gray-500 mt-1">
                        Vento: {flight_analysis.mean_wind_speed_kmh} km/h
                    </div>
                    <div className="text-gray-600 text-xs">
                        ACS Max: {flight_analysis.acs_correction_speed_kmh} km/h
                    </div>
                </div>

                {/* Fleet Size */}
                <div className="bg-space-900 p-3 rounded border border-space-700 col-span-2">
                    <div className="flex items-center gap-2 mb-1 text-gray-400">
                        <Users size={14} /> Overprovisioning Flotta
                        <InfoTooltip text="Fattore di moltiplicazione della flotta per garantire copertura continua. Calcolato in base alla probabilità di station-keeping e alla volatilità dei venti." />
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-accent-400 text-lg font-bold">{flight_analysis.overprovisioning_factor}x</span>
                        <span className="text-gray-400">→</span>
                        <span className="text-white">{flight_analysis.fleet_size_recommended} piattaforma{flight_analysis.fleet_size_recommended > 1 ? 'e' : ''} raccomandat{flight_analysis.fleet_size_recommended > 1 ? 'e' : 'a'}</span>
                    </div>
                </div>
            </div>

            {/* Quote */}
            {is_feasible && (
                <div className="mt-2 border-t border-space-700 pt-4">
                    <div className="text-gray-400 text-sm mb-1 uppercase tracking-wider flex items-center">
                        Preventivo Missione
                        <InfoTooltip text="Preventivo calcolato: (CAPEX ammortizzato + Costi operativi) × Fattore Overprovisioning, più margine desiderato." />
                    </div>
                    <div className="text-4xl font-mono font-bold text-white mb-4">
                        €{quote.price_quoted.toLocaleString()}
                    </div>

                    <div className="space-y-2 text-sm text-gray-300">
                        <div className="flex justify-between">
                            <span className="flex items-center">
                                Piattaforma (Flotta x{quote.breakdown.overprovisioning_factor})
                                <InfoTooltip text="CAPEX piattaforma ammortizzato su N voli + costo lancio, moltiplicato per il fattore flotta." />
                            </span>
                            <span>€{quote.breakdown.platform_amortized.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="flex items-center">
                                Payload
                                <InfoTooltip text="CAPEX payload ammortizzato su 10 missioni." />
                            </span>
                            <span>€{quote.breakdown.payload_amortized.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="flex items-center">
                                Operazioni & Dati
                                <InfoTooltip text="Costi operativi giornalieri × durata + costi di downlink satellite (€5/GB)." />
                            </span>
                            <span>€{(quote.breakdown.ops_cost + quote.breakdown.data_cost).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between pt-2 border-t border-space-700 font-bold text-accent-500">
                            <span className="flex items-center">
                                Margine Netto ({quote.margin_percent}%)
                                <InfoTooltip text="Profitto = Prezzo - Costo Totale. Margine % = Profitto / Prezzo × 100." />
                            </span>
                            <span>€{quote.margin_absolute.toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
