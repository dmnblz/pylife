# Pylife

Pylife is a small collection of Python scripts for experimenting with 2D physics based "cell" simulations.  The project uses [pygame](https://www.pygame.org/) to render a set of particles connected by springs.  By combining simple physics rules the scripts can model soft bodies such as circular walls, rods and more complex shapes.

## Features

* **Interactive builder** – `start_create.py` opens a window where you can drag particles, connect them with springs and spawn predefined structures. A sidebar UI contains sliders to tweak parameters such as mass, radius, collision elasticity, spring stiffness and various environment settings like temperature, gravity, repulsion, viscous damping, velocity damping, collision toggling and optional particle trails with adjustable length. Older save files without these fields load with trails disabled. Tools exist for circles, rods, bending springs, flexible hook arms and sensor particles. The Sensor tool exposes range, half-angle, direction and colour sliders so every sensor property can be configured before placement, spawning yellow sensors by default. A Trigger button or dragging from a sensor (or pressing **T**) links another particle that activates the sensor when it enters the sensing radius, drawing a line to the cursor and highlighting the candidate. Inspect mode tweaks existing particles, springs, bends and sensors. Hovering in Inspect mode shows a tooltip with key properties. A Select tool can highlight multiple particles, springs, bending springs and hook arms via a drag rectangle; press Backspace/Delete to remove the highlighted items or **Ctrl+C**/**Ctrl+V** to copy and paste them. Circles and rods now have per-shape stiffness sliders and an option to add bending springs along their outline. Bending springs may use the current angle of the selected particles or a manual value and display a small arc between the connected segments indicating the bend direction during creation and afterwards. The arc highlights when hovered and can be clicked to inspect or edit the bend even when nearby springs overlap, and its orientation now accounts for the inverted screen y-axis so vertical bends render correctly. Arm creation now exposes mass, radius, colour, adhesion settings and cycle speed per arm. Particle, spring and environment controls each have their own button in the sidebar. Sidebar and menu buttons darken when clicked, highlight active tools or toggles and the sidebar scrolls with the mouse wheel but stops at the list bounds. The builder can also save or load the entire scene using sidebar buttons, an **Undo** button reverts the most recent change and a **Theme** button switches between light and dark palettes, recoloring the canvas, grid and HUD. The light palette has been tuned for softer contrasts, and the HUD draws on a translucent panel so the world remains visible beneath it. Undo operations now keep springs and bending springs functional thanks to a unified `remove_entities` helper. Variable springs offer two rest lengths switched by a user-defined key in hold or toggle mode, and save files retain their parameters and key bindings. Variable bending springs provide a second angle that can be activated via a key and smoothly transition at a configurable rate. Their arcs are colour-coded by angular stress, turning blue when compressed and red when stretched. A dedicated **Grid** tool toggles a grid overlay and lets you adjust its spacing; newly created particles snap to grid intersections while it is enabled. Snapping uses a `snap_to_grid` helper that leaves already aligned positions untouched. Internally, these options are grouped into small dataclasses for particles, springs and the environment, simplifying updates.
Press **F1** to toggle an on-screen help overlay listing common key controls.
Number keys **1–0** switch between the first ten sidebar tools in order and each button displays its shortcut. The Select tool is accessed with **Ctrl+S**. Internally, the builder now dispatches mouse and keyboard input through per‑mode handlers which are looked up from a small dictionary, simplifying the event logic. The delete tool now removes springs without crashing, inspecting springs no longer triggers errors, and converting springs between normal and variable types is stable.
* **Channel signalling** – Sensors and variable elements can share integer channels; a sensor activates all variable particles, springs and bends on its channel while the trigger remains in range. Channel numbers render next to these objects and hovering a sensor highlights everything on its channel. Channels supplement key control, leaving manual toggles intact.
* **Demo scenes** – other `start_*.py` files showcase different preset configurations (e.g. cell walls, rods or gradient walls).  They are good starting points for custom experiments.
* **Energy monitoring** – HUDs display total kinetic and spring potential energy; `PhysicsEngine.total_energy()` exposes the value for custom uses.
* **Modular codebase** – the core simulation is split into small modules:
  * `particle.py` – a point mass implemented with Verlet integration.
  * `spring.py` – linear springs that apply Hooke's law and change colour depending on stretch/compression.
  * `bending_spring.py` – maintains an angle between three particles.
  * `physics.py` – contains ``PhysicsEngine`` which integrates particles each
    frame.  The engine applies gravity, spring forces and short range
    repulsion with squared-distance checks to skip distant pairs, optional
    collision resolution with per-particle restitution using a spatial hash
    with a separate cell size, viscous drag scaled by each particle's
    ``drag`` multiplier and Brownian noise. It also exposes
    ``total_energy()`` to inspect kinetic and spring potential energy.
  * `renderer.py` – draws particles, springs and bending springs to the pygame window.
  * `structures.py` – helper functions to build shapes like circular walls or rods.
  * `builder_ui/` and `color_picker.py` – the sidebar widgets and the cross‑platform colour selection utility. Tools in this
    package inherit from a small :class:`Tool` base class that provides
    default lifecycle, drawing and event hooks, including a shared
    active/visibility check for event handling.
  * `builder_io.py` – save/load helpers for the interactive builder.
  * `sensor_particle.py` – particles with circular or sector sensing that
    invoke callbacks when tagged objects enter their view.
  * **High-drag adhesion** – increase a particle's ``drag`` attribute to make it
    stick in place. Values above ``1`` apply proportionally stronger damping.
  * **Weighted adhesion** – a ``HookArm`` tip also increases in mass when stuck
    for extra grip.
  * **Variable springs** – springs can switch between two rest lengths via a
    user-defined key.
* **Variable particles** – particles can switch between two drag values via a
  key in hold or toggle mode. Inspect mode can also convert existing particles
  to or from this type.
* **Variable bending springs** – bends can alternate between two angles via a
  key in hold or toggle mode. Their arcs tint blue when compressed and red when stretched. Stiffness
  sliders now reach 5000 for creating especially rigid bends.
  * **Developer-friendly** – comprehensive docstrings document the builder UI
    and creation script.
  * **Typed callbacks** – sidebar widgets declare explicit ``Callable``
    signatures for getters and setters, aiding static type checkers.
  * **Channel protocol** – variable elements conform to a shared
    ``ChannelControlled`` protocol exposing ``set_channel_active`` for
    type-safe channel signalling.
  * **Cached fonts** – sidebar and field widgets reuse the default pygame font
    to prevent leaking file descriptors on some systems.

### Using high-drag particles

Increasing a particle's ``drag`` attribute amplifies the damping force in
``PhysicsEngine.update``. Values greater than ``1`` make the particle stick and
are rendered with a red outline. ``HookArm`` also makes its tip heavier whenever
high drag is enabled. Demo scripts use this to simulate particles adhering to
their surroundings—press **B/N/M** in ``start_bending_wall.py`` or **H** in
``start_hook_arm.py`` to toggle the behaviour. Holding **W**, **A**, **S** or
**D** in ``start_hook_arm.py`` runs a loop that extends, sticks and retracts an
arm.

## Requirements

The scripts require Python 3 and the `pygame` package.  On most systems it can be installed with:

```bash
pip install pygame
```

Some features (the colour picker) use `tkinter` which is included with most Python installations.

## Installation and CLI usage

This repository bundles a small command line interface powered by
[Typer](https://typer.tiangolo.com/).  Install the extra dependency and
invoke the CLI to create new project directories or write configuration
files:

```bash
pip install typer
python -m pylife.cli create demo_project
python -m pylife.cli config demo_project/config.json
```

Tests can exercise the CLI via `CliRunner` from `typer.testing`.  See
`tests/test_cli.py` for small examples.

## Running the builder

```bash
python start_create.py
```

Mouse and keyboard controls allow you to switch modes and modify properties:

* **1** – drag existing particles
* **Ctrl+S** – select multiple particles or springs with a rectangle
* **2** – place new particles
* Use the **VarPar** button to create a particle with a controllable drag
  multiplier
* **3** – connect two particles with a spring
* Use the **VarSpr** button to link particles with a spring that can expand or
  contract when a chosen key is pressed
* **4** – create a bending spring from three particles
* Use the **VarBend** button to create a bending spring with a controllable
  alternate angle
* **5** – draw a circle of particles and springs
* **6** – create rod structures
* **7** – attach a hook arm to a particle
* **8** – inspect an existing particle, spring or bending spring. Hover a target to preview its key properties.
* **9** – toggle a grid overlay and adjust its spacing
* **0** – adjust environment settings (temperature, gravity, repulsion, viscous damping, velocity damping, collisions, particle trails, and the simulation field size)
* **Backspace/Delete** – remove selected particles, springs, bends and hook arms or switch to the Delete tool when nothing is selected
* **Ctrl+C** – copy selected particles, springs, bends and hook arms
* **Ctrl+V** – paste a copied selection, including hook arms
* **Space** – pause or resume the physics update
* **F1** – toggle an on-screen help panel with key controls
* Use the **Save** and **Load** buttons in the sidebar to export or import the
  current scene as a JSON file. Loaded scenes automatically resume simulation.
* Hit **Undo** in the sidebar to revert the most recent addition or deletion.
* Scroll the sidebar with the mouse wheel; scrolling stops at the list bounds.
* Right-click and drag – pan the camera view.
* Middle-click and drag – rotate the camera.

Particles can be grabbed with the left mouse button.  When in spring mode, click two particles to connect them. Selecting the **Arm** tool lets you click a particle, drag out a direction and then hit *Create* to spawn a hook arm. The sidebar fields let you set the arm's mass, radius, stiffness, cycle speed, colours and adhesion factor before creation, and any number of arms may share the same cycle key. The **Inspect** tool can select a particle, spring or bending spring so their properties (colour, mass, radius, elasticity, drag, rest length, stiffness, **max force** and visibility) may be edited in place. Springs and particles may also be converted between normal and variable types through this menu. A value of ``0`` for max force disables the limit. Use the Particle, Spring or Env buttons to reveal their respective sliders.

## Example demos

Other start files demonstrate specific setups and each window supports simple
keyboard shortcuts:

* **`start.py`** – three nested circular walls that behave like a soft cell.
  Press **O**/**P** to spawn loose particles, **K/L** to tweak spring
  stiffness, **N/M** to change the temperature and **Q/W** to freeze or unfreeze
  loose particles.
* **`start_basic.py`** – a minimal ring of particles.  Only dragging with the
  left mouse button is implemented.
* **`start_rod.py`** – shows a capsule‑shaped rod; controls are the same as in
  `start.py`.
* **`start_bending_wall.py`** – demonstrates bending springs.  Keys **D**, **F**
  and **G** temporarily shorten individual springs while **B**, **N** and **M**
  toggle high drag on selected particles.  All other controls from `start.py`
  are also available.
* **`start_hook_arm.py`** – showcases four flexible arms attached to a cell.
  Hold **E** to extend all arms, **Q** to retract them, press **H** to toggle
  adhesion on every tip or hold **W**, **A**, **S** or **D** to repeatedly
  extend, stick and contract an individual arm. High‑drag particles are
  highlighted in red.
* **`start_four_rods.py`** – four rods positioned around the centre with the
  same controls as `start.py`.
* **`start_gradient_wall.py`** – similar to `start_four_rods.py` but colours each
  rod with a gradient.

Feel free to modify any of these scripts or build new configurations using the interactive builder.

---

This repository is intended for learning and experimentation.  The code is small and easy to extend, so you can try out new physical behaviours or rendering ideas.

## Contributing

When modifying or adding code, keep the documentation aligned with the repository:

* Update `README.md` to describe new behaviour, scripts or changes in usage.
* Update `AGENTS.md` with a short description of any new files so future agents understand the project layout.
* Provide docstrings for new modules, classes and functions.
