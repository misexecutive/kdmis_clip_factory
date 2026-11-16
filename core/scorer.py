"""
Nyro AI Clip Factory - Candidate Scorer & Explanation Engine
Evaluates candidate clips across 15 YouTube Shorts retention dimensions
and provides contextual editorial reasoning for extended highlights and micro-clips.
"""

import logging
from typing import Dict, Any, List, Tuple
import numpy as np
from core.clip_discovery import CandidateClip, MultiDimensionalScorer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class CandidateScorer:
    """
    Evaluates candidate clips using the MultiDimensionalScorer engine across 15 dimensions:
    Opening strength, visual impact, audio impact, unexpectedness, emotional intensity,
    gameplay relevance, cinematic value, storytelling potential, curiosity potential,
    payoff quality, replay potential, loop potential, viewer comprehension, originality, editing potential.
    """

    def __init__(self):
        self.engine = MultiDimensionalScorer()

    def score_candidate(
        self,
        candidate: CandidateClip,
        time_vector: np.ndarray,
        rms_curve: np.ndarray,
        motion_samples: Any = None,
    ) -> CandidateClip:
        """Computes multi-dimensional scores and editorial explanation for a candidate."""
        return self.engine.evaluate_clip(candidate, time_vector, rms_curve, motion_samples)

    def score_all(
        self,
        candidates: List[CandidateClip],
        time_vector: np.ndarray,
        rms_curve: np.ndarray,
        motion_samples: Any = None,
    ) -> List[CandidateClip]:
        """Scores and ranks all candidates in descending order."""
        for c in candidates:
            self.score_candidate(c, time_vector, rms_curve, motion_samples)

        candidates.sort(key=lambda x: x.score, reverse=True)
        logger.info(f"Scored {len(candidates)} candidates. Top score: {candidates[0].score if candidates else 'N/A'}")
        return candidates


if __name__ == "__main__":
    scorer = CandidateScorer()
    print("CandidateScorer module ready.")
