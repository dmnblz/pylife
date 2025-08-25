## Pylife: Architecture and Developer’s Guide

### What this project is
A compact, extensible 2D soft‑body sandbox built on pygame. It simulates particles connected by linear and angular constraints, with interaction tools for building scenes and saving/loading them. It includes demo scenes to showcase common setups.

---

## Installation

- Python 3.10+
- `pip install pygame`
- Optional: Tkinter (usually ships with Python) for the color/file pickers

---

## Quick start

### Interactive builder
- Run: `python start_create.py`
- Create circles, rods, variable springs/particles, bending springs, hook arms; tweak gravity, temperature, viscous damping, velocity damping, repulsion; save/load, undo.
- Number keys map to modes in the sidebar (1–0 in order). Buttons show their shortcuts.

### Demos
- `start.py`: 3 nested circular walls
- `start_basic.py`: minimal ring
- `start_rod.py`: capsule rod
- `start_bending_wall.py`: triangles + bending springs
- `start_hook_arm.py`: 4 flexible hook arms
- `start_four_rods.py` and `start_gradient_wall.py`: multiple rods

---

## Core simulation model

### Particles
Point masses with Verlet integration, optional drag multiplier and other render hints.

- Key attributes: `pos`, `prev_pos`, `acc`, `mass`, `fixed`, `drag`, `color`, `radius`, `tag`.

### Linear springs
Hooke’s law between two particles; optional break threshold and invisibility. Color encodes compression/extension via `Spring.get_color`.

### Bending springs
Maintain an angle at a vertex between three particles (`p1`–`p2`–`p3`).

### Variable elements
- `VariableSpring`: smoothly transitions between base and alternate rest lengths on a key press (hold or toggle), with adjustable speed.
- `VariableParticle`: smoothly transitions between base and alternate drag on a key press (hold or toggle), with adjustable speed.

### Physics engine
`PhysicsEngine.update(dt)` applies:
- gravity
- spring and bending forces
- particle‑particle short‑range repulsion
- velocity‑proportional viscous drag scaled by per‑particle `drag`
- Brownian noise
- Verlet integration and additional wall friction for particles near boundaries

Key files:
- `particle.py`
- `spring.py`
- `bending_spring.py`
- `physics.py`

---

## Rendering and camera

`renderer.py` supports world/screen transforms, zoom and rotation, and draws particles, springs, and bending springs. Compressed/extended springs are color‑coded; high‑drag particles get a red outline.
Right‑click and drag pans the view; middle‑click and drag rotates the camera around the center of the play area. Mouse wheel zooms around the cursor.

---

## Structures and helpers

`structures.py` creates common shapes:

- `create_wall`: circular wall with perimeter springs.
- `create_bending_wall`: circular wall plus a `BendingSpring` at every vertex using the polygon angle.
- `create_rod`: capsule (rectangle with semicircular ends). Options:
  - cytoskeleton (radial spokes across caps),
  - internal spine skeleton,
  - automatic connections from perimeter to skeleton.

All return particle and spring lists ready for simulation.

---

## Hook arms

`hook_arm.py` defines `HookArm`, a small chain attached to a base particle, with extension/contraction and a high‑drag adhesion phase for the tip. It can be cycled (extend → adhere → contract) and keyed. Tip adhesion multiplies mass and drag, and changes color for visibility.

---

## Interactive builder: UI and tools

The builder (`start_create.py`) manages the simulation and a sidebar of tools.

### Parameter dataclasses
`builder_ui/config.py` holds defaults for newly created objects and environment:
- `ParticleParams`, `SpringParams`, `VariableSpringParams`, `VariableParticleParams`, `EnvironmentParams`.

### Tools
- **Drag**: move particles.
- **Particle / VarPar**: place normal or variable particles.
- **Spring / VarSpr**: connect particles with linear or variable springs.
- **Bend**: add a `BendingSpring` by selecting three particles; auto/manual angle.
- **Circle**: preview/create a circle; optional bending springs; separate stiffness controls.
- **Rod**: preview/create capsules; optional bending springs, cytoskeleton, skeleton.
- **Arm**: attach a `HookArm`; configure mass, radius, stiffness, colors, adhesion factor, cycle speed, cycle key.
- **Inspect**: click an existing particle, spring, or bend to edit properties; convert between normal/variable; toggle spring visibility; set max force.
- **Grid**: toggle grid and spacing; creation snaps to intersections.
- **Env**: adjust gravity, repulsion radius/strength, viscous damping, velocity damping, temperature.
- **Delete**: remove closest particle or spring (undo supported).

### Sidebar/events
- Shared base `builder_ui/tools/base.py::Tool` handles active/visible checks and keeps mouse‑wheel zoom working over world space.
- Sidebar scrolls within bounds; buttons flash and show active state.

---

## Persistence: save/load format

`builder_io.py` serializes everything to JSON:
- Particles (position, prev position, mass, radius, color, fixed, tag, drag; for variable particles: base/alt drag, speed, key, mode, active, current drag).
- Springs (endpoints by index, rest, stiffness, max force, invisible; variable springs add base/alt rest, speed, key, mode, active, current rest).
- Bending springs (p1/p2/p3 indices, angle, stiffness).
- Hook arms (particle indices, spring indices, rest/max lengths, cycle speed, colors, adhesion, tip original mass/drag, cycle key).
- Physics globals (gravity, repulsion, temperature, viscous damping, velocity damping).

Loading rebuilds references and re‑registers variable elements and key bindings.

---

## Camera and world space

- Zoom and pan in world space, keeping the mouse anchor fixed while zooming.
- World play area is independent of window size; the physics engine also receives the screen size and play area for boundary effects.

---

## Extending the system

- New constraints/forces: add a module exposing `apply()` and have the engine call it per step; append instances to the app and assign to `physics`.
- New shapes: add a function to `structures.py` returning particles/springs; optionally add a builder tool for previews.
- New tools: subclass `builder_ui.tools.base.Tool`, render UI via `builder_ui/fields.py` components, implement `draw_preview` and `handle_event`; wire into `builder_ui/sidebar.py` and `BuilderApp.set_mode`.
- New visual cues: adjust `renderer.py` or per‑object attributes.

---

## Performance and stability tips

- Reduce particle count or spring density; tune `stiffness`, viscous `damping`, and `integration_damping` to avoid instability.
- Use `repulsion_radius` sparingly; it’s O(n^2).
- Consider breaking springs via `max_force` to avoid runaway configurations.
- For “sticky” effects, prefer raising `drag` instead of setting `fixed=True` during motion.

---

## API reference (selected)

- `Particle(position, mass=1.0, color=None, radius=None, tag=None, drag=1.0)`
- `Spring(p1, p2, rest_length, stiffness, max_force=None, invisible=False)`
- `BendingSpring(p1, p2, p3, rest_angle_rad, stiffness)`
- `VariableSpring(..., alt_rest_length, key=None, mode='hold'|'toggle', change_speed=..., ...)`
- `VariableParticle(..., base_drag=..., alt_drag=..., key=None, mode='hold'|'toggle', change_speed=...)`
- `PhysicsEngine(particles, springs, bending_springs=None, gravity=(0,0), repulsion_radius=..., repulsion_strength=..., temperature=..., damping_coeff=..., integration_damping=0.98, collision_bucket_size=...)`
  - `set_screen_size(w, h)`, `set_play_area(pygame.Rect)`, `update(dt)`

---

## Example: build a scene programmatically

```python
import pygame
from particle import Particle
from spring import Spring
from physics import PhysicsEngine
from renderer import Renderer

pygame.init()
screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
clock = pygame.time.Clock()

# Build a small ring
particles, springs = [], []
center = pygame.Vector2(500, 350)
radius, segments, k = 120, 40, 300
for i in range(segments):
    t = i / segments * 6.28318530718
    p = Particle(center + pygame.Vector2(radius * pygame.cos(t), radius * pygame.sin(t)), radius=6, color=(220,220,255))
    particles.append(p)
for i in range(segments):
    p1, p2 = particles[i], particles[(i+1)%segments]
    springs.append(Spring(p1, p2, (p2.pos - p1.pos).length(), stiffness=k))

max_r = max((p.radius for p in particles), default=0)
engine = PhysicsEngine(
    particles,
    springs,
    repulsion_radius=25,
    repulsion_strength=800,
    temperature=200,
    damping_coeff=1.0,
    integration_damping=0.98,
    collision_bucket_size=max_r * 2,
)
engine.set_screen_size(*screen.get_size())
renderer = Renderer(screen)

running = True
selected = None
while running:
    dt = clock.tick(120)/1000
    for e in pygame.event.get():
        if e.type == pygame.QUIT: running=False
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mouse = pygame.Vector2(e.pos)
            selected = min(particles, key=lambda p: (p.pos - mouse).length()); selected.fixed = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if selected: selected.fixed = False; selected = None
        elif e.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
            renderer.screen = screen; engine.set_screen_size(e.w, e.h)

    if selected:
        pos = pygame.Vector2(pygame.mouse.get_pos())
        selected.pos = pos; selected.prev_pos = pos

    engine.update(dt)
    renderer.draw_background(pygame.Rect(0, 0, *screen.get_size()))
    renderer.draw(particles, springs)
    pygame.display.flip()

pygame.quit()
```

---

## Troubleshooting

- Window resize glitches: update `renderer.screen` and `physics.set_screen_size`.
- Tkinter errors: disable color/file pickers or install a Python build with Tk.
- Jitter/instability: increase viscous damping, lower stiffness, adjust `integration_damping` (default 0.98, configurable in the builder), or reduce time step (increase FPS).

---

## Contributing

- Keep `README.md` and `AGENTS.md` aligned with changes.
- Add docstrings to new modules/classes/functions.
- Prefer small, focused modules and use dataclasses for user‑configurable defaults.
