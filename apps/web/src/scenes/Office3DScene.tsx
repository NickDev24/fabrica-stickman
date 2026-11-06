import { useRef, useState, useEffect, createContext, useContext, useReducer } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Environment, ContactShadows, Html, Stars, useIntersect } from "@react-three/drei";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

// Design tokens (barto's fenix: Space Grotesk + ink/paper + #FF5C35 accent)
const PALETTE = {
  ink: "#111827",
  paper: "#F5F1E8",
  accent: "#FF5C35",
  deep: "#0F172A",
  muted: "#475569",
  heroText: "#FFFFFF",
  mutedText: "#94A3B8",
  border: "#334155",
};

// Typecheck cutoff guard: floor area used by the scene
const ROOM_SIZE = 18;

// ─── Factory task state (single source of truth for the 3D oficina) ───
export type TaskState = "idle" | "searching" | "selecting" | "creating" | "done" | "error";

export interface FactoryAgent {
  id: string;
  name: string;
  role: string;
  color: number;
  task: TaskState;
  taskDetail: string;
  station: THREE.Vector3;
}

export const AGENTS: FactoryAgent[] = [
  { id: "nova",  name: "Nova",   role: "Onboarding",       color: 0xF472B6, task: "idle",       taskDetail: "Bienvenido — configura tu fábrica", station: new THREE.Vector3(-2.6, -0.25, 0.6) },
  { id: "kai",   name: "Kai",    role: "APIs & MCPs",      color: 0x38BDF8, task: "idle",       taskDetail: "Buscando proveedores en línea", station: new THREE.Vector3(-2.6, -0.25, 0.6) },
  { id: "luna",  name: "Luna",   role: "Skills",           color: 0x34D399, task: "idle",       taskDetail: "Escaneando skills instalados", station: new THREE.Vector3(2.6, -0.25, 0.6) },
  { id: "zern",  name: "Zern",   role: "Conectores",       color: 0xFBBF24, task: "idle",       taskDetail: "Vincular Zernio (TikTok/FB/IG/YT)", station: new THREE.Vector3(2.6, -0.25, 0.6) },
];

export const INITIAL_TASK: FactoryAgent[] = AGENTS.map((a) => ({ ...a, task: "idle", taskDetail: a.taskDetail }));

export interface FactoryStore {
  agents: FactoryAgent[];
  productionPhase: string;
  setTask: (id: string, task: TaskState, detail: string) => void;
  clearTask: (id: string) => void;
  setProductionPhase: (p: string) => void;
  reset: () => void;
}

const factoryReducer = (s: FactoryAgent[], action: Partial<FactoryAgent>): FactoryAgent[] =>
  s.map((a) => (a.id === action.id ? { ...a, ...action } : a));

export const FactoryContext = createContext<FactoryStore | null>(null);

export function FactoryProvider({ children }: { children: React.ReactNode }) {
  const [agents, dispatch] = useReducer(factoryReducer, INITIAL_TASK);

  const setTask = (id: string, task: TaskState, detail: string) => {
    dispatch({ id, task, taskDetail: detail });
  };

  const clearTask = (id: string) => {
    dispatch({ id, task: "idle", taskDetail: agents.find((a) => a.id === id)?.taskDetail || "" });
  };

  const setProductionPhase = (p: string) => {
    dispatch({ id: "", task: "searching", taskDetail: p });
  };

  const reset = () => {
    dispatch({ id: "" });
  };

  const value = { agents, productionPhase: "", setTask, clearTask, setProductionPhase, reset };

  return <FactoryContext.Provider value={value}>{children}</FactoryContext.Provider>;
}

export function useFactory() {
  const ctx = useContext(FactoryContext);
  if (!ctx) throw new Error("useFactory must be used within FactoryProvider");
  return ctx;
}

/** Reusable 3D furniture loader. */
function Model3D({ glbPath, label }: { glbPath: string; label?: string }) {
  const group = useRef<THREE.Group>(null);
  const [loaded, setLoaded] = useState(false);

  useFrame(() => {
    if (group.current && loaded) {
      group.current.rotation.y += 0.002;
    }
  });

  useIntersect(() => {
    if (loaded || !group.current) return;
    const loader = new GLTFLoader();
    loader.load(glbPath, (gltf: any) => {
      const node = gltf.scene || gltf.scenes?.[0];
      if (node) {
        group.current!.attach(node);
        setLoaded(true);
      }
    });
  });

  return (
    <group ref={group}>
      <meshStandardMaterial color={0xff5c35} emissive={0xff5c35} emissiveIntensity={0.06} />
      {loaded ? (
        <Html center position={[0, 1.0, 0]}>
          <div className="label-chip">
            <span className="label-chip__dot" style={{ background: 0xff5c35 }} />
            {label}
          </div>
        </Html>
      ) : (
        <sphereGeometry args={[0.8, 16, 16]} />
      )}
    </group>
  );
}

/** Agent 3D whose body follows its real task state from the factory store. */
function AgentMarker({ agent, station }: { agent: FactoryAgent; station: THREE.Vector3 }) {
  const group = useRef<THREE.Group>(null);
  const [loaded, setLoaded] = useState(false);
  const { agents, setTask, productionPhase } = useFactory();

  // Current agent state from the store — never undefined (fallback to defaults)
  const state: FactoryAgent = agents.find((x) => x.id === agent.id) ?? {
    ...agent,
    task: "idle",
    taskDetail: agent.role,
  }

  useFrame(() => {
    if (group.current && loaded) {
      group.current.rotation.y += 0.002;
      // Walk between stations when the pipeline is in a phase that moves agents
      const moving = productionPhase.length > 0 && state.task !== "idle";
      if (moving) {
        group.current.position.y = Math.sin(Date.now() * 0.002) * 0.06;
        group.current.position.x += Math.sin(Date.now() * 0.001) * 0.001;
      }
    }
  });

  // Transition states when the pipeline changes
  useEffect(() => {
    if (state.task === "error") {
      // error: quick shake
      let i = 0;
      const id = setInterval(() => {
        if (group.current) {
          group.current.position.x = Math.sin(Date.now() * 0.06) * 0.08;
          group.current.position.z = Math.cos(Date.now() * 0.06) * 0.08;
        }
        i++;
        if (i > 20) clearInterval(id);
      }, 80);
      return () => clearInterval(id);
    }
    if (state.task === "creating") {
      // create: calm idle bob
      let ids = 0;
      const id = setInterval(() => {
        if (group.current) {
          group.current.position.y = Math.sin(Date.now() * 0.002) * 0.06;
        }
      }, 40);
      return () => clearInterval(id);
    }
    // idle / searching / selecting / done: gentle idle rotation
  }, [state.task]);

  useIntersect(() => {
    if (loaded) return;
    const loader = new GLTFLoader();
    // Each agent maps to its own 3D model by role; fallback to bomi for all
    const path = state.id === "luna" ? "/oficina3d/characters/office-seo.glb" : "/oficina3d/characters/office-bomi.glb";
    loader.load(path, (gltf: any) => {
      const node = gltf.scene || gltf.scenes?.[0];
      if (node && group.current) {
        group.current.attach(node);
        setLoaded(true);
      }
    });
  });

  return (
    <group ref={group} position={station}>
      <meshStandardMaterial color={0xff5c35} emissive={0xff5c35} emissiveIntensity={0.06} />
      {loaded ? (
        <Html center position={[0, 1.0, 0]}>
          <div className="label-chip">
            <span className="label-chip__dot" style={{ background: agent.color }} />
            <span className="label-chip__name">{agent.name}</span>
            <span className="label-chip__role">{agent.role}</span>
            <span className="label-chip__task">{state.task.toUpperCase()}</span>
            <span className="label-chip__detail">{state.taskDetail}</span>
          </div>
        </Html>
      ) : (
        <sphereGeometry args={[0.5, 16, 16]} />
      )}
    </group>
  );
}

export function Office3D() {
  return (
    <>
      <color attach="background" args={[PALETTE.deep]} />
      <Stars radius={40} depth={20} count={4000} factor={4} />

      {/* floor */}
      <group position={[0, -0.5, 0]}>
        <planeGeometry args={[ROOM_SIZE, ROOM_SIZE]} />
        <meshStandardMaterial color={0x0f172a} roughness={0.95} metalness={0.0} />
        <gridHelper args={[ROOM_SIZE, ROOM_SIZE, 0x232323, 0x232323]} />
      </group>

      {/* isometric back wall: metrics panel + winner monitor */}
      <group position={[0, 0.2, -ROOM_SIZE / 2 + 0.5]}>
        <meshStandardMaterial color={0xf5f1e8} roughness={0.25} metalness={0.5} side={THREE.DoubleSide} />
        <boxGeometry args={[5.4, 2.4, 0.12]} />
        <Html position={[0.0, 0.6, 0.12]} center>
          <div className="metrics-panel">
            <div className="metrics-panel__title">PANTALLA GANADORA · SEMANA</div>
            <div className="metric-row"><strong>12</strong> video stickman</div>
            <div className="metric-row"><strong>8</strong> cómics esta semana</div>
            <div className="metric-row"><strong>4/4</strong> agentes activos</div>
            <div className="metric-row"><strong>Atlas</strong> · respuesta 2.1s</div>
          </div>
        </Html>
      </group>

      {/* furniture */}
      <group position={[0, -0.25, 1.0]}>
        <Model3D glbPath="/oficina3d/furniture/conference-table-v1.glb" label="Mesa" />
        <Model3D glbPath="/oficina3d/furniture/office-chair-v1.glb" label="Silla" />
      </group>

      {/* agent pods */}
      {AGENTS.map((agent) => (
        <group key={agent.id} position={agent.station}>
          <AgentMarker agent={agent} station={agent.station} />
        </group>
      ))}

      {/* main canvas = image generator display */}
      <group position={[0, 0.3, -ROOM_SIZE / 2 + 1.0]}>
        <Model3D glbPath="/oficina3d/furniture/mobile-board-v1.glb" label="Tablet de tinta" />
        <Html position={[0, 0, 0.12]} className="screen" center>
          <div className="screen__glow" />
          <div className="screen__body">
            <div className="screen__topbar">
              <span>✎ trazado en tinta</span>
              <span className="screen__mode">CANVAS 2D/3D</span>
            </div>
            <canvas width={640} height={360} className="screen__pix" data-status="drawing" />
            <div className="screen__bottom">
              <div className="screen__progress">0%</div>
              <div className="screen__pulp" />
            </div>
          </div>
        </Html>
      </group>

      <OrbitControls makeDefault minPolarAngle={1.0} maxPolarAngle={1.8} target={[0, 0.1, 0]} minDistance={6} maxDistance={18} />
      <ContactShadows position={[0, -0.45, 0]} blur={0.8} scale={ROOM_SIZE - 0.8} opacity={0.28} />
      <Environment preset="studio" />
    </>
  );
}
