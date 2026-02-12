---
id: ex-01-canvas-circle-animation
category: visual
type: few-shot-example
demonstrates: Canvas API, requestAnimationFrame, delta-time, self-contained HTML
---

## Task

Circle bouncing horizontally across the canvas.

## Input

Create a single HTML file with a circle that bounces back and forth horizontally across a 600x400 canvas. Use requestAnimationFrame and delta-time for smooth animation.

## Output

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bouncing Circle</title>
    <style>
        body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: #111; }
        canvas { border: 1px solid #333; }
    </style>
</head>
<body>
<canvas id="c" width="600" height="400"></canvas>
<script>
    const canvas = document.getElementById('c');
    const ctx = canvas.getContext('2d');

    const circleRadius = 20;
    let circleX = circleRadius;
    let speed = 200;
    let lastTime = 0;

    function update(timestamp) {
        const dt = lastTime ? (timestamp - lastTime) / 1000 : 0;
        lastTime = timestamp;

        circleX += speed * dt;
        if (circleX + circleRadius > canvas.width || circleX - circleRadius < 0) {
            speed = -speed;
            circleX = Math.max(circleRadius, Math.min(canvas.width - circleRadius, circleX));
        }

        ctx.fillStyle = '#111';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.beginPath();
        ctx.arc(circleX, canvas.height / 2, circleRadius, 0, Math.PI * 2);
        ctx.fillStyle = '#4af';
        ctx.fill();

        requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
</script>
</body>
</html>
```
