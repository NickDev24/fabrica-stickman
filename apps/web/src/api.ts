/**
 * Cliente API para comunicarse con el backend factoryd (puerto 8610)
 */

const API_BASE = "http://localhost:8610";

export interface FactoryState {
  estado: string;
  episodio_actual: string | null;
  progreso: number;
  ultima_actividad: string;
  metricas: {
    cpu: number;
    memoria: number;
    imagenes_generadas: number;
    videos_rendereados: number;
  };
}

export interface Episode {
  slug: string;
  titulo: string;
  estado: string;
  creado_en: string;
}

export async function getFactoryState(): Promise<FactoryState> {
  const response = await fetch(`${API_BASE}/api/estado`);
  if (!response.ok) {
    throw new Error(`Error fetching state: ${response.statusText}`);
  }
  return response.json();
}

export async function getEpisodes(): Promise<Episode[]> {
  const response = await fetch(`${API_BASE}/api/episodios`);
  if (!response.ok) {
    throw new Error(`Error fetching episodes: ${response.statusText}`);
  }
  return response.json();
}

export async function createEpisode(titulo: string, nicho: string): Promise<Episode> {
  const response = await fetch(`${API_BASE}/api/episodios`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ titulo, nicho }),
  });
  if (!response.ok) {
    throw new Error(`Error creating episode: ${response.statusText}`);
  }
  return response.json();
}

export async function controlFactory(action: "play" | "pause" | "stop" | "skip"): Promise<void> {
  const response = await fetch(`${API_BASE}/api/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accion: action }),
  });
  if (!response.ok) {
    throw new Error(`Error controlling factory: ${response.statusText}`);
  }
}

export interface WebSocketMessage {
  tipo: "estado" | "progreso" | "error" | "nuevo_episodio";
  datos: any;
}

export function connectWebSocket(onMessage: (msg: WebSocketMessage) => void): WebSocket {
  const ws = new WebSocket(`ws://localhost:8610/ws`);
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as WebSocketMessage;
      onMessage(msg);
    } catch (e) {
      console.error("Error parsing WS message:", e);
    }
  };
  return ws;
}
