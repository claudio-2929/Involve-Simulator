import type { SimulationResponse } from '../types';
import { AlertTriangle, CheckCircle, Wind, Battery, Users, Gauge } from 'lucide-react';

interface QuoteCardProps {
    result: SimulationResponse | null;
}

export default function QuoteCard({ result }: QuoteCardProps) {
    if (!result) {
        return (
            <div className="bg-space-800 p-6 rounded-xl border border-space-700 h-full flex items-center justify-center text-gray-500 font-mono">
                Run simulation to generate quote
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
                        {is_feasible ? 'Mission Viable' : 'Mission Constraints Exceeded'}
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
                        <Battery size={14} /> Power
                    </div>
                    <div className={power_analysis.is_feasible ? 'text-green-400' : 'text-red-400'}>
                        {power_analysis.status}
                    </div>
                    <div className="flex items-center gap-1 mt-1 text-gray-500">
                        <Gauge size={12} /> Duty Cycle: <span className={power_analysis.duty_cycle_percent < 100 ? 'text-yellow-400' : 'text-green-400'}>{power_analysis.duty_cycle_percent}%</span>
                    </div>
                </div>

                {/* Wind / Drift */}
                <div className="bg-space-900 p-3 rounded border border-space-700">
                    <div className="flex items-center gap-2 mb-1 text-gray-400">
                        <Wind size={14} /> Drift Risk
                    </div>
                    <div className={flight_analysis.drift_warning ? 'text-red-400' : flight_analysis.drift_risk === "High" ? 'text-orange-400' : 'text-blue-400'}>
                        {flight_analysis.drift_warning ? '⚠ Drift Warning' : `${flight_analysis.drift_risk} Risk`}
                    </div>
                    <div className="text-gray-500 mt-1">
                        Wind: {flight_analysis.mean_wind_speed_kmh} km/h | ACS: {flight_analysis.acs_correction_speed_kmh} km/h
                    </div>
                </div>

                {/* Fleet Size */}
                <div className="bg-space-900 p-3 rounded border border-space-700 col-span-2">
                    <div className="flex items-center gap-2 mb-1 text-gray-400">
                        <Users size={14} /> Fleet Overprovisioning
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-accent-400 text-lg font-bold">{flight_analysis.overprovisioning_factor}x</span>
                        <span className="text-gray-400">→</span>
                        <span className="text-white">{flight_analysis.fleet_size_recommended} platform{flight_analysis.fleet_size_recommended > 1 ? 's' : ''} recommended</span>
                    </div>
                </div>
            </div>

            {/* Quote */}
            {is_feasible && (
                <div className="mt-2 border-t border-space-700 pt-4">
                    <div className="text-gray-400 text-sm mb-1 uppercase tracking-wider">Total Mission Cost</div>
                    <div className="text-4xl font-mono font-bold text-white mb-4">
                        €{quote.price_quoted.toLocaleString()}
                    </div>

                    <div className="space-y-2 text-sm text-gray-300">
                        <div className="flex justify-between">
                            <span>Platform (Fleet x{quote.breakdown.overprovisioning_factor})</span>
                            <span>€{quote.breakdown.platform_amortized.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Payload</span>
                            <span>€{quote.breakdown.payload_amortized.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Operations & Data</span>
                            <span>€{(quote.breakdown.ops_cost + quote.breakdown.data_cost).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between pt-2 border-t border-space-700 font-bold text-accent-500">
                            <span>Net Margin ({quote.margin_percent}%)</span>
                            <span>€{quote.margin_absolute.toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
