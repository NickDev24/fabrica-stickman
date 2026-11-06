import React, { useEffect, useRef } from "react";
import Phaser from "phaser";
import { OfficeScene } from "./scenes/OfficeScene";

export default function App() {
  const ref = useRef<HTMLDivElement>(null);
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
      <header className="p-4 border-b border-slate-700">
        <h1 className="text-2xl font-bold">Fábrica Autónoma — Oficina 2D</h1>
        <p className="text-slate-400 text-sm">Usa las flechas para moverte. Habla con los agentes.</p>
      </header>
      <main className="flex-1 flex items-center justify-center p-4">
        <div ref={ref} className="rounded-xl overflow-hidden shadow-2xl" />
      </main>
    </div>
  );
}
