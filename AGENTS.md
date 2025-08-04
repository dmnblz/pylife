# Agent Guidelines

This repository contains small pygame demos for 2D particle-based physics simulations. Each script showcases a particular setup built from particles and springs.

## File overview

- `particle.py` – Particle class using Verlet integration.
- `spring.py` – linear spring connecting two particles.
- `variable_spring.py` – spring variant with a user-controlled second rest length.
- `bending_spring.py` – bending constraint that keeps an angle between three particles.
- `physics.py` – `PhysicsEngine` that applies forces, drag and Brownian noise.
- `renderer.py` – draws particles and springs to the screen.
- `structures.py` – helper routines for building walls, rods and other shapes.
- `builder_ui/` – sidebar UI widgets used by the interactive builder.
- `color_picker.py` – colour picker helper using Tkinter.
- `file_dialog.py` – opens save/load dialogs in a separate process.
- `builder_io.py` – helper functions to save or load builder scenes.
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

- Particles with ``drag`` > 1 render with a red outline to indicate adhesion.
- `hook_arm.py` defines a reusable `HookArm` helper class.
- `start_hook_arm.py` now features four arms; hold **W**, **A**, **S** or **D** to
  run a continuous extend/adhere/contract cycle on the corresponding arm.
- The hook arm's tip becomes heavier while high drag is active.
- `start_create.py` and the `builder_ui` package now let you attach hook arms and assign a
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
- Save/load logic now lives in a new ``builder_io`` module.
- Circle and rod tools now expose spring stiffness sliders and can add bending springs along their outline.
- A new **Grid** tool can overlay a configurable grid; enabling it snaps new particles to the nearest intersection.
- Sidebar includes an **Undo** button to revert the most recent change.
- Rod tool preview now renders correctly through a dedicated `draw_preview` method.
- Builder tools now share a common `Tool` base class providing default
  `start`, `cancel`, drawing and event hooks to reduce boilerplate.
- Builder event handling uses per-mode handler methods looked up from a dispatch dictionary, simplifying `start_create.py`.
- Particle, spring and environment parameters now reside in ``builder_ui/config.py``
  dataclasses, and the builder updates these structures directly instead of
  using individual setter methods.
- Comprehensive docstrings added across builder tools and the main builder app.
- Unified ``remove_entities`` helper deletes particles, springs, bending springs
  and arms without breaking subsequent undo operations.
- Tool base class now performs active/visibility checks in ``handle_event``,
  removing duplicate logic from individual tools.
- Sidebar field callbacks now use explicit ``Callable`` type hints for more
  reliable static checking.
- Particles now carry an individual ``drag`` coefficient. A new
  ``VariableParticle`` subclass toggles between two drag values via a key,
  and the builder supports creating and saving these particles.
- Inspect mode recognises variable particles and can convert particles
  between normal and variable drag types.
- `snap_to_grid` now leaves already aligned coordinates unchanged and is used
  throughout `start_create.py` for grid snapping.
- Number keys 1–0 now select sidebar tools in order, and button labels display
  the corresponding shortcut.
- Variable springs provide two rest lengths controlled by a user key in hold
  or toggle mode. Inspect mode can modify their lengths, speed, key and mode.
- Delete tool no longer crashes when removing springs.
- Saving and loading scenes now keep variable spring parameters and key bindings.
- Inspect mode can convert normal springs to variable springs and back, and
  spring fields in the sidebar align correctly. Inspecting springs no longer
  crashes after fixing slider positioning.
- Converting a normal spring to a variable spring through the Inspect tool no
  longer raises an exception.
- Sidebar buttons darken briefly when clicked and highlight the active tool.
- The sidebar supports mouse-wheel scrolling to access overflow options.
- Scrolling now stops at the top and bottom of the content to avoid losing the
  sidebar's current context.
- Tool menu buttons darken when clicked and highlight active toggles for clearer
  feedback.
