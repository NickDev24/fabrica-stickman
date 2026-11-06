import Phaser from "phaser";
import { CircularOfficeScene } from "./CircularOfficeScene";

export interface OfficeBridge {
  onToggleOffice: () => void;
}

export class OfficeScene extends Phaser.Scene {
  private player!: Phaser.GameObjects.Container;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;

  constructor() {
    super("OfficeScene");
  }

  create(data: { bridge?: OfficeBridge } = {}) {
    const bridge = data.bridge;

    // Round office world (1600x1100 canvas, circular scene inset)
    this.cameras.main.setBounds(0, 0, 1600, 1100);
    this.cameras.main.setBackgroundColor(0x0f172a);

    // Decorative round background
    const bg = this.add.graphics();
    bg.fillStyle(0x0f172a, 1);
    bg.fillCircle(800, 550, 850);
    bg.lineStyle(2, 0x0ea5e9, 0.12);
    bg.lineStyle(2, 0x0ea5e9, 1);
    bg.strokeCircle(800, 550, 850);

    // Wall panels / floor
    const g = this.add.graphics();
    g.fillStyle(0x1e293b, 1);
    g.fillRect(0, 0, 1600, 1100);
    // decorative ring (desk ring)
    g.fillStyle(0x0f172a, 0.6);
    g.fillCircle(800, 550, 560);
    g.lineStyle(2, 0x0ea5e9, 0.15);
    g.lineStyle(2, 0x0ea5e9, 1);
    g.strokeCircle(800, 550, 560);

    // Add the circular office scene as a sub-scene overlay
    this.scene.add("CircularOffice", CircularOfficeScene);

    // Player (cursor follower)
    this.player = this.add.container(800, 980);
    const pBody = this.add.rectangle(0, 0, 24, 52, 0xffffff).setStrokeStyle(3, 0x111827);
    const pHead = this.add.rectangle(0, -38, 24, 20, 0xfde68a).setStrokeStyle(2, 0x111827);
    this.player.add([pBody, pHead]);
    this.player.setSize(40, 70);
    this.player.setInteractive({ useHandCursor: true });

    this.cursors = this.input.keyboard!.createCursorKeys();
    this.input.setDefaultCursor("auto");

    this.input.keyboard!.on("keydown-E", () => {
      if (bridge?.onToggleOffice) bridge.onToggleOffice();
    });
  }

  update(_time: number, _delta: number) {
    const speed = 3;
    if (this.cursors.left.isDown) this.player.x -= speed;
    if (this.cursors.right.isDown) this.player.x += speed;
    if (this.cursors.up.isDown) this.player.y -= speed;
    if (this.cursors.down.isDown) this.player.y += speed;
    this.player.x = Phaser.Math.Clamp(this.player.x, 30, 1570);
    this.player.y = Phaser.Math.Clamp(this.player.y, 60, 1040);
    this.cameras.main.startFollow(this.player, false, 0.12, 0.12);
    this.cameras.main.setFollowOffset(0, 60);
    this.cameras.main.setZoom(0.85);
  }
}
