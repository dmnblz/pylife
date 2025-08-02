"""Tool for previewing and creating rod-like structures."""

import math
import pygame

from ..fields import SliderField


class RodTool:
    """Handle rod preview creation with sliders and click placement."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False
        self.center = None
        self.radius = 30.0
        self.length = 100.0
        self.segments = 20
        self.skeleton_count = 5
        self.include_cytoskeleton = False
        self.include_skeleton = False
        self.dragging = False
        self.stiffness = 200.0
        self.bend_stiffness = 200.0
        self.include_bend = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.radius_field = SliderField(
            "R Radius", 5, 200, lambda: self.radius, self._set_radius, x, y, width
        )
        y += 40
        self.length_field = SliderField(
            "Length", 10, 600, lambda: self.length, self._set_length, x, y, width
        )
        y += 40
        self.segments_field = SliderField(
            "Segments", 4, 200, lambda: self.segments, self._set_segments, x, y, width
        )
        y += 40
        self.skel_count_field = SliderField(
            "Skeleton", 1, 20, lambda: self.skeleton_count, self._set_skel_count, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiff, x, y, width
        )
        y += 40
        self.bend_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)
        y += self.sidebar.BUTTON_HEIGHT + 4
        self.bstiff_field = SliderField(
            "BStiff", 10, 1000, lambda: self.bend_stiffness, self._set_bstiff, x, y, width
        )
        y += 40
        self.cyto_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)
        y += self.sidebar.BUTTON_HEIGHT + 4
        self.skeleton_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)
        y += self.sidebar.BUTTON_HEIGHT + 4
        self.create_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)

    # ---------------- value setters
    def _set_radius(self, value: float):
        self.radius = max(1, value)

    def _set_length(self, value: float):
        self.length = max(1, value)

    def _set_segments(self, value: float):
        self.segments = max(4, int(value))

    def _set_skel_count(self, value: float):
        self.skeleton_count = max(1, int(value))

    def _set_stiff(self, value: float):
        self.stiffness = max(10, value)

    def _set_bstiff(self, value: float):
        self.bend_stiffness = max(10, value)

    # ---------------- control
    def start(self):
        self.active = True
        self.center = None

    def cancel(self):
        self.active = False
        self.dragging = False

    # ---------------- helpers
    def _generate_points(self):
        center = self.center
        if center is None:
            return []
        radius = self.radius
        length = self.length
        segments = self.segments
        pts = []
        total_length = 2 * length + 2 * math.pi * radius
        step = total_length / segments
        center_left = center + pygame.Vector2(-length / 2, 0)
        center_right = center + pygame.Vector2(length / 2, 0)
        for i in range(segments):
            s = i * step
            if s < math.pi * radius:
                theta = math.pi / 2 + (s / (math.pi * radius)) * math.pi
                pos = center_left + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            elif s < math.pi * radius + length:
                pos = pygame.Vector2(center_left.x + (s - math.pi * radius), center.y - radius)
            elif s < 2 * math.pi * radius + length:
                theta = 3 * math.pi / 2 + ((s - math.pi * radius - length) / (math.pi * radius)) * math.pi
                pos = center_right + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            else:
                pos = pygame.Vector2(
                    center_right.x - (s - 2 * math.pi * radius - length), center.y + radius
                )
            pts.append(self.app.snap_to_grid(pos))
        return pts

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.radius_field.draw(self.sidebar.screen)
        self.length_field.draw(self.sidebar.screen)
        self.segments_field.draw(self.sidebar.screen)
        self.skel_count_field.draw(self.sidebar.screen)
        self.stiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.bend_rect)
        bend_txt = "Bend: On" if self.include_bend else "Bend: Off"
        txt = self.sidebar.font.render(bend_txt, True, (255, 255, 255))
        rect = txt.get_rect(center=self.bend_rect.center)
        self.sidebar.screen.blit(txt, rect)
        if self.include_bend:
            self.bstiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.cyto_rect)
        cyto_txt = "Cytoskeleton" if self.include_cytoskeleton else "No Cytoskeleton"
        txt = self.sidebar.font.render(cyto_txt, True, (255, 255, 255))
        rect = txt.get_rect(center=self.cyto_rect.center)
        self.sidebar.screen.blit(txt, rect)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.skeleton_rect)
        skel_txt = "Skeleton" if self.include_skeleton else "No Skeleton"
        txt = self.sidebar.font.render(skel_txt, True, (255, 255, 255))
        rect = txt.get_rect(center=self.skeleton_rect.center)
        self.sidebar.screen.blit(txt, rect)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        """Draw the rod preview at the current mouse position."""
        if not self.active or self.center is None:
            return

        screen = self.sidebar.screen
        color = (150, 150, 150)
        pts = self._generate_points()
        for i in range(len(pts)):
            p1 = pts[i]
            p2 = pts[(i + 1) % len(pts)]
            pygame.draw.line(screen, color, p1, p2, 1)
            pygame.draw.circle(screen, color, (int(p1.x), int(p1.y)), self.app.radius, 1)

        if self.include_cytoskeleton:
            total_length = 2 * self.length + 2 * math.pi * self.radius
            step = total_length / self.segments
            n_arc = int(round((math.pi * self.radius) / step))
            n_side = self.segments - 2 * n_arc

            bottom_y = self.center.y - self.radius
            top_y = self.center.y + self.radius
            bottom_nodes = [
                p
                for p in pts
                if abs(p.y - bottom_y) < 1e-6
                and (self.center.x - self.length / 2) < p.x < (self.center.x + self.length / 2)
            ]
            top_nodes = [
                p
                for p in pts
                if abs(p.y - top_y) < 1e-6
                and (self.center.x - self.length / 2) < p.x < (self.center.x + self.length / 2)
            ]
            bottom_nodes.sort(key=lambda p: p.x)
            top_nodes.sort(key=lambda p: p.x)
            for b, t in zip(bottom_nodes, top_nodes):
                pygame.draw.line(screen, color, b, t, 1)

            for i in range(n_arc // 2):
                pygame.draw.line(screen, color, pts[i], pts[n_arc - 1 - i], 1)

            start = n_arc + n_side
            for i in range(n_arc // 2):
                pygame.draw.line(screen, color, pts[start + i], pts[start + n_arc - 1 - i], 1)

        if self.include_skeleton:
            skeleton_pts = []
            center_left = self.center + pygame.Vector2(-self.length / 2, 0)
            for k in range(self.skeleton_count):
                t = k / (self.skeleton_count - 1) if self.skeleton_count > 1 else 0.5
                pos = center_left + pygame.Vector2(self.length * t, 0)
                skeleton_pts.append(pos)

            for i in range(len(skeleton_pts) - 1):
                pygame.draw.line(screen, color, skeleton_pts[i], skeleton_pts[i + 1], 1)

            eps = 1e-6
            for p in pts:
                if abs(p.y - (self.center.y - self.radius)) < eps or abs(p.y - (self.center.y + self.radius)) < eps:
                    dists = sorted(((sp - p).length(), sp) for sp in skeleton_pts)
                    for _, sp in dists[:2]:
                        pygame.draw.line(screen, color, p, sp, 1)
                else:
                    sp = min(skeleton_pts, key=lambda sp: (sp - p).length())
                    pygame.draw.line(screen, color, p, sp, 1)

            for sp in skeleton_pts:
                pygame.draw.circle(screen, color, (int(sp.x), int(sp.y)), self.app.radius, 1)

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False

        if self.sidebar.visible:
            if self.radius_field.handle_event(event):
                return True
            if self.length_field.handle_event(event):
                return True
            if self.segments_field.handle_event(event):
                return True
            if self.skel_count_field.handle_event(event):
                return True
            if self.stiff_field.handle_event(event):
                return True
            if self.include_bend and self.bstiff_field.handle_event(event):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.bend_rect.collidepoint(event.pos):
                    self.include_bend = not self.include_bend
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.cyto_rect.collidepoint(event.pos):
                    self.include_cytoskeleton = not self.include_cytoskeleton
                    return True
                if self.skeleton_rect.collidepoint(event.pos):
                    self.include_skeleton = not self.include_skeleton
                    return True
                if self.create_rect.collidepoint(event.pos) and self.center:
                    self.app.create_rod(
                        self.center,
                        self.radius,
                        self.length,
                        self.segments,
                        self.include_cytoskeleton,
                        self.include_skeleton,
                        self.skeleton_count,
                        self.stiffness,
                        self.include_bend,
                        self.bend_stiffness,
                    )
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                self.center = self.app.snap_to_grid(pygame.Vector2(event.pos))
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse = self.app.snap_to_grid(pygame.Vector2(event.pos))
            self.length = abs(mouse.x - self.center.x) * 2
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        return False
