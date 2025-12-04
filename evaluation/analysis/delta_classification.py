from collections import Counter


delta_reasons = ["debugging",
                 "command_wrong",
                 "flag_wrong",
                 "exploration",
                 "optimization",
                 "llm_assist",
                 "replacement",
                 "input_source",
                 "behavior",
                 "aggregation",
                 "summary",
                 "visualization"
                 ]

DELTAS = {
    "beginner": [
        {"change_reason": "flag_wrong", "type": "mod"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "flag_wrong", "type": "mod"},
        {"change_reason": "aggregation", "type": "add"},
        {"change_reason": "optimization", "type": ["del", "mod"]},
        {"change_reason": "exploration", "type": "mod"},
        {"change_reason": "flag_wrong", "type": "mod"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "flag_wrong", "type": "mod"},
        {"change_reason": "aggregation", "type": "add"},
        {"change_reason": "flag_wrong", "type": "mod"},
    ],
    "bio": [
        {"change_reason": "input_source", "type": ["mod", "add"]},
        {"change_reason": "behavior", "type": "add"},
        {"change_reason": "input_source", "type": "mod"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
    ],
    "covid": [
        {"change_reason": "exploration", "type": ["add", "mod"]},
        {"change_reason": "exploration", "type": "mod"},
        {"change_reason": "exploration", "type": ["mod", "del"]},
        {"change_reason": "exploration", "type": ["add", "del"]},
    ],
    "dpt": [
        {"change_reason": "optimization", "type": "del"},
        {"change_reason": "flag_wrong", "type": "add"},
        {"change_reason": "input_source", "type": "mod"},
        {"change_reason": "visualization", "type": "add"},
    ],
    "file-mod": [
        {"change_reason": "llm_assist", "type": "add"},
        {"change_reason": "debugging", "type": ["add", "del"]},
        {"change_reason": "llm_assist", "type": "add"},
        {"change_reason": "optimization", "type": ["add", "mod"]},
        {"change_reason": "llm_assist", "type": "add"},
        {"change_reason": "optimization", "type": ["del", "add"]},
    ],
    "image": [
        {"change_reason": "debugging", "type": "mod"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "llm_assist", "type": ["add", "mod"]},
        {"change_reason": "optimization", "type": "mod"},
        {"change_reason": "debugging", "type": "mod"},
    ],
    "nginx": [
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "aggregation", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "replacement", "type": ["add", "del"]},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "aggregation", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "aggregation", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "aggregation", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "summary", "type": "add"},
        {"change_reason": "aggregation", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "flag_wrong", "type": "mod"},
        {"change_reason": "command_wrong", "type": "add"},
    ],
    "ngram": [
        {"change_reason": "behavior", "type": "add"},
        {"change_reason": "behavior", "type": "add"},
    ],
    "uppercase": [
        {"change_reason": "behavior", "type": "add"},
    ],
    "poet": [
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
    ],
    "spell": [
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
        {"change_reason": "behavior", "type": "add"},
        {"change_reason": "behavior", "type": "add"},
        {"change_reason": "debugging", "type": "add"},
    ],
    "unixfun": [
        {"change_reason": "exploration", "type": "mod"},
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "exploration", "type": ["del", "add"]},
        {"change_reason": "exploration", "type": "mod"},
        {"change_reason": "exploration", "type": ["del", "mod", "add"]},
    ],
    "weather": [
        {"change_reason": "exploration", "type": "add"},
        {"change_reason": "exploration", "type": "add"},
    ],
    "dict": [
        {"change_reason": "summary", "type": "add"},
    ]
}


assert all(delta["change_reason"] in delta_reasons for deltas in DELTAS.values() for delta in deltas)
assert all(any(delta["change_reason"] == reason for deltas in DELTAS.values() for delta in deltas) for reason in delta_reasons)

def canon_type(t):
    if isinstance(t, list):
        return tuple(sorted(t))
    return (t,)

def encode_runs(deltas):
    runs = []
    prev = None
    count = 0
    for d in deltas:
        key = (d["change_reason"], canon_type(d["type"]))
        if key == prev:
            count += 1
        else:
            if prev is not None:
                runs.append((count, *prev))
            prev = key
            count = 1
    if prev is not None:
        runs.append((count, *prev))
    return runs

def encode_totals_unordered(deltas):
    ctr = Counter((d["change_reason"], canon_type(d["type"])) for d in deltas)
    return [(c, r, t) for (r, t), c in ctr.items()]

def reason_letter(reason: str) -> str:
    return reason[0].upper()

def type_tag(types_tuple) -> str:
    return "".join(types_tuple)  # e.g. ("add","mod") -> "add-mod"

def latex_for_runs(runs):
    parts = []
    for count, reason, types_tuple in runs:
        R = reason_letter(reason)
        tag = type_tag(types_tuple)
        C = count if count > 1 else ""
        macro = f"\\CB{{\\ttt{{{C}{R}}}}}{{{tag}}}"
        parts.append(macro)
    return "".join(parts)

# Emit LaTeX table rows
ordered_benchmarks = ["dpt", "bio", "dict", "ngram", "uppercase", "unixfun", "nginx", "weather", "covid", "spell",
                      "poet", "image", "file-mod", "beginner"]
for name in ordered_benchmarks:
    row = latex_for_runs(encode_totals_unordered(DELTAS[name]))
    print(f"{row}")
