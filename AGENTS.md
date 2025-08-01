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
- `file_dialog.py` – opens save/load dialogs in a separate process.
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
- `hook_arm.py` defines a reusable `HookArm` helper class.
- `start_hook_arm.py` now features four arms; hold **W**, **A**, **S** or **D** to
  run a continuous extend/adhere/contract cycle on the corresponding arm.
- The hook arm's tip becomes heavier while ``"high_drag"`` is active.
- `start_create.py` and `builder_ui.py` now let you attach hook arms and assign a
  key for cycling them.
- Multiple hook arms can listen to the same cycle key.
- A new **Inspect** mode lets you click a particle and modify its mass, radius
  and colour through the sidebar.
- Inspect mode can now select springs to edit rest length, stiffness,
  max force and visibility.
- The hook arm builder exposes fields for mass, radius, stiffness, colours and
  adhesion factor per arm.
- Inspect tool uses ``0`` for spring max force to disable the limit and avoid errors.
- Particle colour/mass/radius sliders and the spring stiffness slider only appear when their creation modes are active.
- Particle, spring and environment controls now live behind separate sidebar buttons.
- Hook arm creation now has a cycle speed slider controlling how fast the arm extends and retracts.
- The environment tool exposes sliders for gravity, repulsion and damping in addition to temperature.
- Bending springs can now be created in the builder by selecting three particles.
  They render as yellow dashed hinges and their rest angle and stiffness are editable.
- A toggle lets bending springs use the current angle of the selected particles
  or a manual value. Inspect mode can modify their angle and stiffness later.
- Builder sidebar now has **Save** and **Load** buttons for exporting and
  importing scene states.
- Loading a saved scene now refreshes the physics engine so simulations resume.
