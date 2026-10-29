#!/usr/bin/env python3
"""Day 19: random forest regressor, feature importances.

Method:
  * Same features, same time split, same test rows as Day 18:
    features = lag1, lag2, lag3 (prices from the past only, leak-free),
    plus MA3 and MA7 rolling means computed on past prices (shift(1)),
    per market-commodity series. Split is by time: test = final 20%
    of distinct arrival dates, train = everything earlier. The forest
    is fitted on TRAIN rows only and scored on the exact same test
    rows as persistence / MA3 / MA7 / OLS — apples-to-apples.
  * One RandomForestRegressor per commodity (80 trees, max_depth=6,
    max_features=3, random_state=19, n_jobs=-1), since the price level
    and dynamics differ across commodities and pooling would let the
    high-price commodity dominate the splits.
  * Feature importances = mean decrease in impurity (Gini/variance)
    across trees, normalised to sum to 1 — shows which lags the forest
    actually leans on.
  * Metrics per commodity and overall: MAE, RMSE, MAPE, alongside the
    Day 18 methods for the head-to-head.

Reads : data/processed/mandi_prices_clean.csv
Writes: data/processed/random_forest.csv      (test rows + rf forecast)
        charts/random_forest_YYYY-MM-DD.svg
        reports/day19_random_forest.md
Prints: per-commodity test MAE for all methods + verification result.
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
OUT = os.path.join(BASE_DIR, "data", "processed", "random_forest.csv")
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


def make_chart(summary, importances, path):
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
    ax1.set_title("Test MAE — all five methods", fontsize=11,
                  fontweight="bold")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(axis="y", alpha=0.3)

    y = np.arange(len(FEATURES))
    imp = [np.mean([importances[c][f] for c in COMMS]) for f in FEATURES]
    ax2.barh(y, imp, color="#43a047")
    ax2.set_yticks(y)
    ax2.set_yticklabels(FEATURES)
    ax2.set_xlabel("Mean importance (impurity decrease)")
    ax2.set_title("Random forest — mean feature importances",
                  fontsize=11, fontweight="bold")
    ax2.grid(axis="x", alpha=0.3)
    fig.suptitle(f"Day 19 — Random forest vs the baselines (test set, to "
                 f"{TODAY})", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def verify(train, test, forests, summary):
    """Three independent checks the module's numbers are trustworthy.

    1. Determinism: re-fitting with the same seed reproduces every
       test prediction exactly (RandomForestRegressor randomness is
       fully controlled by random_state).
    2. Importances sum to 1.0 for every commodity's forest.
    3. Spot-check: recompute one test prediction by walking the first
       tree by hand — apply the same split rules along the path and
       confirm the leaf value equals the tree's prediction.
    """
    # 1. Re-fit determinism.
    for comm in COMMS:
        tr = train[(train["commodity"] == comm)
                   & train["lag3"].notna() & train["ma7"].notna()]
        rf2 = fit_forest(tr)
        te = test[test["commodity"] == comm].copy()
        p1 = forests[comm].predict(te[FEATURES].to_numpy(dtype=float))
        p2 = rf2.predict(te[FEATURES].to_numpy(dtype=float))
        assert np.array_equal(p1, p2), f"non-deterministic forest {comm}"
        # 2. Importances sum to 1.
        total = float(forests[comm].feature_importances_.sum())
        assert abs(total - 1.0) < 1e-9, (comm, total)
    # 3. Walk the first tree of the Onion forest by hand.
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
    return (row["market"], row["arrival_date"], leaf_val, rf_pred)


def write_report(split, summary, overall, importances, verify_res,
                 chart_name, path):
    market, row_date, leaf_val, rf_pred = verify_res
    lines = [
        "# Day 19 — Random forest regressor, feature importances",
        "",
        "## Method (read this first)",
        "",
        "A random forest averages 80 regression trees, each trained on a",
        "bootstrap sample of the train set, each split considering only",
        "a random subset of 3 of the 5 features. Averaging de-correlated",
        "trees cuts the variance that makes a single tree brittle — the",
        "same 'smoother wins' lesson Day 18's MA7 taught, but learned",
        "from the data instead of hand-picked. The feature set extends",
        "Day 17's lag1/lag2/lag3 with MA3 and MA7 rolling means (all",
        "computed from past prices only — leak-free). One forest per",
        "commodity: Onion, Potato and Tomato trade at different price",
        "levels and pooling them would let the high-price commodity",
        "dominate the splits. Fitted on TRAIN rows only, scored on the",
        "exact same test rows as Day 18's four methods.",
        "",
        "Hyperparameters (fixed, not tuned — Day 22's job):",
        "",
        "- n_estimators=80, max_depth=6, max_features=3, random_state=19",
        "",
        "## Split",
        "",
        f"- Train dates: {split[0]} to {split[1]} ({split[4]} rows)",
        f"- Test dates: {split[2]} to {split[3]} ({split[5]} rows scored)",
        "",
        "## Out-of-sample results — test set only",
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
        "## Feature importances (mean decrease in impurity, per commodity)",
        "",
        "| Commodity | " + " | ".join(FEATURES) + " |",
        "|" + "---|" * (len(FEATURES) + 1),
    ]
    for comm in COMMS:
        imp = importances[comm]
        lines.append("| " + comm + " | " +
                     " | ".join(f"{imp[f]:.3f}" for f in FEATURES) + " |")
    lines += [
        "",
        "## Does the forest beat the linear model?",
        "",
    ]
    for comm in COMMS:
        rf_mae = summary[comm]["fc_rf"]["mae"]
        lr_mae = summary[comm]["fc_lr"]["mae"]
        verb = "beats" if rf_mae < lr_mae else "does NOT beat"
        lines.append(f"- **{comm}**: random forest Rs {rf_mae:.2f}/qtl "
                     f"{verb} linear regression (Rs {lr_mae:.2f}/qtl).")
    rf_overall = overall["fc_rf"]["mae"]
    lr_overall = overall["fc_lr"]["mae"]
    lines += [
        "",
        f"**Overall: random forest Rs {rf_overall:.2f}/qtl vs linear "
        f"regression Rs {lr_overall:.2f}/qtl.**",
        "",
        "## Reading the result",
        "",
    ]
    if rf_overall < lr_overall:
        read = ("The forest wins overall out-of-sample — its edge comes "
                "from capturing the non-linear interactions the linear "
                "model misses (importances spread across lags and MAs "
                "rather than loading on lag1 alone).")
    else:
        read = ("The linear model holds the crown overall — on this "
                "short, noisy sample the forest's extra capacity does not "
                "pay for itself; it likely chases jitter that MA3/OLS "
                "smooth over. That verdict flips if real portal data "
                "carries genuine non-linear dynamics, and Day 22's "
                "hyperparameter search will test whether depth/trees "
                "recover an edge.")
    lines += [
        read + " On sample data the series are short (a month) and the "
        "day-to-day moves are largely independent noise, so any "
        "lag-based model is mostly fitted curve, not forecasting skill "
        "— the honest framing stays: the time-split table above is the "
        "bar every model must clear, and Day 20's forecast-vs-actual "
        "tracking will show day by day where the forest diverges from "
        "the linear model on the test window.",
        "",
        "## Verification",
        "",
        f"Three independent checks, all passed: (1) re-fitting each "
        f"commodity's forest with the same seed reproduces every test "
        f"prediction exactly — the randomness is fully controlled; "
        f"(2) every forest's feature importances sum to 1.000; (3) the "
        f"final {market} Onion test row ({row_date.date()}) was verified "
        f"by hand — walking the first tree's split rules along the "
        f"prediction path lands on a leaf worth Rs {leaf_val:.2f}/qtl, "
        f"matching that tree's prediction, and averaging all 80 trees "
        f"gives Rs {rf_pred:.2f}/qtl, matching the module's stored "
        f"forecast to the paisa.",
        "",
        f"![Random forest](../charts/{chart_name})",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    df = pd.read_csv(PROCESSED)
    df["arrival_date"] = pd.to_datetime(df["arrival_date"])
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

    summary, overall_importances, forests = {}, {}, {}
    for comm in COMMS:
        tr = train[train["commodity"] == comm].copy()
        te = test[test["commodity"] == comm].copy()
        beta = fit_ols(tr)
        te["fc_lr"] = apply_ols(te, beta)
        rf = fit_forest(tr)
        forests[comm] = rf
        te["fc_rf"] = rf.predict(te[FEATURES].to_numpy(dtype=float))
        test.loc[te.index, ["fc_lr", "fc_rf"]] = te[["fc_lr", "fc_rf"]]
        y = te["modal_price"].to_numpy(dtype=float)
        summary[comm] = {m: metrics(y, te[m].to_numpy(dtype=float))
                         for m in METHODS}
        overall_importances[comm] = dict(
            zip(FEATURES, [float(v) for v in rf.feature_importances_]))

    overall = {}
    y_all = test["modal_price"].to_numpy(dtype=float)
    for m in METHODS:
        overall[m] = metrics(y_all, test[m].to_numpy(dtype=float))

    cols = ["market", "commodity", "arrival_date", "modal_price"] + FEATURES \
        + METHODS
    out = test[cols].copy()
    out["arrival_date"] = out["arrival_date"].dt.strftime("%Y-%m-%d")
    out.to_csv(OUT, index=False)

    verify_res = verify(train, test, forests, summary)

    chart_name = f"random_forest_{TODAY}.svg"
    make_chart(summary, overall_importances, os.path.join(CHARTS_DIR,
                                                          chart_name))
    split = (str(dates[0]),
             str(dates[-n_test_dates - 1]) if len(dates) > n_test_dates
             else str(dates[0]),
             str(test_dates[0]), str(test_dates[-1]),
             len(train), len(test), n_test_dates, len(dates))
    write_report(split, summary, overall, overall_importances, verify_res,
                 chart_name,
                 os.path.join(REPORTS_DIR, "day19_random_forest.md"))

    print(f"Split: train {split[0]}..{split[1]} ({split[4]} rows), "
          f"test {split[2]}..{split[3]} ({split[5]} rows scored)")
    for comm in COMMS:
        print(f"{comm}: " + ", ".join(
            f"{LABELS[m]} MAE {summary[comm][m]['mae']:.2f}"
            for m in METHODS) + f" (n={summary[comm]['fc_rf']['n']})")
    winner = min(METHODS, key=lambda m: overall[m]["mae"])
    print(f"Overall test winner: {LABELS[winner]} "
          f"(MAE {overall[winner]['mae']:.2f})")
    print("Verification: re-fit determinism + importance sums + manual "
          "tree-walk hand-check all PASSED")


if __name__ == "__main__":
    main()
