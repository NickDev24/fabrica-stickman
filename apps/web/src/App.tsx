import React from "react";
import { Office3D } from "./scenes/Office3DScene";
import { useStore, exportEnv, seal } from "./store";

type AgentId = "nova" | "kai" | "luna" | "zern";

export default function App() {
  const ref = React.useRef<HTMLDivElement>(null);
  const cfg = useStore((s) => s.cfg);
  const progress = useStore((s) => s.progress);
  const add = useStore((s) => s.add);
  const bump = useStore((s) => s.bump);
  const load = useStore((s) => s.load);
  const [active, setActive] = React.useState<AgentId | null>(null);
  const [step, setStep] = React.useState(0);
  const [provider, setProvider] = React.useState("OpenAI");
  const [apiKey, setApiKey] = React.useState("");
  const [explain, setExplain] = React.useState(false);
  const [throttle, setThrottle] = React.useState(false);
  const [showCircular, setShowCircular] = React.useState(false);

  React.useEffect(() => {
    load();
  }, [load]);

  async function saveKey() {
    if (throttle) return;
    setThrottle(true);
    setTimeout(() => setThrottle(false), 600);
    await seal(apiKey);
    add({ key: `API_${provider.toUpperCase()}`, value: apiKey });
    bump();
    setStep((s) => s + 1);
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#0f172a] text-white">
      <header className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-[#0f172a]">
        <h1 className="text-lg font-bold tracking-tight">Fábrica Autónoma — Oficina 3D</h1>
        <span className="text-sm text-slate-400">ES</span>
      </header>

      <main className="flex-1 p-4 flex flex-col items-center justify-center">
        {/* 3D isometric oficina — the primary visual view */}
        <div className="office3d-wrapper w-full max-w-[1280px] rounded-xl overflow-hidden shadow-2xl border border-slate-700">
          <Office3D />
        </div>

        {/* Mobile controls scaffolding (the 3D scene controls itself via OrbitControls) */}
        <div className="flex gap-3 mt-3 flex-wrap items-center justify-center">
          <button
            className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm"
            onClick={() => setShowCircular(true)}
          >
            Abrir mesa redonda
          </button>
          <button
            className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm"
            onClick={() => setActive("nova")}
          >
            Nova
          </button>
          <button
            className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm"
            onClick={() => setActive("kai")}
          >
            Kai
          </button>
        </div>
      </main>

      {showCircular && (
        <div className="fixed inset-0 z-50 bg-[#0f172a]/90 flex items-center justify-center">
          <div className="text-center text-slate-300">
            <p className="text-lg font-bold">Mesa redonda — ganador de la semana</p>
            <p className="text-sm text-slate-400">El contenido más compartido del mes</p>
            <button
              className="mt-4 px-4 py-2 bg-[#FF5C35] text-white rounded hover:bg-[#e84e1f]"
              onClick={() => setShowCircular(false)}
            >
              Ver mesa redonda
            </button>
          </div>
        </div>
      )}

      <aside className="w-80 bg-[#1e293b] rounded-xl p-4 order-first md:order-last max-h-[60vh] overflow-y-auto">
        <h2>
          Progreso: {progress}%
        </h2>
        <p className="text-slate-400 text-sm">Usa flechas para moverte. Pulsa E cerca de un agente para hablar.</p>
        <ul className="mt-2 text-sm text-slate-300">
          {cfg.map((c) => (
            <li key={c.key}>
              {c.key} = <span className="text-slate-500">••••</span>
              <button
                className="text-xs text-sky-400 underline"
                onClick={() => { navigator.clipboard?.writeText(c.value); bump(); }}
              >
                copiar
              </button>
            </li>
          ))}
        </ul>
        {active && (
          <section aria-label="dialogue" className="mt-4 bg-[#0f172a] rounded-lg p-3">
            <h3 className="font-bold text-sm uppercase">{active}</h3>
            {active === "nova" && (
              <div>
                <p>¡Bienvenido! Soy Nova. Te guío para montar tu fábrica.</p>
                <button
                  className="mt-2 px-3 py-2 bg-emerald-600 rounded"
                  onClick={() => { bump(); setStep(1); }}
                >
                  Siguiente
                </button>
              </div>
            )}
            {active === "kai" && (
              <div className="space-y-2">
                <label className="block text-sm">Proveedor</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-[#1e293b] rounded px-2 py-2 text-sm"
                >
                  {["OpenAI", "Anthropic", "Gemini", "ElevenLabs", "HeyGen", "Runway"].map((p) => (
                    <option key={p} className="bg-[#1e293b]">{p}</option>
                  ))}
                </select>
                <label className="block text-sm">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-[#1e293b] rounded px-2 py-2 text-sm"
                  placeholder="sk-..."
                />
                <div className="flex gap-2">
                  <button
                    disabled={throttle}
                    className="px-3 py-2 bg-emerald-600 rounded"
                    onClick={saveKey}
                  >
                    Guardar
                  </button>
                  <button
                    className="px-3 py-2 bg-sky-600 rounded"
                    onClick={() => bump()}
                  >
                    Probar
                  </button>
                </div>
                <a
                  className="text-sky-400 underline text-sm"
                  href="https://platform.openai.com/api-keys"
                  target="_blank"
                  rel="noreferrer"
                >
                  ¿Cómo obtengo esto?
                </a>
                <button
                  className="text-amber-300 underline text-sm block"
                  onClick={() => setExplain((v) => !v)}
                >
                  Explícame como si tuviera 10 años
                </button>
                {explain && <p className="text-sm text-slate-200">Es como la contraseña de tu robot para hablar con la IA.</p>}
                <p className="text-xs text-slate-400">Guardado cifrado (Web Crypto) + localStorage</p>
                <p className="text-xs">Step: {step}</p>
              </div>
            )}
            {active === "luna" && <p>Escaneo ~/.claude/skills… (mock)</p>}
            {active === "zern" && <p>OAuth local: http://localhost:4321/callback</p>}
            <button className="mt-3 text-sm underline" onClick={() => setActive(null)}>
              Cerrar
            </button>
          </section>
        )}
        <div className="flex gap-2 mt-4 flex-wrap">
          <button className="px-3 py-2 bg-slate-600 rounded" onClick={() => setActive(null)}>
            Saltar por ahora
          </button>
        </div>
        <button
          className="mt-3 px-3 py-2 bg-sky-600 rounded"
          onClick={() => {
            const blob = new Blob([exportEnv(cfg)], { type: "text/plain" });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = ".env";
            a.click();
          }}
        >
          Exportar config .env
        </button>
      </aside>
    </div>
  );
}
