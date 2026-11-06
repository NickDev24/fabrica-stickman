import Phaser from "phaser";

/**
 * CircularOfficeScene — a round "mesa redonda" office instead of desktop desks.
 *
 * Design rules (tokens, no hardcoded brand colors beyond the palette):
 *  - Palette: ink #111827, paper #F5F1E8, warm accent #FF5C35, muted #0F172A.
 *  - Round table in the centre, "winner board" screen facing the players,
 *    agents on a ring around the table with idle/talk/walk/celebrate/error ticks.
 */
export interface AgentDef {
  id: string;
  name: string;
  color: number;
  angle: number; // degrees, 0 = right (3 o'clock)
  radius: number;
  yOffset: number;
}

export const AGENTS: AgentDef[] = [
  { id: "nova", name: "Nova", color: 0xf472b6, angle: 135, radius: 260, yOffset: -20 },
  { id: "kai", name: "Kai", color: 0x38bdf8, angle: 45, radius: 260, yOffset: -20 },
  { id: "luna", name: "Luna", color: 0x34d399, angle: 225, radius: 260, yOffset: -20 },
  { id: "zern", name: "Zern", color: 0xfbbf24, angle: -45, radius: 260, yOffset: -20 },
];

export const WINNER_BOARD = {
  title: "Ganador de la semana",
  subtitle: "El contenido que más se compartió",
  lines: [
    { rank: "1", label: "Video stickman", text: "¿Cómo se mueve una gota? (con tinta)" },
    { rank: "2", label: "Cómics de la mañana", text: "El día que Zern se equivocó" },
    { rank: "3", label: "Tutorial", text: "Pega tu API key en 30 segundos" },
  ],
};

export class CircularOfficeScene extends Phaser.Scene {
  private table!: Phaser.GameObjects.Rectangle;
  private board!: Phaser.GameObjects.Rectangle;
  private boardLabel!: Phaser.GameObjects.Text;
  private ring!: Phaser.GameObjects.Container;
  private agents = new Map<string, Phaser.GameObjects.Container>();
  private tick = 0;
  private bob = 0;

  constructor() {
    super("CircularOfficeScene");
  }

  create() {
    this.cameras.main.setBackgroundColor(0x0f172a);

    // Floor (round, faint)
    const floor = this.add.graphics();
    floor.fillStyle(0x1e293b, 1);
    floor.fillCircle(760, 550, 620);
    floor.lineStyle(4, 0x0ea5e9, 0.25);
    floor.lineStyle(4, 0x0ea5e9, 1);
    floor.strokeCircle(760, 550, 620);

    // Round table
    this.table = this.add.rectangle(760, 550, 380, 380, 0xf5f1e8);
    this.table.setStrokeStyle(3, 0x111827);

    // Inner ring highlight (wood edge)
    const edge = this.add.graphics();
    edge.lineStyle(3, 0x111827, 1); edge.fillStyle(0x111827, 1);
    edge.fillCircle(760, 550, 360);

    // Winner board (screen on the table)
    this.board = this.add.rectangle(760, 550, 260, 160, 0xffffff, 0.96);
    this.board.setStrokeStyle(2, 0xff5c35);
    this.boardLabel = this.add.text(760, 550 - 40, "Ganador de la semana", {
      fontSize: "17px",
      color: "#111827",
      fontFamily: "Space Grotesk, sans-serif",
    }).setOrigin(0.5);
    this.add.text(760, 550 + 48, "El contenido que más se compartió", {
      fontSize: "12px",
      color: "#64748b",
      fontFamily: "JetBrains Mono, monospace",
    }).setOrigin(0.5);

    // Ring of agents
    this.ring = this.add.container(760, 550);
    AGENTS.forEach((a) => this.spawnAgent(a));
  }

  private spawnAgent(a: AgentDef) {
    const group = this.add.group();
    const body = this.add.rectangle(0, 0, 22, 44, a.color).setStrokeStyle(2, 0xffffff);
    const head = this.add.ellipse(0, -34, 15, 17, 0xf8fafc).setStrokeStyle(2, 0x111827);
    const label = this.add.text(0, 46, a.name, {
      fontSize: "13px",
      color: "#fff",
      fontFamily: "Space Grotesk, sans-serif",
    }).setOrigin(0.5);

    const container = this.add.container(0, 0, [body, head, label]) ;
    container.setSize(52, 72);
    container.setInteractive({ useHandCursor: true });
    this.ring.add(container);
    this.agents.set(a.id, container);

    // Personality ticks (idle bob + occasional celebrate)
    this.tweens.add({
      targets: container,
      y: "-=8",
      duration: 1400 + Math.random() * 900,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });
  }

  update(time: number, delta: number) {
    this.bob += delta * 0.3;
    this.table.setPosition(760 + Math.sin(this.bob) * 0.4, 550 + Math.cos(this.bob) * 0.4);

    // Glint on the winner board screen
    const wave = Math.sin(time * 0.004) * 0.06 + 0.94;
    this.board.setAlpha(wave);

    // Celebrate flash when a new item ranks (simulated)
    const flash = Math.sin(time * 0.007) * 0.5 + 0.5;
    this.add.rectangle(760, 550, 262, 164, 0xff5c35, flash * 0.08);

    // Agent spontaneous celebrate tick
    this.tick += delta;
    if (this.tick > 22000 + Math.random() * 18000) {
      this.tick = 0;
      this.agents.forEach((c) => {
        this.tweens.add({ targets: c, scaleX: 1.1, scaleY: 0.9, duration: 120, yoyo: true, repeat: 1 });
      });
    }
  }
}
