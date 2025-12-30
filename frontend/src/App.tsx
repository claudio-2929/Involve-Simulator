import { useState, useEffect } from 'react';
import axios from 'axios';
import type { Platform, Payload, SimulationResponse } from './types';
import SimulationMap from './components/Map';
import ControlPanel from './components/ControlPanel';
import QuoteCard from './components/QuoteCard';
import AssetManager from './pages/AssetManager';
import type { LatLngTuple } from 'leaflet';
import { Globe, Activity, Settings } from 'lucide-react';

function App() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [payloads, setPayloads] = useState<Payload[]>([]);
  const [showAssetManager, setShowAssetManager] = useState(false);

  // State for Controls
  const [selectedPlatformId, setSelectedPlatformId] = useState<number>(0);
  const [selectedPayloadId, setSelectedPayloadId] = useState<number>(0);
  const [month, setMonth] = useState<number>(6);
  const [duration, setDuration] = useState<number>(30);
  const [radius, setRadius] = useState<number>(50);
  const [margin, setMargin] = useState<number>(30);

  // Map State
  const [center, setCenter] = useState<LatLngTuple>([45.0, 10.0]); // Default Italy

  // Results
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);

  // Load Init Data
  const loadAssets = async () => {
    try {
      const pRes = await axios.get('/api/platforms/');
      const plRes = await axios.get('/api/payloads/');
      setPlatforms(pRes.data);
      setPayloads(plRes.data);
      if (pRes.data.length > 0 && selectedPlatformId === 0) setSelectedPlatformId(pRes.data[0].id);
      if (plRes.data.length > 0 && selectedPayloadId === 0) setSelectedPayloadId(plRes.data[0].id);
    } catch (e) {
      console.error("Failed to load assets", e);
    }
  };

  useEffect(() => {
    loadAssets();
  }, []);

  const handleChange = (field: string, value: number) => {
    if (field === 'platform_id') setSelectedPlatformId(value);
    if (field === 'payload_id') setSelectedPayloadId(value);
    if (field === 'month') setMonth(value);
    if (field === 'duration') setDuration(value);
    if (field === 'target_radius_km') setRadius(value);
    if (field === 'margin') setMargin(value);
  };

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const payload = {
        platform_id: selectedPlatformId,
        payload_id: selectedPayloadId,
        lat: center[0],
        lon: center[1],
        month: month,
        duration_days: duration,
        target_radius_km: radius,
        margin_percent: margin / 100.0
      };

      const res = await axios.post('/api/simulate/', payload);
      setResult(res.data);
    } catch (e) {
      console.error(e);
      alert("Simulation Failed");
    } finally {
      setLoading(false);
    }
  };

  const handleAssetManagerClose = () => {
    setShowAssetManager(false);
    loadAssets(); // Refresh data after asset changes
  };

  return (
    <div className="flex h-screen w-screen bg-space-900 overflow-hidden relative">
      {/* Left: Map */}
      <div className="w-2/3 h-full relative z-0">
        <SimulationMap
          center={center}
          radiusKm={radius}
          onLocationSelect={(lat, lon) => setCenter([lat, lon])}
        />
        {/* Overlay Title */}
        <div className="absolute top-6 left-6 z-[1000] pointer-events-none">
          <div className="bg-space-900/80 backdrop-blur border border-space-700 p-4 rounded-xl flex items-center gap-3">
            <Globe className="text-accent-500" size={32} />
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Involve Stratospheric</h1>
              <p className="text-xs text-gray-400 font-mono">MISSION SIMULATOR & QUOTER v2.0</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Controls */}
      <div className="w-1/3 h-full bg-space-900 border-l border-space-800 flex flex-col z-10 shadow-2xl">
        <div className="p-4 border-b border-space-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-accent-500" />
            <span className="font-bold text-sm tracking-widest text-gray-300">CONFIGURATION</span>
          </div>
          <button
            onClick={() => setShowAssetManager(true)}
            className="p-2 hover:bg-space-700 rounded-lg transition"
            title="Asset Manager"
          >
            <Settings size={18} className="text-gray-400 hover:text-accent-400" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <ControlPanel
            platforms={platforms}
            payloads={payloads}
            selectedPlatformId={selectedPlatformId}
            selectedPayloadId={selectedPayloadId}
            month={month}
            duration={duration}
            radius={radius}
            margin={margin}
            onChange={handleChange}
            onSimulate={handleSimulate}
            loading={loading}
          />

          <QuoteCard result={result} />
        </div>
      </div>

      {/* Asset Manager Modal */}
      {showAssetManager && <AssetManager onClose={handleAssetManagerClose} />}
    </div>
  );
}

export default App;
