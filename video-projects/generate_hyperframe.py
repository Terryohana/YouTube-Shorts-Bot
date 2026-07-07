import json
import re
import colorsys
import random

def calculate_word_timestamps(script_text, total_duration):
    """Calculate per-word timestamps weighted by character length and punctuation pauses."""
    words = script_text.split()
    
    # Weight each word by character count + punctuation pause bonus
    weights = []
    for word in words:
        w = len(word)
        # Add pause weight for punctuation
        if word.endswith('.'):
            w += 4
        elif word.endswith('!'):
            w += 3
        elif word.endswith('?'):
            w += 3
        elif word.endswith(','):
            w += 2
        elif word.endswith(';') or word.endswith(':'):
            w += 2
        elif word.endswith('—'):
            w += 2
        weights.append(w)
    
    total_weight = sum(weights)
    time_per_weight = total_duration / total_weight
    
    timestamps = []
    cumulative_time = 0.0
    for i, word in enumerate(words):
        word_duration = weights[i] * time_per_weight
        timestamps.append({
            "word": word,
            "start": round(cumulative_time, 3),
            "duration": round(word_duration, 3)
        })
        cumulative_time += word_duration
    
    return timestamps

def chunk_timestamps(timestamps, words_per_chunk=4):
    """Group word timestamps into display chunks."""
    chunks = []
    for i in range(0, len(timestamps), words_per_chunk):
        group = timestamps[i:i+words_per_chunk]
        chunk_text = " ".join(t["word"] for t in group)
        chunk_start = group[0]["start"]
        chunk_end = group[-1]["start"] + group[-1]["duration"]
        chunk_duration = chunk_end - chunk_start
        chunks.append({
            "text": chunk_text,
            "start": chunk_start,
            "duration": chunk_duration,
            "words": group
        })
    return chunks

def generate_color_palette(n):
    """Generate n visually distinct, vibrant colors."""
    colors = []
    for i in range(n):
        hue = (i / n) % 1.0
        sat = 0.75 + random.uniform(0, 0.2)
        val = 0.8 + random.uniform(0, 0.15)
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        colors.append(f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}")
    return colors

def generate_html(script_text, total_duration):
    timestamps = calculate_word_timestamps(script_text, total_duration)
    chunks = chunk_timestamps(timestamps, words_per_chunk=4)
    num_chunks = len(chunks)
    colors = generate_color_palette(num_chunks)
    visual_types = ["rings", "bars", "dots", "lines", "grid", "arcs"]
    
    # Build chunks data with precise timing
    chunks_data = []
    for i, chunk in enumerate(chunks):
        word_offsets = []
        for w in chunk["words"]:
            # Offset relative to chunk start
            word_offsets.append({
                "word": w["word"].replace('"', '&quot;').replace("'", "&#39;"),
                "offset": round(w["start"] - chunk["start"], 3),
                "duration": w["duration"]
            })
        chunks_data.append({
            "text": chunk["text"].replace('"', '&quot;').replace("'", "&#39;"),
            "start": chunk["start"],
            "duration": chunk["duration"],
            "color": colors[i],
            "visual": visual_types[i % len(visual_types)],
            "words": word_offsets
        })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>HyperFrames Motion Graphics</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');

* {{ margin:0; padding:0; box-sizing:border-box; }}

body {{
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    background: #050510;
    font-family: 'Inter', sans-serif;
    position: relative;
}}

.morph-bg {{
    position: absolute;
    width: 100%; height: 100%;
    z-index: 0;
    filter: blur(120px);
    opacity: 0.5;
}}
.blob {{
    position: absolute;
    border-radius: 50%;
}}
.blob-1 {{ width: 600px; height: 600px; top: -100px; left: -100px; background: #6366f1; }}
.blob-2 {{ width: 500px; height: 500px; bottom: -100px; right: -100px; background: #ec4899; }}
.blob-3 {{ width: 400px; height: 400px; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #14b8a6; }}

.particle-layer {{
    position: absolute;
    width: 100%; height: 100%;
    z-index: 1;
}}
.particle {{
    position: absolute;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
}}

.grid-overlay {{
    position: absolute;
    width: 100%; height: 100%;
    z-index: 1;
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    opacity: 0.6;
}}

.visual-layer {{
    position: absolute;
    width: 100%; height: 100%;
    z-index: 2;
    pointer-events: none;
}}

.ring {{
    position: absolute;
    border: 3px solid rgba(255,255,255,0.15);
    border-radius: 50%;
    opacity: 0;
}}

.bar-group {{
    position: absolute;
    display: flex;
    align-items: flex-end;
    gap: 8px;
    opacity: 0;
}}
.bar {{
    width: 20px;
    border-radius: 4px 4px 0 0;
    transform-origin: bottom;
}}

.dot-grid {{
    position: absolute;
    display: grid;
    gap: 20px;
    opacity: 0;
}}
.dot {{
    width: 8px; height: 8px;
    border-radius: 50%;
    opacity: 0;
}}

.line-element {{
    position: absolute;
    height: 3px;
    border-radius: 2px;
    transform-origin: left;
    transform: scaleX(0);
    opacity: 0;
}}

.text-layer {{
    position: absolute;
    width: 100%; height: 100%;
    z-index: 10;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 100px 200px;
}}

.chunk-container {{
    position: absolute;
    text-align: center;
    opacity: 0;
}}

.chunk-text {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 88px;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.15;
    text-shadow: 0 0 60px rgba(0,0,0,0.8);
    letter-spacing: -1px;
}}

.chunk-text .word {{
    display: inline-block;
    margin: 0 8px;
    opacity: 0.15;
    transform: translateY(20px);
}}

.highlight-bar {{
    height: 6px;
    border-radius: 3px;
    margin-top: 20px;
    transform: scaleX(0);
    transform-origin: left;
}}

.hud-top-left {{
    position: absolute;
    top: 40px; left: 40px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    color: rgba(255,255,255,0.3);
    z-index: 20;
    letter-spacing: 2px;
}}

.hud-bottom-right {{
    position: absolute;
    bottom: 40px; right: 40px;
    z-index: 20;
}}

.subscribe-pill {{
    background: #ef4444;
    color: white;
    padding: 16px 32px;
    border-radius: 50px;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 1px;
    box-shadow: 0 8px 30px rgba(239,68,68,0.4);
    display: flex; align-items: center; gap: 12px;
}}

.progress-bar-container {{
    position: absolute;
    bottom: 0; left: 0;
    width: 100%; height: 4px;
    z-index: 20;
    background: rgba(255,255,255,0.1);
}}
.progress-bar {{
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #6366f1, #ec4899, #f59e0b);
}}
</style>
</head>
<body>

<div class="morph-bg">
    <div class="blob blob-1" id="blob1"></div>
    <div class="blob blob-2" id="blob2"></div>
    <div class="blob blob-3" id="blob3"></div>
</div>

<div class="particle-layer" id="particleLayer"></div>
<div class="grid-overlay"></div>
<div class="visual-layer" id="visualLayer"></div>
<div class="text-layer" id="textLayer"></div>

<div class="hud-top-left">
    HYPERFRAMES // MOTION SYSTEM<br>
    LIVE RENDER &bull; 1080p
</div>

<div class="hud-bottom-right">
    <div class="subscribe-pill">
        <span style="font-size:18px;">🔴</span> SUBSCRIBE
    </div>
</div>

<div class="progress-bar-container">
    <div class="progress-bar" id="progressBar"></div>
</div>

<script>
const CHUNKS = {json.dumps(chunks_data)};

// ========== PARTICLES ==========
(function() {{
    const layer = document.getElementById('particleLayer');
    for (let i = 0; i < 50; i++) {{
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 4 + 1;
        p.style.width = size + 'px';
        p.style.height = size + 'px';
        p.style.left = Math.random() * 1920 + 'px';
        p.style.top = Math.random() * 1080 + 'px';
        layer.appendChild(p);
        gsap.to(p, {{
            y: -200 - Math.random() * 400,
            x: (Math.random() - 0.5) * 300,
            opacity: 0,
            duration: 5 + Math.random() * 10,
            repeat: -1,
            delay: Math.random() * 5,
            ease: "none"
        }});
    }}
}})();

// ========== BLOB MORPHING ==========
function morphBlobs(color) {{
    gsap.to('#blob1', {{ x: Math.random()*400-200, y: Math.random()*300-150, scale: 0.8+Math.random()*0.8, background: color, duration: 3, ease: "sine.inOut" }});
    gsap.to('#blob2', {{ x: Math.random()*400-200, y: Math.random()*300-150, scale: 0.7+Math.random()*0.9, duration: 3.5, ease: "sine.inOut" }});
    gsap.to('#blob3', {{ x: Math.random()*300-150, y: Math.random()*200-100, scale: 0.6+Math.random()*1.0, duration: 4, ease: "sine.inOut" }});
}}

// ========== VISUAL GENERATORS ==========
const visualLayer = document.getElementById('visualLayer');

function clearVisuals() {{
    gsap.to(visualLayer.children, {{ opacity: 0, duration: 0.5, stagger: 0.05, onComplete: () => visualLayer.innerHTML = '' }});
}}

function spawnRings(color) {{
    for (let i = 0; i < 3; i++) {{
        const ring = document.createElement('div');
        ring.className = 'ring';
        const size = 150 + Math.random() * 300;
        Object.assign(ring.style, {{ width: size+'px', height: size+'px', borderColor: color+'44', left: (300+Math.random()*1300)+'px', top: (200+Math.random()*600)+'px' }});
        visualLayer.appendChild(ring);
        gsap.fromTo(ring, {{ opacity:0, scale:0.3 }}, {{ opacity:0.6, scale:1, duration:1.5, ease:"elastic.out(1,0.5)", delay:i*0.3 }});
        gsap.to(ring, {{ rotation:360, duration:8+i*2, repeat:-1, ease:"none" }});
    }}
}}

function spawnBars(color) {{
    const group = document.createElement('div');
    group.className = 'bar-group';
    Object.assign(group.style, {{ left: (200+Math.random()*600)+'px', bottom: (150+Math.random()*200)+'px' }});
    for (let i = 0; i < 8; i++) {{
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.height = '0px';
        bar.style.background = 'linear-gradient(to top, '+color+', '+color+'88)';
        group.appendChild(bar);
        gsap.to(bar, {{ height: 40+Math.random()*200, duration: 0.8, delay: i*0.1, ease: "back.out(1.7)" }});
    }}
    visualLayer.appendChild(group);
    gsap.to(group, {{ opacity: 1, duration: 0.5 }});
}}

function spawnDots(color) {{
    const grid = document.createElement('div');
    grid.className = 'dot-grid';
    Object.assign(grid.style, {{ gridTemplateColumns: 'repeat(6, 1fr)', right: (100+Math.random()*400)+'px', top: (200+Math.random()*400)+'px' }});
    for (let i = 0; i < 24; i++) {{
        const dot = document.createElement('div');
        dot.className = 'dot';
        dot.style.background = color;
        grid.appendChild(dot);
        gsap.to(dot, {{ opacity: Math.random()*0.8+0.2, scale: 0.5+Math.random()*1.5, duration: 0.4, delay: i*0.05, ease: "back.out(2)" }});
    }}
    visualLayer.appendChild(grid);
    gsap.to(grid, {{ opacity: 1, duration: 0.3 }});
}}

function spawnLines(color) {{
    for (let i = 0; i < 5; i++) {{
        const line = document.createElement('div');
        line.className = 'line-element';
        Object.assign(line.style, {{ width: (200+Math.random()*600)+'px', background: 'linear-gradient(90deg, '+color+', transparent)', left: Math.random()*1200+'px', top: (100+Math.random()*880)+'px' }});
        visualLayer.appendChild(line);
        gsap.to(line, {{ opacity: 0.6, scaleX: 1, duration: 0.8, delay: i*0.15, ease: "power3.out" }});
    }}
}}

function spawnGrid(color) {{
    for (let i = 0; i < 12; i++) {{
        const rect = document.createElement('div');
        const size = 40+Math.random()*120;
        Object.assign(rect.style, {{ position:'absolute', border:'2px solid '+color+'33', borderRadius:'8px', width:size+'px', height:size+'px', left:Math.random()*1800+'px', top:Math.random()*1000+'px', opacity:'0' }});
        visualLayer.appendChild(rect);
        gsap.to(rect, {{ opacity:0.4, rotation:Math.random()*45, duration:1, delay:i*0.08, ease:"power2.out" }});
        gsap.to(rect, {{ rotation:'+=90', duration:10+Math.random()*10, repeat:-1, ease:"none" }});
    }}
}}

function spawnArcs(color) {{
    for (let i = 0; i < 4; i++) {{
        const arc = document.createElement('div');
        const size = 200 + Math.random() * 250;
        Object.assign(arc.style, {{ position:'absolute', width:size+'px', height:size+'px', borderRadius:'50%', border:'3px solid transparent', borderTopColor:color+'66', borderRightColor:color+'33', left:(200+Math.random()*1400)+'px', top:(100+Math.random()*700)+'px', opacity:'0' }});
        visualLayer.appendChild(arc);
        gsap.to(arc, {{ opacity:0.7, duration:0.8, delay:i*0.2 }});
        gsap.to(arc, {{ rotation:360*(Math.random()>0.5?1:-1), duration:4+Math.random()*6, repeat:-1, ease:"none" }});
    }}
}}

const visualSpawners = {{ rings:spawnRings, bars:spawnBars, dots:spawnDots, lines:spawnLines, grid:spawnGrid, arcs:spawnArcs }};

// ========== BUILD TIMED WORD ELEMENTS ==========
const textLayer = document.getElementById('textLayer');
const progressBar = document.getElementById('progressBar');
const masterTl = gsap.timeline();

CHUNKS.forEach((chunk, index) => {{
    // Create chunk container
    const container = document.createElement('div');
    container.className = 'chunk-container';
    container.id = 'chunk-' + index;

    const textDiv = document.createElement('div');
    textDiv.className = 'chunk-text';
    chunk.words.forEach((w, wi) => {{
        const span = document.createElement('span');
        span.className = 'word';
        span.textContent = w.word;
        span.id = 'c' + index + 'w' + wi;
        textDiv.appendChild(span);
    }});
    container.appendChild(textDiv);

    const bar = document.createElement('div');
    bar.className = 'highlight-bar';
    bar.style.background = 'linear-gradient(90deg, ' + chunk.color + ', ' + chunk.color + '88)';
    container.appendChild(bar);

    textLayer.appendChild(container);

    // === PRECISELY TIMED ANIMATIONS ===
    
    // Show the chunk container at its exact start time
    masterTl.set(container, {{ opacity: 1 }}, chunk.start);
    
    // Animate highlight bar across the chunk duration
    masterTl.fromTo(bar, {{ scaleX: 0 }}, {{ scaleX: 1, duration: chunk.duration * 0.8, ease: "power1.out" }}, chunk.start);

    // Animate each word at its EXACT offset time
    chunk.words.forEach((w, wi) => {{
        const wordEl = document.getElementById('c' + index + 'w' + wi);
        const wordTime = chunk.start + w.offset;
        
        // Word pops in at exact spoken time
        masterTl.to(wordEl, {{
            opacity: 1,
            y: 0,
            duration: 0.15,
            ease: "back.out(2)"
        }}, wordTime);
        
        // Highlight with accent color
        masterTl.to(wordEl, {{
            color: chunk.color,
            textShadow: '0 0 40px ' + chunk.color + '88',
            duration: 0.1
        }}, wordTime);
        
        // Unhighlight after its duration
        masterTl.to(wordEl, {{
            color: '#ffffff',
            textShadow: '0 0 60px rgba(0,0,0,0.8)',
            duration: 0.3
        }}, wordTime + w.duration);
    }});

    // Fade out the entire chunk after last word finishes
    const chunkEnd = chunk.start + chunk.duration;
    masterTl.to(container, {{ opacity: 0, y: -30, duration: 0.35, ease: "power2.in" }}, chunkEnd - 0.35);

    // Morph blobs on every chunk
    masterTl.call(morphBlobs, [chunk.color], chunk.start);

    // Swap visual elements every 3 chunks
    if (index % 3 === 0) {{
        masterTl.call(clearVisuals, [], chunk.start);
        masterTl.call(() => {{
            const spawner = visualSpawners[chunk.visual] || spawnRings;
            spawner(chunk.color);
        }}, [], chunk.start + 0.3);
    }}
}});

// Progress bar driven by total duration
const totalDur = CHUNKS[CHUNKS.length - 1].start + CHUNKS[CHUNKS.length - 1].duration;
masterTl.to(progressBar, {{ width: '100%', duration: totalDur, ease: "none" }}, 0);

</script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated Synced Motion Graphics ({num_chunks} chunks, {len(timestamps)} words)")

if __name__ == "__main__":
    import sys
    total_dur = float(sys.argv[1]) if len(sys.argv) > 1 else 200.0
    with open("daily_script.txt", "r", encoding="utf-8") as f:
        script = f.read().strip()
    generate_html(script, total_dur)
