#!/usr/bin/env python3
"""生成した透過PNGを LINE Creators Market の規定サイズに書き出す。

- メイン画像   : 240x240
- 一覧用画像   : 96x74
- 各スタンプ   : 370x320以内（透過を維持したままレターボックスで収める）

使い方:
  python3 resize_for_line.py [main_source_id]

  main_source_id を省略した場合は output/raw 内の最初のファイルを
  メイン画像・一覧画像の元にする。
"""

import sys
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "output" / "raw"
OUT_DIR = BASE_DIR / "output" / "line_submission"

MAIN_SIZE = (240, 240)
TAB_SIZE = (96, 74)
STICKER_MAX = (370, 320)


def fit_transparent(img: Image.Image, box: tuple[int, int]) -> Image.Image:
    """アスペクト比を保ったまま box に収め、余白は透過で埋める。"""
    img = img.convert("RGBA")
    fitted = img.copy()
    fitted.thumbnail(box, Image.LANCZOS)
    canvas = Image.new("RGBA", box, (0, 0, 0, 0))
    x = (box[0] - fitted.width) // 2
    y = (box[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y), fitted)
    return canvas


def main() -> None:
    if not RAW_DIR.exists():
        print(f"{RAW_DIR} が見つかりません。先に generate_stickers.py を実行してください。", file=sys.stderr)
        sys.exit(1)

    sources = sorted(RAW_DIR.glob("*.png"))
    if not sources:
        print(f"{RAW_DIR} にPNGがありません。", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 各スタンプ本体を書き出し
    for src in sources:
        img = Image.open(src)
        sticker = fit_transparent(img, STICKER_MAX)
        sticker.save(OUT_DIR / src.name, optimize=True)
        print(f"スタンプ書き出し: {src.name} -> {STICKER_MAX[0]}x{STICKER_MAX[1]}以内")

    # メイン画像・一覧画像は指定 or 先頭のスタンプから作成
    main_id = sys.argv[1] if len(sys.argv) > 1 else sources[0].stem
    main_src = RAW_DIR / f"{main_id}.png"
    if not main_src.exists():
        print(f"指定された {main_src} が見つかりません。", file=sys.stderr)
        sys.exit(1)

    base_img = Image.open(main_src)
    fit_transparent(base_img, MAIN_SIZE).save(OUT_DIR / "main.png", optimize=True)
    fit_transparent(base_img, TAB_SIZE).save(OUT_DIR / "tab.png", optimize=True)

    print(f"メイン画像・一覧画像を作成しました（元: {main_id}）")
    print(f"完了。出力先: {OUT_DIR}")


if __name__ == "__main__":
    main()
