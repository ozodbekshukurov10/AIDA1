import * as THREE from 'three';

export class CinematicCameraController {
  targetPosition: THREE.Vector3;
  targetLookAt: THREE.Vector3;
  currentLookAt: THREE.Vector3;

  constructor() {
    this.targetPosition = new THREE.Vector3(0, 0, 16);
    this.targetLookAt = new THREE.Vector3(0, 0, 0);
    this.currentLookAt = new THREE.Vector3(0, 0, 0);
  }

  update(
    camera: THREE.PerspectiveCamera,
    phase: number,
    time: number,
    mouseX: number,
    mouseY: number,
    isReducedMotion: boolean
  ) {
    if (phase === 0) {
      // Phase 0: Opening. Slow ambient drift, smooth push in.
      const push = time < 3.0 ? time * 0.45 : 1.35;
      this.targetPosition.set(
        Math.sin(time * 0.06) * 1.2,
        Math.cos(time * 0.04) * 0.6,
        17.5 - push
      );
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 1) {
      // Phase 1: Logo Reveal. Precise centered framing.
      this.targetPosition.set(0, 0, 14.0);
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 2) {
      // Phase 2: Text Story. Pan right for typography canvas.
      this.targetPosition.set(
        1.4 + Math.sin(time * 0.15) * 0.4,
        -0.4 + Math.cos(time * 0.12) * 0.2,
        15.2
      );
      this.targetLookAt.set(0.4, 0, 0);
    } 
    else if (phase === 3) {
      // Phase 3: AIDA Transformation. Slowly back up to view intelligence system.
      this.targetPosition.set(
        Math.sin(time * 0.08) * 1.8,
        Math.cos(time * 0.06) * 1.2,
        16.8
      );
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 4) {
      // Phase 4: Core Zoom-in. Zoom close to Core.
      this.targetPosition.set(0, 0, 8.5);
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 5) {
      // Phase 5: Memory Exploration. Camera approaches Memory Clusters
      this.targetPosition.set(-1.8, 1.2, 3.8);
      this.targetLookAt.set(-2.0, 0.6, -2.0);
    } 
    else if (phase === 6) {
      // Phase 6: Information Retrieval / Vector Search. Focus on KNOWLEDGE cluster
      this.targetPosition.set(1.8, 1.4, 3.2);
      this.targetLookAt.set(2.2, 1.6, -1.5);
    } 
    else if (phase === 7) {
      // Phase 7: Reasoning. Focus on REASONING cluster (Violet)
      this.targetPosition.set(0.8, 1.8, 3.5);
      this.targetLookAt.set(0.6, 2.2, 1.0);
    } 
    else if (phase === 8) {
      // Phase 8: Tools & Memory. Orbit and look at TOOLS cluster (Purple)
      this.targetPosition.set(2.0, -0.4, 3.8);
      this.targetLookAt.set(2.4, -0.6, 1.8);
    } 
    else if (phase === 9) {
      // Phase 9: Verification. Slow sweeping orbit.
      this.targetPosition.set(
        Math.sin(time * 0.3) * 5.5,
        Math.cos(time * 0.15) * 1.8,
        6.5
      );
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 10) {
      // Phase 10: Global Neural Convergence — Slow orbital sweep settling toward center
      this.targetPosition.set(
        Math.sin(time * 0.35) * 3.5,
        Math.cos(time * 0.25) * 1.2,
        9.5
      );
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 11) {
      // Phase 11: Core Power-Up & Implosion -> Silence Pause. Push in close
      this.targetPosition.set(0, 0, 7.2);
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 12) {
      // Phase 12: MASSIVE AIDA BRAND REVEAL — Centered framing with slow cinematic push-in
      const push = (time % 5.0) * 0.25;
      this.targetPosition.set(0, 0, 11.5 - push);
      this.targetLookAt.set(0, 0, 0);
    } 
    else if (phase === 13) {
      // Phase 13: Final Transition — Smooth 60fps camera thrust straight through inside the word AIDA into website
      const elapsed = time % 1.5;
      const transitionZoom = 11.5 * (1 - (elapsed / 1.2));
      
      this.targetPosition.set(0, 0, Math.max(-1.5, transitionZoom));
      this.targetLookAt.set(0, 0, 0);
    }

    // Parallax mouse influence
    if (!isReducedMotion) {
      this.targetPosition.x += mouseX * 1.2;
      this.targetPosition.y += mouseY * 0.8;
    }

    // Smooth exponential spline lerp (no robotic linear steps)
    const lerpSpeed = isReducedMotion ? 0.015 : 0.045;
    camera.position.lerp(this.targetPosition, lerpSpeed);
    this.currentLookAt.lerp(this.targetLookAt, lerpSpeed);
    camera.lookAt(this.currentLookAt);

    // Dynamic Field of View adjustment
    if (phase >= 4 && phase <= 12) {
      camera.fov = THREE.MathUtils.lerp(camera.fov, 50, 0.03); // Cinematic narrow lens
    } else {
      camera.fov = THREE.MathUtils.lerp(camera.fov, 45, 0.03); // Standard lens
    }
    camera.updateProjectionMatrix();
  }
}
