#!/usr/bin/env python3
"""Day 40: model comparison refresh — re-score all 5 methods on the
longer window now that real portal rows exist.

Method (identical to Day 19 so the numbers are comparable):
  * Same features, same split rule, same hyperparameters: features =
    lag1, lag2, lag3, MA3, MA7 (all computed on past prices only,
    leak-free, per market-commodity series); split is by time, test =
    final 20% of distinct arrival dates, train = everything earlier.
    One OLS and one RandomForestRegressor per commodity (80 trees,
    max_depth=6, max_features=3, random_state=19).
  * The five methods: Persistence, MA3, MA7, Linear regression (OLS),
    Random forest — scored on the exact same test rows.
  * What's new vs Day 19: the window is 49 distinct dates (29 Sep –
    17 Nov) instead of 32, and the test window (08–17 Nov) is made
    entirely of real portal rows — per-mandi sample feed ended 29 Oct,
    National portal pulls began 30 Oct. So this is the first
    5-method comparison scored on real published prices, not seeded
    sample. Provenance is read off source_file: files dated
    2026-10-30 or later are portal pulls (verified: every such file
    is 1-market National or a -mandi extract; every earlier file is
    the 8-market × 3-commodity sample).
  * Caveat, stated plainly: the TRAIN set still mixes sample (Sep–Oct
    per-mandi) with real rows, and per-mandi lag features bridge the
    30 Oct – 05 Nov hole (shift is by row position, so lag1 for 06 Nov
    is the 29 Oct sample value). Only the scored test rows are real.

Reads : data/processed/mandi_prices_clean.csv
Writes: data/processed/model_comparison_refresh.csv
        charts/model_comparison_refresh_YYYY-MM-DD.svg
        reports/day40_model_comparison_refresh.md
Prints: per-commodity + overall test MAE for all 5 methods,
        Day 19 vs Day 40 overall MAE, verification result.
"""
import datetime as dt
import math
import os

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
OUT = os.path.join(BASE_DIR, "data", "processed", "model_comparison_refresh.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TODAY = dt.date.today().isoformat()

COMMS = ["Onion", "Potato", "Tomato"]
FEATURES = ["lag1", "lag2", "lag3", "ma3", "ma7"]
METHODS = ["fc_persist", "fc_ma3", "fc_ma7", "fc_lr", "fc_rf"]
LABELS = {"fc_persist": "Persistence", "fc_ma3": "MA3 forecast",
          "fc_ma7": "MA7 forecast", "fc_lr": "Linear regression",
          "fc_rf": "Random forest"}
COLORS = {"Persistence": "#37474f", "MA3 forecast": "#e67e22",
          "MA7 forecast": "#e53935", "Linear regression": "#2e86ab",
          "Random forest": "#43a047"}
# Day 19 overall test MAE (test 24–29 Oct, n=144, all sample) — the
# baseline this refresh is measured against. Different test window,
# so this is a refresh, not a paired comparison.
DAY19_OVERALL_MAE = {"fc_persist": 246.94, "fc_ma3": 226.97,
                     "fc_ma7": 216.20, "fc_lr": 207.22, "fc_rf": 221.60}
PORTAL_FROM = "mandi_prices_2026-10-30.csv"


def add_features(df):
    df = df.sort_values(["market", "commodity", "arrival_date"]).copy()
    grp = df.groupby(["market", "commodity"])["modal_price"]
    df["lag1"] = grp.shift(1)
    df["lag2"] = grp.shift(2)
    df["lag3"] = grp.shift(3)
    df["ma3"] = grp.transform(lambda s: s.rolling(3).mean().shift(1))
    df["ma7"] = grp.transform(lambda s: s.rolling(7).mean().shift(1))
    df["fc_persist"] = df["lag1"]
    df["fc_ma3"] = df["ma3"]
    df["fc_ma7"] = df["ma7"]
    return df


def fit_ols(sub):
    X = np.column_stack([np.ones(len(sub)), sub["lag1"], sub["lag2"],
                         sub["lag3"]])
    y = sub["modal_price"].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def apply_ols(sub, beta):
    return (beta[0] + beta[1] * sub["lag1"] + beta[2] * sub["lag2"]
            + beta[3] * sub["lag3"]).to_numpy(dtype=float)


def fit_forest(sub):
    rf = RandomForestRegressor(n_estimators=80, max_depth=6,
                               max_features=3, random_state=19, n_jobs=1)
    rf.fit(sub[FEATURES].to_numpy(dtype=float),
           sub["modal_price"].to_numpy(dtype=float))
    return rf


def metrics(y, pred):
    err = y - pred
    return {
        "n": len(y),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "mape": float(np.mean(np.abs(err) / y) * 100),
    }


def make_chart(summary, overall, path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.6))
    x = np.arange(len(COMMS))
    w = 0.15
    for i, m in enumerate(METHODS):
        vals = [summary[c][m]["mae"] for c in COMMS]
        ax1.bar(x + (i - 2) * w, vals, w, label=LABELS[m],
                color=COLORS[LABELS[m]])
    ax1.set_xticks(x)
    ax1.set_xticklabels(COMMS)
    ax1.set_ylabel("Test MAE (Rs/qtl)")
    ax1.set_title("Test MAE — all five methods (real rows)", fontsize=11,
                  fontweight="bold")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(axis="y", alpha=0.3)

    x2 = np.arange(len(METHODS))
    d19 = [DAY19_OVERALL_MAE[m] for m in METHODS]
    d40 = [overall[m]["mae"] for m in METHODS]
    ax2.bar(x2 - 0.2, d19, 0.4, label="Day 19 (sample test)",
            color="#b0bec5")
    ax2.bar(x2 + 0.2, d40, 0.4, label="Day 40 (real test)",
            color="#2e86ab")
    ax2.set_xticks(x2)
    ax2.set_xticklabels([LABELS[m] for m in METHODS], rotation=25,
                        ha="right", fontsize=8)
    ax2.set_ylabel("Overall test MAE (Rs/qtl)")
    ax2.set_title("Day 19 vs Day 40 — overall MAE", fontsize=11,
                  fontweight="bold")
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3)
    fig.suptitle(f"Day 40 — Model comparison refresh (test set, to "
                 f"{TODAY})", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def verify(train, test, forests, betas):
    """Three independent checks, mirroring Day 19's verification.
    1. Determinism: re-fitting each forest with the same seed
       reproduces every test prediction exactly.
    2. Importances sum to 1.0 for every commodity's forest.
    3. Spot-check: walk the first tree of the Onion forest by hand
       on the last test row and confirm the leaf value equals that
       tree's prediction, and the forest mean equals the stored fc_rf.
    4. OLS hand-check: recompute one test row's fc_lr from the
       coefficients by hand.
    """
    for comm in COMMS:
        tr = train[(train["commodity"] == comm)
                   & train["lag3"].notna() & train["ma7"].notna()]
        rf2 = fit_forest(tr)
        te = test[test["commodity"] == comm].copy()
        p1 = forests[comm].predict(te[FEATURES].to_numpy(dtype=float))
        p2 = rf2.predict(te[FEATURES].to_numpy(dtype=float))
        assert np.array_equal(p1, p2), f"non-deterministic forest {comm}"
        total = float(forests[comm].feature_importances_.sum())
        assert abs(total - 1.0) < 1e-9, (comm, total)
    comm = "Onion"
    rf = forests[comm]
    te = test[test["commodity"] == comm].copy()
    row = te.iloc[-1]
    x = row[FEATURES].to_numpy(dtype=float)
    tree = rf.estimators_[0].tree_
    node = 0
    while tree.children_left[node] != tree.children_right[node]:
        feat, thr = tree.feature[node], tree.threshold[node]
        node = (tree.children_left[node] if x[feat] <= thr
                else tree.children_right[node])
    leaf_val = float(tree.value[node, 0, 0])
    tree_pred = float(rf.estimators_[0].predict(x.reshape(1, -1))[0])
    assert abs(leaf_val - tree_pred) < 1e-9, (leaf_val, tree_pred)
    rf_pred = float(rf.predict(x.reshape(1, -1))[0])
    stored = float(row["fc_rf"])
    assert abs(rf_pred - stored) < 1e-9, (rf_pred, stored)
    # OLS hand-check on the same row.
    beta = betas[comm]
    manual = float(beta[0] + beta[1] * row["lag1"] + beta[2] * row["lag2"]
                   + beta[3] * row["lag3"])
    assert abs(manual - float(row["fc_lr"])) < 0.01, (manual, row["fc_lr"])
    return (row["market"], row["arrival_date"], leaf_val, rf_pred, manual)


def write_report(split, summary, overall, comp, verify_res, chart_name,
                 path):
    market, row_date, leaf_val, rf_pred, manual = verify_res
    lines = [
        "# Day 40 — Model comparison refresh: all 5 methods re-scored "
        "on real portal rows",
        "",
        "## Method (read this first)",
        "",
        "Identical to Day 19 so the numbers are comparable: features",
        "lag1/lag2/lag3 + MA3/MA7 (past prices only, leak-free), one OLS",
        "and one random forest (80 trees, depth 6, max_features 3,",
        "seed 19) per commodity, time split with test = final 20% of",
        "distinct arrival dates. The five methods — Persistence, MA3,",
        "MA7, Linear regression, Random forest — are scored on the",
        "exact same test rows. What changed is the window: 49 distinct",
        "dates (29 Sep – 17 Nov) instead of 32, and the test window",
        f"({split[2].date()} – {split[3].date()}) is made entirely of",
        "real portal rows — the per-mandi sample feed ended 29 Oct and",
        "National portal pulls began 30 Oct. Provenance is read off",
        "`source_file`: files dated 2026-10-30 or later are portal",
        "pulls (verified: every such file is a 1-market National table",
        "or a `-mandi` extract; every earlier file is the 8-market ×",
        "3-commodity sample).",
        "",
        "Caveat, stated plainly: the TRAIN set still mixes sample",
        "(Sep–Oct per-mandi) with real rows, and per-mandi lag features",
        "bridge the 30 Oct – 05 Nov hole (shift is by row position, so",
        "lag1 for 06 Nov is the 29 Oct sample value). Only the scored",
        "test rows are real — this refresh measures how the methods do",
        "on real prices, not whether training on real-only data would",
        "change the ranking. That is a follow-up once the real window",
        "is long enough to train on alone.",
        "",
        "## Split",
        "",
        f"- Train dates: {split[0].date()} to {split[1].date()} "
        f"({split[4]} rows)",
        f"- Test dates: {split[2].date()} to {split[3].date()} "
        f"({split[5]} rows scored)",
        f"- Test rows by provenance: {split[6]} real portal / "
        f"{split[7]} sample",
        f"- Test rows by market: " +
        ", ".join(f"{m} {n}" for m, n in split[8].items()),
        "",
        "## Out-of-sample results — test set only (all real rows)",
        "",
        "| Commodity | Method | n | MAE Rs/qtl | RMSE Rs/qtl | MAPE % |",
        "|---|---|---|---|---|---|",
    ]
    for comm in COMMS:
        for m in METHODS:
            s = summary[comm][m]
            lines.append(f"| {comm} | {LABELS[m]} | {s['n']} | {s['mae']:.2f} | "
                         f"{s['rmse']:.2f} | {s['mape']:.2f} |")
    lines += [
        "",
        "## Overall test set (all commodities pooled)",
        "",
        "| Method | n | MAE Rs/qtl | RMSE Rs/qtl | MAPE % |",
        "|---|---|---|---|---|",
    ]
    for m in METHODS:
        s = overall[m]
        lines.append(f"| {LABELS[m]} | {s['n']} | {s['mae']:.2f} | "
                     f"{s['rmse']:.2f} | {s['mape']:.2f} |")
    lines += [
        "",
        "## Day 19 vs Day 40 — overall MAE (different test windows)",
        "",
        "Day 19's test window (24–29 Oct, n=144) was all sample; Day 40's",
        f"({split[2].date()} – {split[3].date()}, n={split[5]}) is all real. "
        "Same methods, same split rule, same hyperparameters — the",
        "comparison shows how the ranking holds up once real prices",
        "replace seeded ones, not a paired A/B on identical rows.",
        "",
        "| Method | Day 19 MAE | Day 40 MAE | Change |",
        "|---|---|---|---|",
    ]
    for m in METHODS:
        d19 = DAY19_OVERALL_MAE[m]
        d40 = overall[m]["mae"]
        delta = d40 - d19
        lines.append(f"| {LABELS[m]} | {d19:.2f} | {d40:.2f} | "
                     f"{delta:+.2f} |")
    lines += [
        "",
        "## Verdict",
        "",
    ]
    best = min(METHODS, key=lambda m: overall[m]["mae"])
    worst = max(METHODS, key=lambda m: overall[m]["mae"])
    lines.append(f"- **Overall winner: {LABELS[best]}** "
                 f"(MAE Rs {overall[best]['mae']:.2f}/qtl, n="
                 f"{overall[best]['n']}).")
    for comm in COMMS:
        cb = min(METHODS, key=lambda m: summary[comm][m]["mae"])
        line = (f"- **{comm}**: {LABELS[cb]} wins "
                f"(Rs {summary[comm][cb]['mae']:.2f}/qtl)")
        if cb != "fc_persist":
            line += (f"; persistence Rs "
                     f"{summary[comm]['fc_persist']['mae']:.2f}/qtl")
        lines.append(line + ".")
    lines.append(f"- Widest gap is {LABELS[worst]} at "
                 f"Rs {overall[worst]['mae']:.2f}/qtl.")
    lines += [
        "",
        "## Reading the result",
        "",
    ]
    if best == "fc_lr":
        read = ("The linear model keeps the crown on real prices too — "
                "the Day 19 ranking survives the switch from seeded to "
                "published data, which is the first evidence the OLS "
                "champion is not a sample artefact. ")
    elif best == "fc_persist":
        read = ("Persistence wins on real prices — on this window the "
                "market moves too little day to day for any lag model to "
                "add skill, and the fancy methods are mostly fitting "
                "noise. ")
    else:
        read = (f"{LABELS[best]} takes the crown on real prices — the "
                "ranking flipped once seeded data left the test set, "
                "which is exactly why the refresh was scheduled. ")
    lines += [
        read + "The honest limit stays: the test window is short "
        f"({split[5]} rows, {split[2].date()} – {split[3].date()}) and "
        "the train set still contains sample history, so treat the "
        "ranking as the first real-data datapoint, not a final verdict. "
        "Re-run this refresh when the real-only window reaches a month "
        "of test dates, and then train on real rows alone.",
        "",
        "## Verification",
        "",
        f"Three independent checks, all passed: (1) re-fitting each "
        f"commodity's forest with the same seed reproduces every test "
        f"prediction exactly; (2) every forest's feature importances "
        f"sum to 1.000; (3) the final {market} Onion test row "
        f"({row_date.date()}) was verified by hand — walking the first "
        f"tree's split rules lands on a leaf worth Rs {leaf_val:.2f}/qtl, "
        f"matching that tree's prediction, and averaging all 80 trees "
        f"gives Rs {rf_pred:.2f}/qtl, matching the stored forecast to "
        f"the paisa; the same row's OLS value recomputed from the "
        f"coefficients by hand gives Rs {manual:.2f}/qtl, matching "
        f"fc_lr.",
        "",
        f"![Model comparison refresh](../charts/{chart_name})",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    df = pd.read_csv(PROCESSED)
    df["arrival_date"] = pd.to_datetime(df["arrival_date"])
    df["is_real"] = df["source_file"] >= PORTAL_FROM
    df = add_features(df)

    dates = sorted(df["arrival_date"].dt.date.unique())
    n_test_dates = math.ceil(0.20 * len(dates))
    test_dates = dates[-n_test_dates:]
    cutoff = pd.Timestamp(test_dates[0])
    need = FEATURES + ["fc_persist", "fc_ma3", "fc_ma7"]
    train = df[(df["arrival_date"] < cutoff)
               & df["lag3"].notna() & df["ma7"].notna()].copy()
    test = df[(df["arrival_date"] >= cutoff)
              & df[need].notna().all(axis=1)].copy()

    summary, overall, forests, betas = {}, {}, {}, {}
    for comm in COMMS:
        tr = train[train["commodity"] == comm].copy()
        te = test[test["commodity"] == comm].copy()
        beta = fit_ols(tr)
        betas[comm] = beta
        te["fc_lr"] = apply_ols(te, beta)
        rf = fit_forest(tr)
        forests[comm] = rf
        te["fc_rf"] = rf.predict(te[FEATURES].to_numpy(dtype=float))
        test.loc[te.index, ["fc_lr", "fc_rf"]] = te[["fc_lr", "fc_rf"]]
        y = te["modal_price"].to_numpy(dtype=float)
        summary[comm] = {m: metrics(y, te[m].to_numpy(dtype=float))
                         for m in METHODS}
    # Overall metrics are pooled over the SCORED rows only (the three
    # forecast commodities). The test set also holds National rows for
    # the other 21 commodities, which no method scores — including
    # them would make the overall MAE NaN.
    scored = test[test["commodity"].isin(COMMS)].copy()
    y_all = scored["modal_price"].to_numpy(dtype=float)
    overall = {m: metrics(y_all, scored[m].to_numpy(dtype=float))
               for m in METHODS}

    cols = ["market", "commodity", "arrival_date", "modal_price", "lag1",
            "lag2", "lag3", "ma3", "ma7", "is_real", "source_file",
            "fc_persist", "fc_ma3", "fc_ma7", "fc_lr", "fc_rf"]
    out = scored[cols].copy()
    out["arrival_date"] = out["arrival_date"].dt.strftime("%Y-%m-%d")
    out.to_csv(OUT, index=False)

    split = (train["arrival_date"].min(), train["arrival_date"].max(),
             scored["arrival_date"].min(), scored["arrival_date"].max(),
             len(train), len(scored), int(scored["is_real"].sum()),
             int((~scored["is_real"]).sum()),
             scored["market"].value_counts().to_dict())
    verify_res = verify(train, test, forests, betas)

    chart_name = f"model_comparison_refresh_{TODAY}.svg"
    make_chart(summary, overall, os.path.join(CHARTS_DIR, chart_name))
    write_report(split, summary, overall, None, verify_res, chart_name,
                 os.path.join(REPORTS_DIR,
                              "day40_model_comparison_refresh.md"))

    for comm in COMMS:
        s = summary[comm]
        print(f"{comm}: OLS {s['fc_lr']['mae']:.2f} | RF "
              f"{s['fc_rf']['mae']:.2f} | MA7 {s['fc_ma7']['mae']:.2f} | "
              f"MA3 {s['fc_ma3']['mae']:.2f} | persist "
              f"{s['fc_persist']['mae']:.2f} (n={s['fc_lr']['n']})")
    print(f"Overall: " + " | ".join(
        f"{LABELS[m]} {overall[m]['mae']:.2f}" for m in METHODS) +
        f" (n={overall['fc_lr']['n']})")
    print(f"Test window {split[2].date()}–{split[3].date()}: "
          f"{split[6]} real / {split[7]} sample rows")
    print(f"Hand-check {verify_res[0]} Onion {verify_res[1].date()}: "
          f"tree leaf Rs {verify_res[2]:.2f} MATCHES, forest "
          f"Rs {verify_res[3]:.2f} MATCHES, OLS Rs {verify_res[4]:.2f} "
          f"MATCHES")


if __name__ == "__main__":
    main()
