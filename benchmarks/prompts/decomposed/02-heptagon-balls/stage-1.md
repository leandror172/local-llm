Create a single HTML file with an 800x800 canvas showing ONLY a rotating heptagon (7-sided regular polygon).

Requirements:
- Heptagon centered on the canvas, radius 300px (from center to vertex)
- Rotates clockwise, completing exactly one full rotation every 5 seconds
- Use delta-time for rotation (track cumulative angle, not per-frame increment)
- Draw as a stroked polygon path (not filled), white or light color on dark background
- Compute vertices using: for i in 0..6: x = cx + R * cos(angle + i * 2π/7), y = cy + R * sin(angle + i * 2π/7)
- Close the path and stroke
- Use requestAnimationFrame
- Nothing else — no balls, no physics
