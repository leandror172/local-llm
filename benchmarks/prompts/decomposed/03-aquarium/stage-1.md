Create a single HTML file with a full-window canvas showing ONLY the static aquarium background elements.

Requirements:
- Canvas fills the entire browser window (resize handler)
- Background: vertical linear gradient from light blue (#87CEEB) at top to dark blue (#001a33) at bottom
- Sandy bottom: a horizontal band at the bottom 15% of the canvas, filled with a sandy color (#c2b280)
- Pebbles: generate 30 pebbles at initialization (NOT each frame) with random x positions along the sandy bottom, random sizes (3-8px radius), random gray/brown colors. Store them in an array and draw from the array each frame.
- Light rays: 5-7 translucent white triangles from the top of the canvas, angled slightly, with low opacity (0.03-0.06). Generate positions at initialization, stored in an array.
- Use requestAnimationFrame (even though nothing animates yet — this prepares for the next stage)
- No fish, no bubbles, no seaweed yet
