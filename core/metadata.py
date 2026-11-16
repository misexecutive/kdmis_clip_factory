"""
Nyro AI Clip Factory - Advanced Metadata & Series Generator
Produces highly differentiated, non-repetitive hook overlays,
multiple title choices, custom descriptions, and tailored CSV tags
for every candidate clip, including episodic Series/Part features.
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from core.detector import CandidateClip

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class MetadataGenerator:
    """
    Generates diverse, moment-specific hooks, multiple title options,
    descriptions, and tags tailored for Gamer Nyro with episodic Series support.
    """

    def __init__(self, channel_name: str = "Gamer Nyro"):
        self.channel_name = channel_name

    def infer_game_context(self, filename: str) -> str:
        """Extracts game name or theme from filename if present."""
        clean = Path(filename).stem.lower().replace("-", " ").replace("_", " ")
        common_games = {
            "valorant": "Valorant",
            "cs2": "Counter-Strike 2",
            "csgo": "CS:GO",
            "cod": "Call of Duty",
            "warzone": "Warzone",
            "apex": "Apex Legends",
            "fortnite": "Fortnite",
            "elden ring": "Elden Ring",
            "cyberpunk": "Cyberpunk 2077",
            "gta": "GTA V",
            "r6": "Rainbow Six Siege",
            "siege": "Rainbow Six Siege",
            "helldivers": "Helldivers 2",
            "pubg": "PUBG",
            "overwatch": "Overwatch 2",
            "minecraft": "Minecraft",
        }
        for key, val in common_games.items():
            if key in clean:
                return val
        return "Gaming"

    def _get_seed_index(self, candidate_id: str, pool_size: int) -> int:
        """Deterministically picks unique items based on clip id hash."""
        h = int(hashlib.md5(candidate_id.encode("utf-8")).hexdigest(), 16)
        return h % pool_size

    def generate_hooks(
        self,
        candidate: CandidateClip,
        game_name: str,
        part_num: Optional[int] = None,
    ) -> List[str]:
        """
        Produces 4 distinct, moment-tailored hook options:
        1. Action / Mechanical Skill Hook
        2. Suspense / Curiosity Hook
        3. POV / Observational Gamer Reaction
        4. Episodic / Multi-Part Series Hook
        """
        is_micro = candidate.clip_format == "micro" or candidate.duration <= 14.0
        peak_intensity = candidate.peak_intensity
        events = candidate.events or []
        has_sudden = any("Sudden" in e.get("description", "") for e in events)
        event_count = len(events)
        idx = self._get_seed_index(candidate.id, 8)

        # 1. Action / Mechanical Skill Hooks
        if is_micro:
            action_pool = [
                "0.1s reaction time...",
                "The cleanest flick you'll see today",
                "Don't blink during this shot",
                "Instant crosshair snap",
                "Calculated 1-tap",
                "How fast was that reflex?!",
                "Target acquired and neutralized",
                "Speedrun elimination",
            ]
        elif event_count >= 15:
            action_pool = [
                "Holding the entire angle on 1 HP...",
                "Surrounded from every single angle",
                "The most chaotic 25 seconds ever",
                "Full squad pushing at the same time",
                "Pure adrenaline clutch",
                "Surviving under impossible pressure",
                "How did this spray transfer connect?",
                "Refusing to lose this duel",
            ]
        else:
            action_pool = [
                f"Peak {game_name} mechanical skill",
                "Patience rewarded with a clutch",
                "Flawless crosshair placement",
                "Outplaying them step by step",
                "Total movement control",
                "Calculated angle hold",
                "Never challenge this position",
                "Cleanest engagement this round",
            ]

        # 2. Suspense / Curiosity Hooks
        if has_sudden:
            curiosity_pool = [
                "He was hiding there the entire time...",
                "Turned around at the worst second",
                "Didn't expect this ambush...",
                "Out of nowhere.",
                "Wait for what happens right here...",
                "Watch the minimap carefully...",
                "He had no idea I was listening",
                "The biggest jumpscare in this match",
            ]
        else:
            curiosity_pool = [
                "Wait for the ending...",
                "They thought they had an easy win",
                "Watch how this round completely flips",
                "He didn't realize who was behind him",
                "The confidence vanished instantly",
                "Look closely at the crosshair...",
                "Everything went wrong, until...",
                "Nobody saw this outcome coming",
            ]

        # 3. POV / Observational Reaction Hooks
        reaction_pool = [
            "Bro thought he was safe behind cover",
            "I can't believe this actually worked",
            "My hands were literally shaking",
            "You cannot script this timing",
            "The disrespect in this play...",
            "He definitely reported me after this",
            "How did that shot even register?!",
            "That's enough gaming for today...",
        ]

        # 4. Episodic / Multi-Part Hook
        part_label = f"PART {part_num}" if part_num else f"PART {self._get_seed_index(candidate.id, 5) + 1}"
        series_pool = [
            f"{part_label} | Wait till the climax...",
            f"{part_label} | The cleanest clutch of the session",
            f"{part_label} | Did he just hit that?!",
            f"{part_label} | Watch how we survived this",
            f"{part_label} | Impossible 1v3 engagement",
            f"{part_label} | Outplaying the whole lobby",
            f"{part_label} | Part 2 drops next, don't miss it",
            f"{part_label} | Most insane play yet",
        ]

        hook1 = action_pool[idx % len(action_pool)]
        hook2 = curiosity_pool[(idx + 2) % len(curiosity_pool)]
        hook3 = reaction_pool[(idx + 4) % len(reaction_pool)]
        hook4 = series_pool[idx % len(series_pool)]

        return [hook1, hook2, hook3, hook4]

    def generate_title_choices(
        self,
        candidate: CandidateClip,
        game_name: str,
        part_num: Optional[int] = None,
    ) -> List[str]:
        """
        Generates 3 distinct YouTube Shorts title choices:
        1. Action & Skill Title
        2. Viral Curiosity Title
        3. Episodic Series Title with Part Indicator
        """
        is_micro = candidate.clip_format == "micro" or candidate.duration <= 14.0
        part_str = f"(Part {part_num})" if part_num else f"(Part {self._get_seed_index(candidate.id, 5) + 1})"
        idx = self._get_seed_index(candidate.id, 6)

        if is_micro:
            action_titles = [
                f"Bro Didn't Even Have Time To React! ⚡ #Shorts",
                f"The Fastest 1-Tap You'll See Today 🎯 #Shorts",
                f"0.1s Pure Reflex Reaction in {game_name} 💥 #Shorts",
                f"Instant Crosshair Flick That Broke Him! 🎯 #Shorts",
                f"He Never Saw It Coming... ⚡ #Shorts",
                f"Cleanest Snap Of The Entire Game 🎯 #Shorts",
            ]
            curiosity_titles = [
                f"Wait... How Did That Even Hit?! 🤯 #Shorts",
                f"He Definitely Reported This One... 💀 #Shorts",
                f"Don't Blink Or You'll Miss It! 👀 #Shorts",
                f"When Pure Muscle Memory Kicks In... 🔥 #Shorts",
                f"That Angle Was Actually Filthy! 🎯 #Shorts",
                f"The Timing On This Was Unreal 😱 #Shorts",
            ]
            series_titles = [
                f"Insane {game_name} Moments {part_str} ⚡ #Shorts",
                f"Unreal Reaction Plays {part_str} 🎯 #Shorts",
                f"Fastest Gaming Highlights {part_str} 🔥 #Shorts",
                f"When Instinct Takes Over {part_str} 💥 #Shorts",
                f"Best Reflexes Of The Week {part_str} 🎯 #Shorts",
                f"Micro Clutch Speedrun {part_str} ⚡ #Shorts",
            ]
        else:
            action_titles = [
                f"1v3 Clutch Against All Odds! 🛡️ #Shorts",
                f"When The Entire Lobby Pushes You At Once 💀 #Shorts",
                f"Surviving On Pure Adrenaline In {game_name}! 🔥 #Shorts",
                f"The Most Intense 30 Seconds In {game_name} 🎯 #Shorts",
                f"Holding The Site With 1 HP Left! 🛡️ #Shorts",
                f"Calculated 200 IQ Play That Shocked Them 🧠 #Shorts",
            ]
            curiosity_titles = [
                f"They Thought They Won Until THIS Happened... 💥 #Shorts",
                f"He Was Hiding There The ENTIRE Time! 😱 #Shorts",
                f"Nobody Believed We Could Win This Round 🤯 #Shorts",
                f"Watch His Teammate's Reaction At The End... 💀 #Shorts",
                f"How Did We Walk Away Alive From This?! 🔥 #Shorts",
                f"The Moment Everything Turned Around... 🎯 #Shorts",
            ]
            series_titles = [
                f"Impossible Clutch Series {part_str} 🎯 #Shorts",
                f"Solo vs Squad Chronicles {part_str} 🛡️ #Shorts",
                f"Road To Victory Highlights {part_str} 🔥 #Shorts",
                f"Unreal Gaming Outplays {part_str} 💥 #Shorts",
                f"Best {game_name} Plays {part_str} 🎮 #Shorts",
                f"High-Stakes Clutch Series {part_str} 🏆 #Shorts",
            ]

        t1 = action_titles[idx % len(action_titles)]
        t2 = curiosity_titles[(idx + 2) % len(curiosity_titles)]
        t3 = series_titles[idx % len(series_titles)]

        return [t1, t2, t3]

    def generate_tags(
        self,
        candidate: CandidateClip,
        game_name: str,
        part_num: Optional[int] = None,
    ) -> List[str]:
        """
        Produces differentiated CSV tags per clip, tailored to gameplay style.
        """
        is_micro = candidate.clip_format == "micro" or candidate.duration <= 14.0
        part_tag = f"part {part_num}" if part_num else f"part {self._get_seed_index(candidate.id, 5) + 1}"

        base_tags = [
            "shorts",
            "gaming shorts",
            "youtube shorts",
            self.channel_name.lower(),
            game_name.lower(),
            f"{game_name.lower()} shorts",
        ]

        if is_micro:
            style_tags = [
                "flick shot",
                "fast reflexes",
                "micro clips",
                "1tap",
                "instant kill",
                "satisfying shots",
                f"{game_name.lower()} reflex",
                part_tag,
                "gamer nyro shorts",
            ]
        else:
            style_tags = [
                "clutch moment",
                "1v3 clutch",
                "gaming highlights",
                "insane gameplay",
                "outplay",
                "fps clutch",
                part_tag,
                f"{game_name.lower()} gameplay",
                "epic gaming moments",
            ]

        # Combine and deduplicate
        all_tags = []
        for t in base_tags + style_tags:
            if t not in all_tags:
                all_tags.append(t)
        return all_tags

    def generate_youtube_metadata(
        self,
        candidate: CandidateClip,
        part_num: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generates upload-ready, diverse YouTube Shorts metadata per candidate clip.
        """
        game_name = self.infer_game_context(candidate.video_filename)
        hooks = self.generate_hooks(candidate, game_name, part_num)
        titles = self.generate_title_choices(candidate, game_name, part_num)
        tags = self.generate_tags(candidate, game_name, part_num)

        part_indicator = f"Part {part_num}" if part_num else f"Part {self._get_seed_index(candidate.id, 5) + 1}"
        next_part = (part_num + 1) if part_num else (self._get_seed_index(candidate.id, 5) + 2)

        candidate.suggested_hooks = hooks
        candidate.title_suggestion = titles[0]
        candidate.title_choices = titles
        candidate.tags_suggestion = tags
        candidate.series_part = part_indicator

        # Diverse description with series hook to bring viewers back
        description = (
            f"🎯 {hooks[0]}\n\n"
            f"🔥 {part_indicator} of our daily {game_name} highlight series from {self.channel_name}!\n"
            f"Original gameplay session timestamp: {candidate.start_time:.1f}s - {candidate.end_time:.1f}s\n\n"
            f"👉 Part {next_part} is dropping next! Tap LIKE & SUBSCRIBE to {self.channel_name} so you don't miss it!\n\n"
            f"🎮 Game: {game_name}\n"
            f"#Shorts #Gaming #{game_name.replace(' ', '')} #GamerNyro #{part_indicator.replace(' ', '')}"
        )
        candidate.description_suggestion = description

        return {
            "title": titles[0],
            "title_choices": titles,
            "hooks": hooks,
            "description": description,
            "tags_list": tags,
            "tags_csv": ", ".join(tags),
            "series_part": part_indicator,
        }


if __name__ == "__main__":
    gen = MetadataGenerator()
    print("MetadataGenerator ready.")
