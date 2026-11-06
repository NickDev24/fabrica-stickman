import Phaser from "phaser";

export class OfficeScene extends Phaser.Scene {
  private player!: Phaser.GameObjects.Rectangle;
  constructor() { super("OfficeScene"); }
  create() {
    this.cameras.main.setBackgroundColor("#1e293b");
    const graphics = this.add.graphics();
    graphics.fillStyle(0x334155, 1);
    graphics.fillRect(0, 0, 960, 640);
    // desks
    for (let i = 0; i < 4; i++) {
      const desk = this.add.rectangle(120 + i * 220, 260, 160, 60, 0x475569);
      desk.setStrokeStyle(2, 0x94a3b8);
    }
    // agents (stickman placeholders)
    const colors = [0xf472b6, 0x60a5fa, 0x34d399, 0xfbbf24];
    const names = ["Nova", "Kai", "Luna", "Zern"];
    colors.forEach((c, i) => {
      const x = 140 + i * 220;
      const body = this.add.rectangle(x, 200, 24, 48, c);
      this.add.text(x - 20, 160, names[i], { color: "#fff", fontSize: "14px" });
      this.tweens.add({ targets: body, y: 206, duration: 800, yoyo: true, repeat: -1 });
    });
    this.player = this.add.rectangle(480, 560, 20, 40, 0xffffff);
    this.input.keyboard?.on("keydown-LEFT", () => this.player.x -= 8);
    this.input.keyboard?.on("keydown-RIGHT", () => this.player.x += 8);
    this.input.keyboard?.on("keydown-UP", () => this.player.y -= 8);
    this.input.keyboard?.on("keydown-DOWN", () => this.player.y += 8);
  }
}
