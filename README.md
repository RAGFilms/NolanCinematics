# NolanCinematics — Blender Add-on

**Version 1.0.0 · AGW Entertainment**

> *The complete cinematographic pipeline of Christopher Nolan productions — inside Blender.*

---

## What It Does

NolanCinematics replicates the full optical and photochemical pipeline of six Nolan/Pfister/van Hoytema productions in a single N-Panel tab. One click configures your camera sensor, lens focal length, anamorphic DOF bokeh, and builds a complete compositor node chain — color grade, shadow crush, lens distortion, chromatic aberration, anamorphic flare streaks, and vignette — tuned to the specific photographic character of each film.

All compositor parameters update live via slider; no rebuilds required during shot refinement.

---

## Films Covered

| Film | DP | Lenses |
|---|---|---|
| **Batman Begins** (2005) | Wally Pfister ASC | Panavision Primo anamorphic |
| **The Dark Knight** (2008) | Wally Pfister ASC | Panavision C/H-Series anamorphic · IMAX spherical |
| **The Dark Knight Rises** (2012) | Wally Pfister ASC | Panavision anamorphic · IMAX spherical |
| **Interstellar** (2014) | Hoyte van Hoytema FSF NSC | Panavision anamorphic · IMAX 65mm spherical |
| **Dunkirk** (2017) | Hoyte van Hoytema FSF NSC | IMAX 65mm spherical · Panavision anamorphic 35mm |
| **Oppenheimer** (2023) | Hoyte van Hoytema FSF NSC | IMAX 65mm · Panavision 65mm — no digital intermediate |

---

## Features

### Camera & Format
- **5 output formats** — Scope 1080p preview, Anamorphic Scope 2K/4K (2.39:1), IMAX 1.43:1 2K/4K
- **7 focal length presets** — 21mm through 150mm, plus Custom mm entry, with Nolan production notes
- **5 aperture presets** — T1.9 through T8, matching Pfister/van Hoytema working stops
- Sensor dimensions set to actual film stock specs (36×24mm anamorphic, 70.41×52.48mm IMAX)
- Anamorphic bokeh ratio applied directly to camera DOF (2.0× oval for scope, 1.0× circular for IMAX)

### Compositor Pipeline
Each stage is independently toggleable and builds as prefixed `NC_` nodes that sit cleanly alongside your existing tree:

1. **Lens Distortion** — barrel K1 preset-matched per format, with Blender 3.x/4.x socket fallback
2. **Anamorphic Flare Streaks** — horizontal 2-streak Glare node, intensity-controlled
3. **Film Grade** — ASC CDL Lift/Gamma/Gain ColorBalance node with per-film RGB tuning
4. **Saturation** — HueSat multiplier on the film baseline, live-adjustable
5. **Shadow Crush** — second ColorBalance pass with per-film lift depth, blend-controlled
6. **Vignette** — EllipseMask → Gaussian Blur → Multiply chain; scope-oval or circular per format

### Live Updates
All Per-Shot Controls sliders (exposure, grade strength, saturation, shadow crush, flare, distortion, chromatic aberration, bokeh ratio, vignette) write directly to the active NC_ nodes in real time. No rebuild needed during a shot.

### Lighting Notes
Per-film lighting reference drawn from production interviews — motivated sources, practical color temperature, key-to-fill ratios — displayed in-panel per selected film.

---

## Output Formats

| Preset | Resolution | Aspect | Sensor | Bokeh |
|---|---|---|---|---|
| Scope 1080p Preview | 1920×804 | 2.39:1 | 36×24mm | 2.0× oval |
| Anamorphic Scope 2K | 2048×858 | 2.39:1 | 36×24mm | 2.0× oval |
| Anamorphic Scope 4K | 4096×1716 | 2.39:1 | 36×24mm | 2.0× oval |
| IMAX 1.43:1 2K | 2048×1433 | 1.43:1 | 70.41×52.48mm | 1.0× circular |
| IMAX 1.43:1 4K | 4096×2866 | 1.43:1 | 70.41×52.48mm | 1.0× circular |

---

## Installation

1. Download `NolanCinematics.zip`
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Navigate to the zip and click **Install Add-on**
4. Enable **NolanCinematics** in the add-on list
5. Open the **N-Panel** in the 3D Viewport (`N` key) → **NolanCinematics** tab

---

## Workflow

**Fastest path:** Select your film and format, hit **⚡ QUICK SETUP ⚡** — camera and full compositor chain configured in one shot.

**Manual path:**
1. Set Film Grade and Format in the main panel
2. **Camera & Lens** sub-panel → set focal and aperture → **Apply to Camera**
3. **Compositor Pipeline** sub-panel → toggle stages → **Build**
4. Fine-tune in **Per-Shot Controls** — all sliders update live

**Changing film mid-project:** Change the Film Grade selector, then **Rebuild** in the Compositor Pipeline panel. Your non-NC nodes are untouched.

---

## Compatibility

- Blender **3.0** through **5.x**
- Tested on Blender 4.x and 5.1
- Cycles and EEVEE (compositor chain is renderer-agnostic; DOF bokeh ratio requires Cycles or EEVEE Next)
- Blender 4.x socket rename handling built in — no manual fixes required

---

## License

MIT License — see `LICENSE` file.

---

## Author

**AGW Entertainment**


