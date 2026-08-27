#!/usr/bin/env python3
"""Summarize a meal-tracker log.csv into per-day and period totals.

Usage:
    python3 summarize_log.py data/log.csv [--days N]

Prints per-day totals for calories/protein/carbs/fat, plus the average
over the selected period (default: last 7 days, including today).
Rows with missing/blank numeric fields are treated as 0 for that field
and flagged in the output so nothing is silently dropped.
"""
import argparse
import csv
import sys
from collections import OrderedDict
from datetime import date, datetime, timedelta


def parse_float(value):
    value = (value or "").strip()
    if not value:
        return 0.0, True  # (parsed_value, was_missing)
    try:
        return float(value), False
    except ValueError:
        return 0.0, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--days", type=int, default=7,
                         help="How many days back to include (default 7)")
    args = parser.parse_args()

    try:
        with open(args.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"No log found at {args.csv_path} yet — nothing to summarize.")
        sys.exit(0)

    if not rows:
        print("Log file exists but has no entries yet.")
        sys.exit(0)

    cutoff = date.today() - timedelta(days=args.days - 1)

    per_day = OrderedDict()
    missing_fields = 0
    skipped_bad_date = 0

    for row in rows:
        raw_date = (row.get("date") or "").strip()
        try:
            d = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            skipped_bad_date += 1
            continue
        if d < cutoff:
            continue

        cal, m1 = parse_float(row.get("calories"))
        pro, m2 = parse_float(row.get("protein_g"))
        carb, m3 = parse_float(row.get("carbs_g"))
        fat, m4 = parse_float(row.get("fat_g"))
        if any([m1, m2, m3, m4]):
            missing_fields += 1

        bucket = per_day.setdefault(d, {"calories": 0.0, "protein_g": 0.0,
                                         "carbs_g": 0.0, "fat_g": 0.0, "meals": 0})
        bucket["calories"] += cal
        bucket["protein_g"] += pro
        bucket["carbs_g"] += carb
        bucket["fat_g"] += fat
        bucket["meals"] += 1

    if not per_day:
        print(f"No entries found in the last {args.days} day(s).")
        sys.exit(0)

    print(f"Daily totals (last {args.days} day(s), {cutoff.isoformat()} to {date.today().isoformat()}):\n")
    print(f"{'Date':<12}{'Meals':<7}{'Calories':<10}{'Protein g':<11}{'Carbs g':<10}{'Fat g':<8}")
    for d in sorted(per_day):
        b = per_day[d]
        print(f"{d.isoformat():<12}{b['meals']:<7}{b['calories']:<10.0f}"
              f"{b['protein_g']:<11.0f}{b['carbs_g']:<10.0f}{b['fat_g']:<8.0f}")

    n = len(per_day)
    avg_cal = sum(b["calories"] for b in per_day.values()) / n
    avg_pro = sum(b["protein_g"] for b in per_day.values()) / n
    avg_carb = sum(b["carbs_g"] for b in per_day.values()) / n
    avg_fat = sum(b["fat_g"] for b in per_day.values()) / n
    total_meals = sum(b["meals"] for b in per_day.values())

    print(f"\nPeriod average per day ({n} day(s) with entries, {total_meals} meal(s) total):")
    print(f"  Calories: {avg_cal:.0f}")
    print(f"  Protein:  {avg_pro:.0f} g")
    print(f"  Carbs:    {avg_carb:.0f} g")
    print(f"  Fat:      {avg_fat:.0f} g")

    if missing_fields:
        print(f"\nNote: {missing_fields} row(s) had a blank/unparseable numeric field, treated as 0.")
    if skipped_bad_date:
        print(f"Note: {skipped_bad_date} row(s) skipped due to unparseable date (expected YYYY-MM-DD).")


if __name__ == "__main__":
    main()
