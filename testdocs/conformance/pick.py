"""Choose which phrasing each package uses, by measuring rather than guessing.

Four variants across six sections is only 4096 combinations, and a naive
i % 4 assignment hands identical frames to every package sixteen apart. So the
combination is chosen greedily against the real similarity metric: for each
package, try a sample of combinations and keep the one that scores lowest
against everything already chosen.
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import prose  # noqa: E402
from app.services.report_similarity import SimilarityIndex  # noqa: E402

N = 50
rng = random.Random(20260905)


def text_for(i, combo):
    return "\n".join(h + " " + b for h, b in prose.sections_with(i, combo))


def main():
    chosen = {}
    texts = []
    for i in range(N):
        best, best_score = None, 2.0
        for _ in range(240):
            combo = tuple(rng.randrange(4) for _ in range(6))
            t = text_for(i, combo)
            idx = SimilarityIndex()
            for j, prev in enumerate(texts):
                idx.add(str(j), prev)
            score = idx.most_similar(t)[0] if texts else 0.0
            if score < best_score:
                best, best_score = combo, score
            if best_score < 0.30:
                break
        chosen[i] = list(best)
        texts.append(text_for(i, best))
        print(f"{i:>2} {best} worst-so-far {best_score:.3f}", file=sys.stderr)

    Path(__file__).with_name("combos.json").write_text(json.dumps(chosen), encoding="utf-8")

    worst = 0.0
    for i in range(N):
        idx = SimilarityIndex()
        for j in range(N):
            if j != i:
                idx.add(str(j), texts[j])
        worst = max(worst, idx.most_similar(texts[i])[0])
    print(f"worst pairwise over the whole set: {worst:.3f}")


if __name__ == "__main__":
    main()
