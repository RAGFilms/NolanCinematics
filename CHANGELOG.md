# Changelog — NolanCinematics

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2025

### Initial Release

**Films**
- Batman Begins (2005) — Wally Pfister ASC
- The Dark Knight (2008) — Wally Pfister ASC
- The Dark Knight Rises (2012) — Wally Pfister ASC
- Interstellar (2014) — Hoyte van Hoytema FSF NSC
- Dunkirk (2017) — Hoyte van Hoytema FSF NSC
- Oppenheimer (2023) — Hoyte van Hoytema FSF NSC

**Camera & Format**
- 5 output format presets: Scope HD/2K/4K, IMAX 2K/4K
- 7 focal length presets (21mm–150mm) + Custom mm
- 5 aperture presets (T1.9–T8)
- Sensor dimensions matched to actual film stock specs
- Anamorphic bokeh ratio applied to camera DOF

**Compositor Pipeline**
- Lens Distortion node (barrel K1 + chromatic aberration)
- Anamorphic Flare Streaks (2-streak Glare, intensity-controlled)
- Film Grade (ASC CDL Lift/Gamma/Gain, per-film RGB)
- Saturation HueSat multiplier
- Shadow Crush (per-film lift depth, blend factor)
- Vignette (EllipseMask → Gaussian Blur → Multiply)
- All stages independently toggleable

**Live Updates**
- All Per-Shot Controls sliders write directly to active NC_ nodes in real time

**Compatibility**
- Blender 3.0–5.x support
- Blender 4.x socket rename handling throughout
- QUICK SETUP one-click camera + compositor apply
