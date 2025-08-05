from __future__ import annotations

"""Command line interface for the scene builder.

This module exposes a :func:`main` function that parses command line
arguments and performs scene operations without launching the pygame GUI.
It relies on :class:`builder_core.SceneBuilder` so the same creation logic is
shared with :mod:`start_create`.
"""

import argparse
from typing import Sequence

import pygame

from builder_core import SceneBuilder


def _parse_color(values: Sequence[int] | None) -> tuple[int, int, int] | None:
    """Convert a sequence of integers to an RGB tuple."""
    if values is None:
        return None
    return tuple(int(v) for v in values)  # type: ignore[return-value]


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(description="Headless scene builder")
    parser.add_argument("--input", help="Scene JSON to load before running")
    parser.add_argument(
        "--output", help="Path to write the resulting scene", default=None
    )
    sub = parser.add_subparsers(dest="cmd")

    # --- scene creation -------------------------------------------------
    p = sub.add_parser("add-particle", help="Add a particle")
    p.add_argument("x", type=float)
    p.add_argument("y", type=float)
    p.add_argument("--mass", type=float, default=1.0)
    p.add_argument("--radius", type=float, default=5.0)
    p.add_argument("--color", type=int, nargs=3)
    p.add_argument("--drag", type=float, default=1.0)

    vp = sub.add_parser("add-variable-particle", help="Add a variable particle")
    vp.add_argument("x", type=float)
    vp.add_argument("y", type=float)
    vp.add_argument("--mass", type=float, default=1.0)
    vp.add_argument("--radius", type=float, default=5.0)
    vp.add_argument("--color", type=int, nargs=3)
    vp.add_argument("--base-drag", type=float, default=1.0)
    vp.add_argument("--alt-drag", type=float, default=100.0)
    vp.add_argument("--key", type=int)
    vp.add_argument("--mode", choices=["hold", "toggle"], default="hold")
    vp.add_argument("--speed", type=float, default=240.0)

    s = sub.add_parser("add-spring", help="Connect two particles")
    s.add_argument("p1", type=int)
    s.add_argument("p2", type=int)
    s.add_argument("--rest", type=float)
    s.add_argument("--stiffness", type=float, default=200.0)
    s.add_argument("--max-force", type=float)
    s.add_argument("--invisible", action="store_true")

    vs = sub.add_parser("add-variable-spring", help="Variable length spring")
    vs.add_argument("p1", type=int)
    vs.add_argument("p2", type=int)
    vs.add_argument("--rest", type=float, required=True)
    vs.add_argument("--alt-rest", type=float, required=True)
    vs.add_argument("--stiffness", type=float, default=200.0)
    vs.add_argument("--key", type=int)
    vs.add_argument("--mode", choices=["hold", "toggle"], default="hold")
    vs.add_argument("--speed", type=float, default=240.0)
    vs.add_argument("--max-force", type=float)
    vs.add_argument("--invisible", action="store_true")

    b = sub.add_parser("add-bending-spring", help="Add a bending spring")
    b.add_argument("p1", type=int)
    b.add_argument("p2", type=int)
    b.add_argument("p3", type=int)
    b.add_argument("--angle", type=float, required=True)
    b.add_argument("--stiffness", type=float, default=100.0)

    c = sub.add_parser("add-circle", help="Create a circular wall")
    c.add_argument("x", type=float)
    c.add_argument("y", type=float)
    c.add_argument("--radius", type=float, default=50.0)
    c.add_argument("--segments", type=int, default=8)
    c.add_argument("--stiffness", type=float, default=200.0)
    c.add_argument("--bending", action="store_true")
    c.add_argument("--bend-stiffness", type=float, default=200.0)

    r = sub.add_parser("add-rod", help="Create a rod structure")
    r.add_argument("x", type=float)
    r.add_argument("y", type=float)
    r.add_argument("--radius", type=float, default=30.0)
    r.add_argument("--length", type=float, default=100.0)
    r.add_argument("--segments", type=int, default=20)
    r.add_argument("--stiffness", type=float, default=200.0)
    r.add_argument("--bending", action="store_true")
    r.add_argument("--bend-stiffness", type=float, default=200.0)
    r.add_argument("--cytoskeleton", action="store_true")
    r.add_argument("--skeleton", action="store_true")
    r.add_argument("--skeleton-count", type=int, default=5)

    ha = sub.add_parser("add-hook-arm", help="Attach a hook arm")
    ha.add_argument("base", type=int)
    ha.add_argument("--dx", type=float, default=1.0)
    ha.add_argument("--dy", type=float, default=0.0)
    ha.add_argument("--segments", type=int, default=3)
    ha.add_argument("--spacing", type=float, default=20.0)
    ha.add_argument("--mass", type=float, default=0.5)
    ha.add_argument("--radius", type=float, default=8.0)
    ha.add_argument("--stiffness", type=float, default=500.0)
    ha.add_argument("--color", type=int, nargs=3, default=(0, 150, 255))
    ha.add_argument("--high-color", type=int, nargs=3, default=(255, 50, 50))
    ha.add_argument("--adhesion", type=float, default=10.0)
    ha.add_argument("--cycle-key", type=int)
    ha.add_argument("--cycle-speed", type=float, default=240.0)

    # --- environment ---------------------------------------------------
    g = sub.add_parser("set-gravity", help="Set gravity vector")
    g.add_argument("x", type=float)
    g.add_argument("y", type=float)

    d = sub.add_parser("set-damping", help="Set damping coefficient")
    d.add_argument("value", type=float)

    rep = sub.add_parser("set-repulsion", help="Set repulsion radius/strength")
    rep.add_argument("radius", type=float)
    rep.add_argument("strength", type=float)

    temp = sub.add_parser("set-temperature", help="Set simulation temperature")
    temp.add_argument("value", type=float)

    grid = sub.add_parser("set-grid", help="Configure grid snapping")
    grid.add_argument("--size", type=float, default=40.0)
    grid.add_argument("--enable", action="store_true")
    grid.add_argument("--disable", action="store_true")

    # --- file and simulation ------------------------------------------
    sub.add_parser("undo", help="Undo last operation")
    save = sub.add_parser("save", help="Save state to file")
    save.add_argument("path")
    load = sub.add_parser("load", help="Load state from file")
    load.add_argument("path")
    run = sub.add_parser("run", help="Advance simulation")
    run.add_argument("--steps", type=int, default=60)
    run.add_argument("--dt", type=float, default=1 / 60)
    sub.add_parser("stop", help="Pause the simulation")

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point used by ``if __name__ == '__main__'``."""
    parser = build_parser()
    args = parser.parse_args(argv)

    builder = SceneBuilder()
    if args.input:
        builder.load(args.input)

    cmd = args.cmd
    if cmd == "add-particle":
        builder.add_particle(
            (args.x, args.y),
            mass=args.mass,
            radius=args.radius,
            color=_parse_color(args.color),
            drag=args.drag,
        )
    elif cmd == "add-variable-particle":
        builder.add_variable_particle(
            (args.x, args.y),
            mass=args.mass,
            radius=args.radius,
            color=_parse_color(args.color),
            base_drag=args.base_drag,
            alt_drag=args.alt_drag,
            key=args.key,
            mode=args.mode,
            change_speed=args.speed,
        )
    elif cmd == "add-spring":
        builder.add_spring(
            args.p1,
            args.p2,
            rest_length=args.rest,
            stiffness=args.stiffness,
            max_force=args.max_force,
            invisible=args.invisible,
        )
    elif cmd == "add-variable-spring":
        builder.add_variable_spring(
            args.p1,
            args.p2,
            rest_length=args.rest,
            alt_rest_length=args.alt_rest,
            stiffness=args.stiffness,
            key=args.key,
            mode=args.mode,
            change_speed=args.speed,
            max_force=args.max_force,
            invisible=args.invisible,
        )
    elif cmd == "add-bending-spring":
        builder.add_bending_spring(
            args.p1, args.p2, args.p3, angle=args.angle, stiffness=args.stiffness
        )
    elif cmd == "add-circle":
        builder.create_circle(
            pygame.Vector2(args.x, args.y),
            args.radius,
            args.segments,
            args.stiffness,
            args.bending,
            args.bend_stiffness,
        )
    elif cmd == "add-rod":
        builder.create_rod(
            pygame.Vector2(args.x, args.y),
            args.radius,
            args.length,
            args.segments,
            args.cytoskeleton,
            args.skeleton,
            args.skeleton_count,
            args.stiffness,
            args.bending,
            args.bend_stiffness,
        )
    elif cmd == "add-hook-arm":
        direction = pygame.Vector2(args.dx, args.dy)
        builder.create_hook_arm(
            builder.particles[args.base],
            direction,
            args.segments,
            args.spacing,
            args.mass,
            args.radius,
            args.stiffness,
            _parse_color(args.color),
            _parse_color(args.high_color),
            args.adhesion,
            args.cycle_key,
            args.cycle_speed,
        )
    elif cmd == "set-gravity":
        builder.set_gravity(args.x, args.y)
    elif cmd == "set-damping":
        builder.set_damping(args.value)
    elif cmd == "set-repulsion":
        builder.set_repulsion(args.radius, args.strength)
    elif cmd == "set-temperature":
        builder.set_temperature(args.value)
    elif cmd == "set-grid":
        builder.set_grid(not args.disable if args.enable or args.disable else builder.grid_enabled, args.size)
    elif cmd == "undo":
        builder.undo()
    elif cmd == "save":
        builder.save(args.path)
        return
    elif cmd == "load":
        builder.load(args.path)
    elif cmd == "run":
        builder.run(args.steps, args.dt)
    elif cmd == "stop":
        builder.stop()
    else:
        parser.print_help()
        return

    out = args.output or args.input
    if out:
        builder.save(out)


if __name__ == "__main__":
    main()
