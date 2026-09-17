"""Builds the material for a run.

Time Attack needs a long continuous stream, Sentence Challenge needs one exact
sentence, Word Rush needs a queue, Survival needs a ladder of both.
"""

import random

from .levels import PASSAGES, RUSH_WORDS, SURVIVAL_STAGES, get_level


def _band(level_number):
    return max(1, min(int(level_number), max(PASSAGES)))


def passage(level_number):
    return random.choice(PASSAGES[_band(level_number)])


def stream(level_number, min_chars=900):
    """Several passages joined into one continuous block for timed runs."""
    pool = PASSAGES[_band(level_number)][:]
    random.shuffle(pool)
    out, i = [], 0
    while len(" ".join(out)) < min_chars:
        out.append(pool[i % len(pool)])
        i += 1
        if i % len(pool) == 0:
            random.shuffle(pool)
    return " ".join(out)


def rush_queue(level_number, count=80):
    band = max(1, min(int(level_number), max(RUSH_WORDS)))
    words = RUSH_WORDS[band][:]
    queue = []
    while len(queue) < count:
        random.shuffle(words)
        queue.extend(words)
    return queue[:count]


def survival_ladder():
    """One chunk per stage, five stages deep."""
    chunks = []
    for stage in SURVIVAL_STAGES:
        if stage["source"] == "words":
            pool = RUSH_WORDS[stage["band"]][:]
            random.shuffle(pool)
            text = " ".join(pool[:10])
        else:
            text = random.choice(PASSAGES[stage["band"]])
        chunks.append({"stage": stage["stage"], "label": stage["label"], "text": text})
    return chunks


def build(mode, level_number):
    level = get_level(level_number)
    payload = {"level": level["number"], "level_title": level["title"], "mode": mode}

    if mode == "sentence":
        payload["text"] = passage(level["number"])
    elif mode == "rush":
        payload["words"] = rush_queue(level["number"])
    elif mode == "survival":
        payload["stages"] = survival_ladder()
    else:
        payload["text"] = stream(level["number"])
    return payload
