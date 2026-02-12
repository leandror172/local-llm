---
id: ex-03-canvas-mouse-follow
category: visual
type: few-shot-example
demonstrates: addEventListener (not inline), lerp smoothing, unique var names
---

## Task

Circle smoothly following the mouse cursor.

## Input

Create a single HTML file with a circle that smoothly follows the mouse cursor on a 600x400 canvas. Use linear interpolation for smooth movement and addEventListener for input handling.

## Output

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mouse Follow</title>
    <style>
        body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: #111; }
        canvas { border: 1px solid #333; cursor: none; }
    </style>
</head>
<body>
<canvas id="c" width="600" height="400"></canvas>
<script>
    const canvas = document.getElementById('c');
    const ctx = canvas.getContext('2d');

    let mouseX = canvas.width / 2;
    let mouseY = canvas.height / 2;
    let followerX = mouseX;
    let followerY = mouseY;
    const followerRadius = 15;
    const lerpFactor = 0.08;

    canvas.addEventListener('mousemove', function(event) {
        const rect = canvas.getBoundingClientRect();
        mouseX = event.clientX - rect.left;
        mouseY = event.clientY - rect.top;
    });

    function lerp(current, target, factor) {
        return current + (target - current) * factor;
    }

    function draw() {
        followerX = lerp(followerX, mouseX, lerpFactor);
        followerY = lerp(followerY, mouseY, lerpFactor);

        ctx.fillStyle = '#111';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.beginPath();
        ctx.arc(followerX, followerY, followerRadius, 0, Math.PI * 2);
        ctx.fillStyle = '#f84';
        ctx.fill();

        requestAnimationFrame(draw);
    }

    requestAnimationFrame(draw);
</script>
</body>
</html>
```
