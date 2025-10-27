import random
import json, math, sys, colorsys
from pathlib import Path
import pygame

G = 1.0
def clamp(x, a, b): return max(a, min(b, x))

def load_or_create_state(state_file: Path):
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    default_state = {
        "window": {"width": 1000, "height": 1000, "fps": 120, "bg_color": [36, 36, 38]},
        "sun": {"mass": 26000.0, "radius": 20, "color": [245, 222, 140]},
        "time": {"dt": 1/60, "time_scale": 10.0},
        "common_hue": 0.62,
        "planets": []
    }
    rng = random.Random(42)
    radii = [140, 210, 280, 360, 420, 470]
    for i, r in enumerate(radii):
        density = rng.uniform(1.2, 12.0)
        default_state["planets"].append({
            "name": f"P{i+1}",
            "radius": rng.randint(9, 22),
            "density": density,
            "orbit_radius": r + rng.uniform(-10, 10),
            "phase": rng.uniform(0, 2*math.pi)
        })
    for i in range(6):
        density = rng.uniform(1.2, 12.0)
        default_state["planets"].append({
            "name": f"M{i+1}",
            "radius": rng.randint(6, 12),
            "density": density,
            "orbit_radius": rng.uniform(170, 520),
            "phase": rng.uniform(0, 2*math.pi)
        })
    for i in range(18):
        density = rng.uniform(1.2, 12.0)
        default_state["planets"].append({
            "name": f"A{i+1}",
            "radius": rng.randint(2, 4),
            "density": density,
            "orbit_radius": rng.uniform(120, 520),
            "phase": rng.uniform(0, 2*math.pi)
        })
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(default_state, f, ensure_ascii=False, indent=2)
    return default_state

class Planet:
    def __init__(self, cfg, sun_mass, center, hue):
        self.name = cfg["name"]
        self.radius = int(cfg["radius"])
        self.density = float(cfg["density"])
        self.orbit_radius = float(cfg["orbit_radius"])
        self.phase = float(cfg.get("phase", 0.0))
        self.cx, self.cy = center
        self.hue = float(hue)

        self.x = self.cx + self.orbit_radius * math.cos(self.phase)
        self.y = self.cy + self.orbit_radius * math.sin(self.phase)

        v = math.sqrt(G * sun_mass / max(self.orbit_radius, 1e-6))
        self.vx = v * -math.sin(self.phase)
        self.vy = v *  math.cos(self.phase)

        self.trail = []
        self.trail_max_len = 120 if self.radius >= 5 else 60

    def color_rgb(self):
        dens_min, dens_max = 1.0, 12.0
        s = (self.density - dens_min) / (dens_max - dens_min)
        s = clamp(s, 0.05, 0.98)
        r, g, b = colorsys.hsv_to_rgb(self.hue, s, 0.90)
        return int(r*255), int(g*255), int(b*255)

    def update(self, sun_mass, center, dt):
        cx, cy = center
        dx, dy = cx - self.x, cy - self.y
        r2 = dx*dx + dy*dy
        r = math.sqrt(r2) + 1e-9
        a = G * sun_mass / (r*r)
        ax, ay = a*dx/r, a*dy/r
        self.vx += ax*dt; self.vy += ay*dt
        self.x += self.vx*dt; self.y += self.vy*dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.trail_max_len: self.trail.pop(0)

    def draw(self, surf):
        if self.radius >= 5:
            for i, (tx, ty) in enumerate(self.trail):
                pygame.draw.circle(surf, self.color_rgb(), (int(tx), int(ty)), 1)
        pygame.draw.circle(surf, self.color_rgb(), (int(self.x), int(self.y)), self.radius)

    def draw_orbit_guide(self, surf, center, color=(90, 90, 95)):
        pygame.draw.circle(surf, color, (int(center[0]), int(center[1])), int(self.orbit_radius), 1)

def main():
    root = Path(__file__).resolve().parent
    state = load_or_create_state(root / "initial_state.json")

    W, H = int(state["window"]["width"]), int(state["window"]["height"])
    fps = int(state["window"]["fps"])
    bg = tuple(state["window"]["bg_color"])
    dt = float(state["time"]["dt"]) * float(state["time"]["time_scale"])

    sun_mass = float(state["sun"]["mass"])
    sun_rad = int(state["sun"]["radius"])
    sun_color = tuple(state["sun"]["color"])
    hue = float(state.get("common_hue", 0.62))
    center = (W//2, H//2)

    pygame.init()
    pygame.display.set_caption("Planetary System — Variant 1 (improved)")
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    planets = [Planet(p, sun_mass, center, hue) for p in state["planets"]]

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
        for pl in planets: pl.update(sun_mass, center, dt)

        screen.fill(bg)
        for pl in planets: pl.draw_orbit_guide(screen, center)
        pygame.draw.circle(screen, sun_color, center, sun_rad)
        for pl in planets: pl.draw(screen)

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit(); sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Runtime error:", e)
        pygame.quit(); sys.exit(1)
