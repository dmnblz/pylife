# Pylife

Pylife is a small collection of Python scripts for experimenting with 2D physics based "cell" simulations.  The project uses [pygame](https://www.pygame.org/) to render a set of particles connected by springs.  By combining simple physics rules the scripts can model soft bodies such as circular walls, rods and more complex shapes.

## Features

* **Interactive builder** – `start_create.py` opens a window where you can drag particles, connect them with springs and spawn predefined structures.  A sidebar UI contains sliders to tweak parameters such as mass, radius, spring stiffness and temperature.
* **Demo scenes** – other `start_*.py` files showcase different preset configurations (e.g. cell walls, rods or gradient walls).  They are good starting points for custom experiments.
* **Modular codebase** – the core simulation is split into small modules:
  * `particle.py` – a point mass implemented with Verlet integration.
  * `spring.py` – linear springs that apply Hooke's law and change colour depending on stretch/compression.
  * `bending_spring.py` – maintains an angle between three particles.
  * `physics.py` – contains ``PhysicsEngine`` which integrates particles each
    frame.  The engine applies gravity, spring forces, short range repulsion,
    viscous drag (with extra drag for particles tagged ``"high_drag"``) and
    Brownian noise.
  * `renderer.py` – draws particles and springs to the pygame window.
  * `structures.py` – helper functions to build shapes like circular walls or rods.
  * `builder_ui.py` and `color_picker.py` – the sidebar widgets and the cross‑platform colour selection utility.

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
* **2** – place new particles
* **3** – connect two particles with a spring
* **4** – delete the particle or spring under the cursor
* **5** – create rod structures
* **C** – choose a colour for newly created particles
* **Z/X** – decrease/increase particle mass
* **V/B** – decrease/increase particle radius
* **K/L** – decrease/increase spring stiffness
* **N/M** – decrease/increase simulation temperature
* **P** – pause or resume the physics update

Particles can be grabbed with the left mouse button.  When in spring mode, click two particles to connect them.

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
* **`start_four_rods.py`** – four rods positioned around the centre with the
  same controls as `start.py`.
* **`start_gradient_wall.py`** – similar to `start_four_rods.py` but colours each
  rod with a gradient.

Feel free to modify any of these scripts or build new configurations using the interactive builder.

---

This repository is intended for learning and experimentation.  The code is small and easy to extend, so you can try out new physical behaviours or rendering ideas.
