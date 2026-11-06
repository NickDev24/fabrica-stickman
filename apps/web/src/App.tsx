import React, { useEffect, useRef, useState } from "react";
import Phaser from "phaser";
import { OfficeScene } from "./scenes/OfficeScene";
import { useStore, exportEnv } from "./store";

const i18n = {
  es: { title: "Fábrica Autónoma — Oficina 2D", paste: "Pegar API Key", skip: "Saltar por ahora", export: "Exportar config .env", progress: "Progreso" },
  en: { title: "Autonomous Factory — 2D Office", paste: "Paste API Key", skip: "Skip for now", export: "Export config .env", progress: "Progress" },
} as const;
type L = keyof typeof i18n;

export default function App() {
  const ref = useRef<HTMLDivElement>(null);
  const cfg = useStore((s) => s.cfg);
  const progress = useStore((s) => s.progress);
  const [lang, setLang] = useState<L>("es");
  const t = i18n[lang];
  useEffect(() => {
    if (!ref.current) return;
    const game = new Phaser.Game({
      type: Phaser.AUTO,
      width: 960,
      height: 640,
      parent: ref.current,
      scene: [OfficeScene],
      backgroundColor: "#0f172a",
    });
    return () => game.destroy(true);
  }, []);
  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col">
      <header className="p-4 border-b border-slate-700 flex justify-between">
        <h1 className="text-2xl font-bold">{t.title}</h1>
        <select aria-label="language" value={lang} onChange={(e) => setLang(e.target.value as L)}>
          <option value="es">ES</option><option value="en">EN</option>
        </select>
      </header>
      <main className="flex-1 flex gap-4 p-4">
        <div ref={ref} className="rounded-xl overflow-hidden shadow-2xl" />
        <aside className="w-72 bg-slate-800 rounded-xl p-4" aria-label="panel">
          <h2>{t.progress}: {progress}%</h2>
          <ul>{cfg.map((c) => <li key={c.key}>{c.key} = ••••</li>)}</ul>
          <div className="flex gap-2 mt-4">
            <button className="px-3 py-2 bg-emerald-600 rounded">{t.paste}</button>
            <button className="px-3 py-2 bg-slate-600 rounded">{t.skip}</button>
          </div>
          <button className="mt-3 px-3 py-2 bg-sky-600 rounded" onClick={() => {
            const blob = new Blob([exportEnv(cfg)], { type: "text/plain" });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = ".env";
            a.click();
          }}>{t.export}</button>
        </aside>
      </main>
    </div>
  );
}
