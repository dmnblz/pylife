# Pylife

Pylife is a small collection of Python scripts for experimenting with 2D physics based "cell" simulations.  The project uses [pygame](https://www.pygame.org/) to render a set of particles connected by springs.  By combining simple physics rules the scripts can model soft bodies such as circular walls, rods and more complex shapes.

## Features

* **Interactive builder** – `start_create.py` opens a window where you can drag particles, connect them with springs and spawn predefined structures. A sidebar UI contains sliders to tweak parameters such as mass, radius, collision elasticity, spring stiffness and various environment settings like temperature, gravity, repulsion, damping and collision toggling. Tools exist for circles, rods, bending springs, flexible hook arms and an inspect mode for tweaking existing particles, springs and bends. A Select tool can highlight multiple particles, springs, bending springs and hook arms via a drag rectangle; press Backspace/Delete to remove the highlighted items or **C**/**V** to copy and paste them. Circles and rods now have per-shape stiffness sliders and an option to add bending springs along their outline. Bending springs may use the current angle of the selected particles or a manual value. Arm creation now exposes mass, radius, colour, adhesion settings and cycle speed per arm. Particle, spring and environment controls each have their own button in the sidebar. Sidebar and menu buttons darken when clicked, highlight active tools or toggles and the sidebar scrolls with the mouse wheel but stops at the list bounds. The builder can also save or load the entire scene using sidebar buttons, and an **Undo** button reverts the most recent change. Undo operations now keep springs and bending springs functional thanks to a unified `remove_entities` helper. Variable springs offer two rest lengths switched by a user-defined key in hold or toggle mode, and save files retain their parameters and key bindings. A dedicated **Grid** tool toggles a grid overlay and lets you adjust its spacing; newly created particles snap to grid intersections while it is enabled. Snapping uses a `snap_to_grid` helper that leaves already aligned positions untouched. Internally, these options are grouped into small dataclasses for particles, springs and the environment, simplifying updates.
Number keys **1–0** switch between the first ten sidebar tools in order and each button displays its shortcut. The Select tool is accessed with **S**. Internally, the builder now dispatches mouse and keyboard input through per‑mode handlers which are looked up from a small dictionary, simplifying the event logic. The delete tool now removes springs without crashing, inspecting springs no longer triggers errors, and converting springs between normal and variable types is stable.
* **Demo scenes** – other `start_*.py` files showcase different preset configurations (e.g. cell walls, rods or gradient walls).  They are good starting points for custom experiments.
* **Modular codebase** – the core simulation is split into small modules:
  * `particle.py` – a point mass implemented with Verlet integration.
  * `spring.py` – linear springs that apply Hooke's law and change colour depending on stretch/compression.
  * `bending_spring.py` – maintains an angle between three particles.
  * `physics.py` – contains ``PhysicsEngine`` which integrates particles each
    frame.  The engine applies gravity, spring forces, short range repulsion,
    optional collision resolution with per-particle restitution, viscous drag scaled by each
    particle's ``drag`` multiplier and Brownian noise.
  * `renderer.py` – draws particles, springs and bending springs to the pygame window.
  * `structures.py` – helper functions to build shapes like circular walls or rods.
  * `builder_ui/` and `color_picker.py` – the sidebar widgets and the cross‑platform colour selection utility. Tools in this
    package inherit from a small :class:`Tool` base class that provides
    default lifecycle, drawing and event hooks, including a shared
    active/visibility check for event handling.
  * `builder_io.py` – save/load helpers for the interactive builder.
  * **High-drag adhesion** – increase a particle's ``drag`` attribute to make it
    stick in place. Values above ``1`` apply proportionally stronger damping.
  * **Weighted adhesion** – a ``HookArm`` tip also increases in mass when stuck
    for extra grip.
  * **Variable springs** – springs can switch between two rest lengths via a
    user-defined key.
  * **Variable particles** – particles can switch between two drag values via a
    key in hold or toggle mode. Inspect mode can also convert existing particles
    to or from this type.
  * **Developer-friendly** – comprehensive docstrings document the builder UI
    and creation script.
  * **Typed callbacks** – sidebar widgets declare explicit ``Callable``
    signatures for getters and setters, aiding static type checkers.

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

## Running the builder

```bash
python start_create.py
```

Mouse and keyboard controls allow you to switch modes and modify properties:

* **1** – drag existing particles
* **S** – select multiple particles or springs with a rectangle
* **2** – place new particles
* Use the **VarPar** button to create a particle with a controllable drag
  multiplier
* **3** – connect two particles with a spring
* Use the **VarSpr** button to link particles with a spring that can expand or
  contract when a chosen key is pressed
* **4** – delete the particle or spring under the cursor
* **Backspace/Delete** – remove selected particles, springs, bends and hook arms or switch to the Delete tool when nothing is selected
* **5** – create rod structures
* **6** – attach a hook arm to a particle
* **7** – inspect an existing particle, spring or bending spring
* **8** – adjust environment settings (temperature, gravity, repulsion, damping and collisions)
* **9** – create a bending spring from three particles
* **C** – copy selected particles, springs, bends and hook arms or choose a colour for new particles when nothing is selected
* **Z/X** – decrease/increase particle mass
* **V** – paste a copied selection (including hook arms) or decrease particle radius when no copy exists
* **B** – increase particle radius
* **K/L** – decrease/increase spring stiffness
* **N/M** – decrease/increase simulation temperature
* **P** – pause or resume the physics update
* Use the **Grid** button in the sidebar to toggle a grid overlay and adjust its spacing. While active, new particles snap to the grid.
* Use the **Save** and **Load** buttons in the sidebar to export or import the
  current scene as a JSON file. Loaded scenes automatically resume simulation.
* Hit **Undo** in the sidebar to revert the most recent addition or deletion.
* Scroll the sidebar with the mouse wheel; scrolling stops at the list bounds.

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
