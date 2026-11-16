"""Relative BRD risk from minute rows.

A score compares cows in this pen. It is not a diagnosis.
"""

from __future__ import annotations

FEEDING = "feeding"
LYING = "lying"
VISIBLE_FLOOR = 0.4
COMPRESS_BAND = 0.15
FRAGILE_MINUTES = 15
MEAL_COWS = 7
WINDOW = 30


def rank_minutes(rows: list[dict]) -> list[dict]:
    """One new dict per cow. Highest visible-only concern first."""
    if not rows:
        return []
    by_cow = _group(rows)
    visible_herd = _herd_deltas(by_cow, visible_only=True)
    all_herd = _herd_deltas(by_cow, visible_only=False)
    scored: list[dict] = []
    blanks: list[dict] = []
    for cow_id, cow_rows in by_cow.items():
        card = _cow_card(cow_id, cow_rows, visible_herd, all_herd, rows)
        if card["risk_visible"] is None:
            blanks.append(card)
        else:
            scored.append(card)
    ordered = _with_ranks(scored, _scale(scored, "risk_visible"), _scale(scored, "risk_all"))
    ordered = _mark_compressed(ordered)
    ordered = _adjacent(ordered)
    blanks = sorted(blanks, key=lambda card: card["cow_id"])
    return ordered + blanks


def _group(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row["cow_id"]), []).append(row)
    return grouped


def _day_rows(rows: list[dict], day: int) -> list[dict]:
    return [row for row in rows if int(row["day"]) == day]


def _behavior_rate(rows: list[dict], behavior: str, visible_only: bool) -> float | None:
    pool = [row for row in rows if row["visible"]] if visible_only else list(rows)
    if not pool:
        return None
    hits = sum(1 for row in pool if row["visible"] and row["behavior"] == behavior)
    return hits / len(pool)


def _alone_rate(rows: list[dict], visible_only: bool) -> float | None:
    pool = [row for row in rows if row["visible"]] if visible_only else list(rows)
    if not pool:
        return None
    hits = sum(1 for row in pool if row["visible"] and row.get("alone"))
    return hits / len(pool)


def _delta(day2: float | None, day1: float | None) -> float | None:
    if day2 is None or day1 is None:
        return None
    return day2 - day1


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _herd_deltas(by_cow: dict[str, list[dict]], visible_only: bool) -> dict[str, float]:
    buckets: dict[str, list[float]] = {"feed": [], "lying": [], "alone": []}
    for cow_rows in by_cow.values():
        day1 = _day_rows(cow_rows, 1)
        day2 = _day_rows(cow_rows, 2)
        pairs = (
            ("feed", _delta(_behavior_rate(day2, FEEDING, visible_only), _behavior_rate(day1, FEEDING, visible_only))),
            ("lying", _delta(_behavior_rate(day2, LYING, visible_only), _behavior_rate(day1, LYING, visible_only))),
            ("alone", _delta(_alone_rate(day2, visible_only), _alone_rate(day1, visible_only))),
        )
        for key, value in pairs:
            if value is not None:
                buckets[key].append(value)
    return {key: _mean(values) if values else 0.0 for key, values in buckets.items()}


def _concern(day1: list[dict], day2: list[dict], herd: dict[str, float], visible_only: bool) -> float | None:
    feed_delta = _delta(_behavior_rate(day2, FEEDING, visible_only), _behavior_rate(day1, FEEDING, visible_only))
    lying_delta = _delta(_behavior_rate(day2, LYING, visible_only), _behavior_rate(day1, LYING, visible_only))
    alone_delta = _delta(_alone_rate(day2, visible_only), _alone_rate(day1, visible_only))
    parts: list[float] = []
    if feed_delta is not None:
        parts.append(herd["feed"] - feed_delta)
    if lying_delta is not None:
        parts.append(lying_delta - herd["lying"])
    if alone_delta is not None:
        parts.append(alone_delta - herd["alone"])
    if not parts:
        return None
    return _mean(parts)


def _cow_card(
    cow_id: str,
    cow_rows: list[dict],
    visible_herd: dict[str, float],
    all_herd: dict[str, float],
    all_rows: list[dict],
) -> dict:
    fraction = sum(1 for row in cow_rows if row["visible"]) / len(cow_rows)
    day1 = _day_rows(cow_rows, 1)
    day2 = _day_rows(cow_rows, 2)
    skips = None if not day1 or not day2 else _meal_skips(all_rows, cow_id)
    visible_concern = _concern(day1, day2, visible_herd, True)
    all_concern = _concern(day1, day2, all_herd, False)
    if skips is not None and visible_concern is not None:
        visible_concern = visible_concern + skips
    card = {
        "cow_id": cow_id,
        "visible_fraction": round(fraction, 4),
        "risk_visible": visible_concern,
        "risk_all": all_concern,
        "feed_drop_minutes": _feed_drop_minutes(day1, day2),
        "change_minute": _change_minute(day1, day2),
        "meal_skips": skips,
        "single_out": "yes",
        "single_out_reason": "",
        "rank": None,
        "minutes_to_swap": None,
        "stability": None,
    }
    if fraction < VISIBLE_FLOOR or visible_concern is None:
        reason = "visible fraction under 0.4" if fraction < VISIBLE_FLOOR else "no day-over-day term"
        return {**card, "risk_visible": None, "single_out": "no", "single_out_reason": reason}
    if _one_hour_dominates(day2):
        return {**card, "single_out": "no", "single_out_reason": "one hour holds the change"}
    return card


def _feed_drop_minutes(day1: list[dict], day2: list[dict]) -> int | None:
    if not day1 or not day2:
        return None

    def _count(rows: list[dict]) -> int:
        return sum(1 for row in rows if row["visible"] and row["behavior"] == FEEDING)

    return _count(day1) - _count(day2)


def _meal_skips(all_rows: list[dict], cow_id: str) -> float | None:
    """Day-2 herd-meal skip rate minus day-1. None when a day has no herd meal."""
    rates: list[float] = []
    for day in (1, 2):
        day_rows = _day_rows(all_rows, day)
        if not day_rows:
            return None
        skips: list[float] = []
        for minute in {int(row["minute"]) for row in day_rows}:
            at = [row for row in day_rows if int(row["minute"]) == minute]
            feeding = sum(1 for row in at if row["visible"] and row["behavior"] == FEEDING)
            if feeding < MEAL_COWS:
                continue
            hers = [row for row in at if str(row["cow_id"]) == cow_id]
            if len(hers) != 1 or not hers[0]["visible"]:
                continue
            skips.append(0.0 if hers[0]["behavior"] == FEEDING else 1.0)
        if not skips:
            return None
        rates.append(_mean(skips))
    return rates[1] - rates[0]


def _one_hour_dominates(day2: list[dict]) -> bool:
    visible = [row for row in day2 if row["visible"]]
    quiet = [row for row in visible if row["behavior"] != FEEDING]
    if len(quiet) < 2:
        return False
    hours: dict[int, int] = {}
    for row in quiet:
        hour = int(row["minute"]) // 60
        hours[hour] = hours.get(hour, 0) + 1
    return max(hours.values()) / len(quiet) > 0.5


def _change_minute(day1: list[dict], day2: list[dict]) -> int | None:
    if not day1 or not day2:
        return None
    start = 0
    while start + WINDOW <= 1440:
        window1 = [row for row in day1 if start <= int(row["minute"]) < start + WINDOW]
        window2 = [row for row in day2 if start <= int(row["minute"]) < start + WINDOW]
        rate1 = _behavior_rate(window1, FEEDING, True)
        rate2 = _behavior_rate(window2, FEEDING, True)
        if rate1 is not None and rate2 is not None and rate1 - rate2 >= 0.5:
            return start
        start += WINDOW
    return None


def _scale(cards: list[dict], key: str) -> dict[str, float]:
    raw = [card[key] for card in cards if card[key] is not None]
    if not raw:
        return {}
    low, high = min(raw), max(raw)
    span = high - low
    scaled: dict[str, float] = {}
    for card in cards:
        if card[key] is None:
            continue
        value = 0.5 if span == 0 else (card[key] - low) / span
        scaled[card["cow_id"]] = round(value, 4)
    return scaled


def _with_ranks(
    cards: list[dict],
    visible_scaled: dict[str, float],
    all_scaled: dict[str, float],
) -> list[dict]:
    merged = [
        {
            **card,
            "risk_visible": visible_scaled.get(card["cow_id"]),
            "risk_all": all_scaled.get(card["cow_id"]),
        }
        for card in cards
    ]
    merged.sort(key=lambda card: (-(card["risk_visible"] or 0.0), card["cow_id"]))
    return [{**card, "rank": index} for index, card in enumerate(merged, start=1)]


def _mark_compressed(ordered: list[dict]) -> list[dict]:
    if len(ordered) < 2:
        return ordered
    scores = [card["risk_visible"] for card in ordered]
    if max(scores) - min(scores) > COMPRESS_BAND:
        return ordered
    return [
        {**card, "single_out": "no", "single_out_reason": "pen scores compressed"}
        for card in ordered
    ]


def _adjacent(ordered: list[dict]) -> list[dict]:
    built: list[dict] = []
    for index, card in enumerate(ordered):
        if len(ordered) == 1:
            built.append({**card, "stability": "tied", "minutes_to_swap": None})
            continue
        if index + 1 >= len(ordered):
            built.append({**card, "stability": "stable", "minutes_to_swap": None})
            continue
        nxt = ordered[index + 1]
        if abs(card["risk_visible"] - nxt["risk_visible"]) < 0.01:
            built.append({**card, "stability": "tied", "minutes_to_swap": 0})
            continue
        left, right = card["feed_drop_minutes"], nxt["feed_drop_minutes"]
        gap = None if left is None or right is None else abs(left - right)
        tag = "fragile" if gap is not None and gap < FRAGILE_MINUTES else "stable"
        built.append({**card, "stability": tag, "minutes_to_swap": gap})
    return built
