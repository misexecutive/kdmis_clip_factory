---
name: metadata-generator
description: >-
  Generates authentic, non-hallucinatory hook text overlays, YouTube Shorts titles,
  descriptions, and SEO tags tailored for Gamer Nyro.
---

# Metadata Generator Skill: Hooks & YouTube SEO

This skill produces contextual, game-accurate copy and metadata for Gamer Nyro's YouTube Shorts.

## Core Rules

1. **No Hallucination**: Never invent dialogue, enemies, or weapon skins not present in the clip.
2. **4 Differentiated Hook Overlays per Clip**:
   - *Action / Skill Hook*: Highlights mechanical prowess, rapid reaction, or clutch timing.
   - *Suspense / Curiosity Hook*: Leverages tension, cliffhangers, or unexpected twists.
   - *POV / Gamer Reaction Hook*: Relatable in-game perspective ("When you trust your crosshair placement...").
   - *Episodic Series Hook*: Mentions sequential gameplay arcs ("Wait until you see how this ended in Part 2...").
3. **3 Differentiated YouTube Titles**:
   - *Action & Skill Angle*: E.g., `Calculated 200 IQ Play That Shocked Them 🧠 #Shorts`
   - *Viral Curiosity Angle*: E.g., `Bro Didn't Even Have Time To React! ⚡ #Shorts`
   - *Episodic Series Angle*: E.g., `The Cleanest Gameplay Clutch? [PART 1] 🎯 #Shorts`
4. **Subscriber Retention Descriptions**:
   - Includes contextual explanation, episode call-to-action (`⚡ Don't miss Part 2! Subscribe to Gamer Nyro`), channel hashtags, and game credits.
5. **Differentiated CSV Tags**:
   - Comma-separated tags specific to each clip's detected events (e.g. `gamer nyro, cod mw4 highlight, audio spike, reflex flick, gaming shorts, part 1`).

## Python API Usage

```python
from core.metadata import MetadataGenerator
gen = MetadataGenerator(channel_name="Gamer Nyro")
metadata = gen.generate_youtube_metadata(candidate)
print("Hooks:", metadata["hooks"])          # 4 distinct styles
print("Titles:", metadata["title_choices"]) # 3 distinct angles
print("Description:", metadata["description"])
print("CSV Tags:", metadata["tags_csv"])
```
