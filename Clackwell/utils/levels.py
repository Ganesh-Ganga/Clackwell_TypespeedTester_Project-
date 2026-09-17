"""Level definitions plus the text each level draws from.

Difficulty is driven by the *material* (word length, punctuation, digits,
casing, vocabulary), not by shrinking the clock.
"""

LEVELS = [
    {
        "number": 1, "title": "Beginner", "blurb": "Short words, all lowercase, no punctuation.",
        "target_wpm": 20, "target_accuracy": 80, "xp_reward": 100,
        "required_score": 250, "difficulty": "Easy", "multiplier": 1.0,
    },
    {
        "number": 2, "title": "Rookie", "blurb": "Everyday sentences with commas and full stops.",
        "target_wpm": 26, "target_accuracy": 82, "xp_reward": 150,
        "required_score": 500, "difficulty": "Easy", "multiplier": 1.1,
    },
    {
        "number": 3, "title": "Typist", "blurb": "Longer sentences, mixed capitals.",
        "target_wpm": 32, "target_accuracy": 85, "xp_reward": 200,
        "required_score": 850, "difficulty": "Medium", "multiplier": 1.25,
    },
    {
        "number": 4, "title": "Speed Runner", "blurb": "Dense paragraphs with heavy punctuation.",
        "target_wpm": 40, "target_accuracy": 88, "xp_reward": 250,
        "required_score": 1250, "difficulty": "Medium", "multiplier": 1.4,
    },
    {
        "number": 5, "title": "Keyboard Warrior", "blurb": "Unfamiliar vocabulary and long words.",
        "target_wpm": 48, "target_accuracy": 90, "xp_reward": 320,
        "required_score": 1700, "difficulty": "Hard", "multiplier": 1.6,
    },
    {
        "number": 6, "title": "Speed Master", "blurb": "Numbers, symbols and technical prose.",
        "target_wpm": 56, "target_accuracy": 92, "xp_reward": 420,
        "required_score": 2200, "difficulty": "Hard", "multiplier": 1.8,
    },
    {
        "number": 7, "title": "Typing Legend", "blurb": "Source code, mixed case, every symbol row.",
        "target_wpm": 65, "target_accuracy": 94, "xp_reward": 550,
        "required_score": 2800, "difficulty": "Brutal", "multiplier": 2.0,
    },
]

MAX_LEVEL = len(LEVELS)


def get_level(number):
    number = max(1, min(int(number or 1), MAX_LEVEL))
    return LEVELS[number - 1]


# --- Passage pools ---------------------------------------------------------
# Written as real prose rather than lorem ipsum so practice feels like reading.

PASSAGES = {
    1: [
        "the cat sat by the door and watched the rain fall on the road",
        "he ran to the shop to buy bread milk and a bag of red apples",
        "we can walk to the park if the sun is out in the late day",
        "she put her old bike near the gate and went in for a cup of tea",
        "a small boy fed the birds with bits of dry bread from his hand",
    ],
    2: [
        "The train was late again, so we sat on the bench and counted the pigeons on the roof.",
        "Rain started just after four, and the whole street smelled like wet dust and cut grass.",
        "She learned to type on her father's old machine, one slow finger at a time.",
        "If you practise for ten minutes a day, the keyboard stops fighting back within a month.",
        "The cafe near the station serves the worst coffee in town, but the chairs are comfortable.",
    ],
    3: [
        "Most people type faster than they think they do; what slows them down is the habit of glancing at their hands between every second word.",
        "The library stayed open until midnight during exam week, and by Thursday every desk near a plug point had been claimed since morning.",
        "Muscle memory is built by repetition, not by effort, which is why a calm ten minutes beats a frantic hour on any given evening.",
        "When the power cut hit, the room went quiet except for the sound of thirty keyboards that had not yet realised the screens were gone.",
        "Good typists are not the ones who never make mistakes; they are the ones who notice a mistake before their eyes reach the end of the line.",
    ],
    4: [
        "Accuracy first, speed second: that's the rule every coach repeats, and it's the one every beginner ignores. The result? Weeks of practice spent teaching your hands to make the same error faster.",
        "\"Don't look down,\" she said, half joking, \"the letters haven't moved since 1873.\" It's true — the layout in front of you was designed for typewriters, not for people, and yet here we are, still using it.",
        "The workshop ran from 9:30 to 11:00, covering posture, hand position, and the strange, stubborn problem of the left ring finger; nobody left early, which the instructor took as a good sign.",
        "He kept a log — date, words per minute, accuracy, mood — and after sixty days the numbers told a story his memory couldn't: progress isn't a line, it's a slope with a lot of noise on top.",
    ],
    5: [
        "The committee's preliminary assessment characterised the proposal as fundamentally sound, albeit encumbered by administrative obligations that no reasonable jurisdiction would voluntarily undertake.",
        "Neuroplasticity, the brain's capacity to reorganise its synaptic architecture, underpins virtually every acquired motor skill, from calligraphy to the unglamorous discipline of touch typing.",
        "Bureaucratic terminology tends toward polysyllabic obfuscation; a sentence that could have communicated its meaning in twelve words instead requires forty-three and a glossary.",
        "Idiosyncratic keyboard layouts — Dvorak, Colemak, Workman — promise measurable ergonomic advantages, though the literature remains conspicuously inconclusive about long-term throughput gains.",
    ],
    6: [
        "In Q3 2024, throughput rose 18.7% to 4,320 units/day, while defect rates fell from 2.4% to 0.9% — a swing of roughly $1.2M against the forecast filed on 03/11.",
        "Set the timer to 45s, the threshold to 0.85, and the retry budget to 3; if latency exceeds 250ms for 5 consecutive samples, the watchdog fires at T+00:02:30 and dumps to /var/log/run.log.",
        "Invoice #INV-2291 (dated 07/09/2025) lists 12 line items totalling ₹86,450.00, of which ₹14,300.75 is GST at 18% — please remit within 30 days to account 0042-9981-7756.",
        "Room 4B, Building 17, Sector 62 — take the 8:15 shuttle, badge in at gate 3, and note that the lab closes at 21:00 sharp on weekdays and 17:30 on Saturdays.",
    ],
    7: [
        "const merged = items.filter(x => x.qty > 0).map(({ id, qty }) => ({ id, qty: qty * 2 })).reduce((acc, cur) => { acc[cur.id] = cur.qty; return acc; }, {});",
        "SELECT u.id, COUNT(r.id) AS runs FROM users u LEFT JOIN results r ON r.user_id = u.id WHERE r.wpm >= 45 GROUP BY u.id HAVING COUNT(r.id) > 10 ORDER BY runs DESC LIMIT 25;",
        "def walk(node, depth=0): return [node['name']] + [n for c in node.get('children', []) for n in walk(c, depth + 1)] if node else []  # depth-first, ~O(n)",
        "git rebase -i HEAD~7 && git push --force-with-lease origin feature/typing-engine; echo \"$?\" | tee -a ./logs/deploy_$(date +%Y%m%d).log",
    ],
}

# Word Rush pools — one bucket per difficulty band.
RUSH_WORDS = {
    1: "cat dog run sun map bed cup box key pen red top hat fan jam leg cow bus arm ice".split(),
    2: "table chair window pencil garden bottle silver monkey orange purple summer wallet ticket pocket".split(),
    3: "keyboard practice sentence highlight sequence movement designer language calendar exercise".split(),
    4: "algorithm framework dependency repository connection background structured philosophy".split(),
    5: "asynchronous polymorphism encapsulation optimisation authentication normalisation".split(),
    6: "int64 x2_buffer 0xFF3A retry_3 v2.1.4 SHA-256 400ms 99.9% utf-8 base64".split(),
    7: "lambda:=>{} try/catch req.body ==!== <div/> npm_i --force git@main".split(),
}

# Survival ladder: each stage pulls from a harder pool.
SURVIVAL_STAGES = [
    {"stage": 1, "label": "Warm-up", "source": "words", "band": 1},
    {"stage": 2, "label": "Longer words", "source": "words", "band": 2},
    {"stage": 3, "label": "Full sentences", "source": "passage", "band": 3},
    {"stage": 4, "label": "Numbers & symbols", "source": "passage", "band": 6},
    {"stage": 5, "label": "Code", "source": "passage", "band": 7},
]
