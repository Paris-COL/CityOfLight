<p align="center">
  <img src="docs/images/logo_col.png" alt="City of Light (COL)" width="160">
</p>

# City of Light (COL)
**A high-performance, Unity-based digital twin of Paris for embodied AI, robotics, and XR research.**

[![PyPI](https://img.shields.io/pypi/v/pycol.svg?label=PyPI&logo=pypi)](https://pypi.org/project/pycol/)
[![GitHub release](https://img.shields.io/github/v/release/Paris-COL/COL?logo=github)](https://github.com/Paris-COL/COL/releases)
[![License](https://img.shields.io/badge/Code-Apache%202.0-blue.svg)](LICENSE)
[![Assets License](https://img.shields.io/badge/Assets-CC%20BY--NC%204.0-purple.svg)](LICENSE_ASSETS.txt)
[![Docs](https://img.shields.io/badge/Docs-Website-informational)](https://paris-col.github.io) <!-- change when ready -->
<!-- [![Paper](https://img.shields.io/badge/Paper-arXiv-orange.svg)](https://arxiv.org/abs/XXXX.XXXXX) -->

<div align="center">
<strong>
[ <a href="#-quick-start">Quick Start</a> | 
<a href="#-features">Features</a> | 
<a href="#-installation">Installation</a> |
<a href="#-unity-builds--downloads">Unity Builds</a> |
<a href="#-licensing">Licensing</a> |
<a href="#-citation">Citation</a> ]
</strong>
</div>

---

<p align="center">
  <img src="docs/images/teaser.gif" alt="COL teaser" width="820">
</p>

**City of Light (COL)** is a geo-anchored, city-scale simulator of Paris (~116 km²) with synchronized multi-sensor streams (**RGB, Depth, Normals, Semantics**) and a zero-copy Python bridge (**TURBO**) that sustains very high throughput (up to ~1300 FPS on a 4090 in our tests).  
COL is designed for **fast scripting, large-scale data collection, RL**, **sim-to-real** and **embodied** research.

---

## 🧩 Features

- **Geo-faithful Paris digital twin** — per-tile meshes from public GIS.
- **Synchronized multi-sensors** — RGB / Depth / Normals / Semantics per frame.
- **TURBO zero-copy bridge** — shared-memory streaming to NumPy (no gRPC, no per-pixel copies).
- **High throughput** — frame-accurate control & observation at hundreds to thousands FPS (resolution-scalable).
- **Dynamic runtime** — stochastic pedestrians & vehicles; chunk streaming (3×3 tile window).
- **Python-first workflow** — simple APIs to launch Unity, move/rotate agent, step actions, and read frames.
- **Reproducible I/O** — deterministic stepping and per-frame update index.

---

## 🛠 Quick Start

### 1) Clone the repo
```bash
git clone https://github.com/Paris-COL/COL.git
cd COL

