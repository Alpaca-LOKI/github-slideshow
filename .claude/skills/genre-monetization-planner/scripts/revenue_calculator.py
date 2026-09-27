#!/usr/bin/env python3
"""売上 = リスト数 × リプ率 × 購入率 × 客単価 の計算・逆算・ボトルネック診断ツール。

3モード:
  forecast : 4つの値から売上を予測する
  solve    : 目標売上と3つの値から、残り1つの必要値を逆算する
  diagnose : 実測のファネル数値を並べて、目標に対してどこが一番のボトルネックかを提示する
"""

import argparse
import sys

VARS = ["list_size", "reply_rate", "purchase_rate", "unit_price"]
LABELS = {
    "list_size": "リスト数（フォロワー/LINE登録者など）",
    "reply_rate": "リプ率（0〜1）",
    "purchase_rate": "購入率（0〜1）",
    "unit_price": "客単価（円）",
}


def revenue(list_size, reply_rate, purchase_rate, unit_price):
    return list_size * reply_rate * purchase_rate * unit_price


def cmd_forecast(args):
    rev = revenue(args.list_size, args.reply_rate, args.purchase_rate, args.unit_price)
    replies = args.list_size * args.reply_rate
    purchases = replies * args.purchase_rate
    print("=== 売上予測 ===")
    print(f"リスト数     : {args.list_size:,.0f}")
    print(f"  × リプ率   : {args.reply_rate:.1%}  → リプ数 {replies:,.1f}")
    print(f"  × 購入率   : {args.purchase_rate:.1%}  → 購入件数 {purchases:,.1f}")
    print(f"  × 客単価   : ¥{args.unit_price:,.0f}")
    print(f"---------------------------------")
    print(f"予測売上     : ¥{rev:,.0f}")


def cmd_solve(args):
    given = {k: getattr(args, k) for k in VARS if getattr(args, k) is not None}
    missing = [k for k in VARS if getattr(args, k) is None]

    if len(missing) != 1:
        print(
            f"エラー: --target-revenue に加えて、{', '.join(VARS)} のうちちょうど3つを指定してください"
            f"（未指定: {', '.join(missing) if missing else 'なし'}）",
            file=sys.stderr,
        )
        sys.exit(1)

    target = args.target_revenue
    denom = 1.0
    for k in given:
        denom *= given[k]

    if denom == 0:
        print("エラー: 指定した値に0が含まれているため計算できません", file=sys.stderr)
        sys.exit(1)

    solved_key = missing[0]
    solved_value = target / denom

    print("=== 目標売上からの逆算 ===")
    print(f"目標売上     : ¥{target:,.0f}")
    for k in VARS:
        if k == solved_key:
            if k == "unit_price":
                print(f"必要な{LABELS[k]:<28}: ¥{solved_value:,.0f} ← 求める値")
            elif k in ("reply_rate", "purchase_rate"):
                print(f"必要な{LABELS[k]:<28}: {solved_value:.1%} ← 求める値")
            else:
                print(f"必要な{LABELS[k]:<28}: {solved_value:,.1f} ← 求める値")
        else:
            v = given[k]
            if k in ("reply_rate", "purchase_rate"):
                print(f"固定値 {LABELS[k]:<28}: {v:.1%}")
            elif k == "unit_price":
                print(f"固定値 {LABELS[k]:<28}: ¥{v:,.0f}")
            else:
                print(f"固定値 {LABELS[k]:<28}: {v:,.0f}")

    if solved_key in ("reply_rate", "purchase_rate") and solved_value > 1:
        print(
            f"\n注意: 必要な{LABELS[solved_key]}が100%を超えています。"
            "この組み合わせでは目標達成が非現実的なので、他の変数（リスト数や客単価）を"
            "見直すことを検討してください。"
        )


def cmd_diagnose(args):
    replies = args.list_size * args.reply_rate
    purchases = replies * args.purchase_rate
    actual_revenue = purchases * args.unit_price
    gap = args.target_revenue - actual_revenue
    ratio = actual_revenue / args.target_revenue if args.target_revenue else 0

    print("=== 現状 vs 目標 ===")
    print(f"現状の売上   : ¥{actual_revenue:,.0f}（目標比 {ratio:.1%}）")
    print(f"目標売上     : ¥{args.target_revenue:,.0f}")
    print(f"差分         : ¥{gap:,.0f}")
    print()
    print("=== 各段階を単独で目標値まで引き上げた場合の必要な倍率 ===")
    needed_multiplier = args.target_revenue / actual_revenue if actual_revenue else float("inf")
    for k, label in LABELS.items():
        print(f"{label:<30}のみ変える場合 : 現状の {needed_multiplier:.2f}倍 が必要")
    print()
    print("判断の目安:")
    print("- リプ率・購入率はもともと低い（数%〜20%程度）ので、数倍にするのは非現実的なことが多い。")
    print("  わずかな改善（例: 20%→25%）でも売上への影響は大きい。")
    print("- リスト数を倍にするのは時間がかかるが、上限がない。")
    print("- 客単価は商品構成の見直し（松竹梅・アップセル）で比較的動かしやすい。")
    print("- 『投稿を増やす』は上記のどの数字にも直結しない場合がある。まずどの段階のテコが")
    print("  一番小さい改善で効果が出るかを、STEP3のポストモーテムと照らし合わせて特定すること。")


def main():
    parser = argparse.ArgumentParser(description="売上 = リスト数 × リプ率 × 購入率 × 客単価 の計算ツール")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_forecast = sub.add_parser("forecast", help="4つの値から売上を予測する")
    p_forecast.add_argument("--list-size", type=float, required=True, dest="list_size")
    p_forecast.add_argument("--reply-rate", type=float, required=True, dest="reply_rate")
    p_forecast.add_argument("--purchase-rate", type=float, required=True, dest="purchase_rate")
    p_forecast.add_argument("--unit-price", type=float, required=True, dest="unit_price")
    p_forecast.set_defaults(func=cmd_forecast)

    p_solve = sub.add_parser("solve", help="目標売上と3つの値から残り1つを逆算する")
    p_solve.add_argument("--target-revenue", type=float, required=True, dest="target_revenue")
    p_solve.add_argument("--list-size", type=float, dest="list_size")
    p_solve.add_argument("--reply-rate", type=float, dest="reply_rate")
    p_solve.add_argument("--purchase-rate", type=float, dest="purchase_rate")
    p_solve.add_argument("--unit-price", type=float, dest="unit_price")
    p_solve.set_defaults(func=cmd_solve)

    p_diag = sub.add_parser("diagnose", help="現状の実測値と目標売上から、どこがボトルネックかを診断する")
    p_diag.add_argument("--list-size", type=float, required=True, dest="list_size")
    p_diag.add_argument("--reply-rate", type=float, required=True, dest="reply_rate")
    p_diag.add_argument("--purchase-rate", type=float, required=True, dest="purchase_rate")
    p_diag.add_argument("--unit-price", type=float, required=True, dest="unit_price")
    p_diag.add_argument("--target-revenue", type=float, required=True, dest="target_revenue")
    p_diag.set_defaults(func=cmd_diagnose)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
