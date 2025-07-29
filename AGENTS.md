# Agent Guidelines

This repository contains small pygame demos for 2D particle-based physics simulations. Each script showcases a particular setup built from particles and springs.

## File overview

- `particle.py` – Particle class using Verlet integration.
- `spring.py` – linear spring connecting two particles.
- `bending_spring.py` – bending constraint that keeps an angle between three particles.
- `physics.py` – `PhysicsEngine` that applies forces, drag and Brownian noise.
- `renderer.py` – draws particles and springs to the screen.
- `structures.py` – helper routines for building walls, rods and other shapes.
- `builder_ui.py` – sidebar UI widgets used by the interactive builder.
- `color_picker.py` – colour picker helper using Tkinter.
- `start_create.py` – interactive builder for constructing scenes.
- `start.py` – demo of a soft cell made from three circular walls.
- `start_basic.py` – minimal ring of particles demo.
- `start_rod.py` – capsule-like rod demonstration.
- `start_bending_wall.py` – triangular wall with bending springs.
- `start_hook_arm.py` – cell with a flexible hook arm.
- `start_four_rods.py` – four rod structures positioned around the centre.
- `start_gradient_wall.py` – four rods coloured with a gradient.

## Maintaining the project

- Provide clear docstrings for all modules, classes and functions.
- After **every** change, update both `README.md` and `AGENTS.md` so they remain accurate.
- Summarise new files or features here for future agents.
- Keep the README up to date with instructions on running the demos and any changed controls or dependencies.

There are no automated tests; run the demo scripts manually to verify behaviour.

## Recent updates

- High-drag particles render with a red outline to indicate adhesion.
- Press **C** in `start_hook_arm.py` to run a full extend/adhere/contract cycle.
