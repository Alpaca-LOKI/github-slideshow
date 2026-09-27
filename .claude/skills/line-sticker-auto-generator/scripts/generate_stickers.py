#!/usr/bin/env python3
"""LINEスタンプ用の画像をOpenAI gpt-image-1で一括生成する。

使い方:
  1. 下の PROMPTS リストに、SKILL.md の STEP3 フォーマットで作った
     プロンプトを {"id": "01_ohayou", "phrase": "おはよう〜！", "prompt": "..."} の形で追加する。
  2. 環境変数 OPENAI_API_KEY を設定する。
  3. python3 generate_stickers.py を実行する。

background="transparent" を渡すことで、gpt-image-1 が透過PNGを直接返す。
"""

import base64
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "raw"

# ここに STEP3 で作成したプロンプトを追加していく（例）
PROMPTS = [
    {
        "id": "01_sample",
        "phrase": "おはよう〜！",
        "prompt": (
            "デフォルメされた可愛い日本のキャラクター、黒髪ショート、私服はパーカー。\n\n"
            "シーン：元気に手を振って挨拶しているポーズ、笑顔\n"
            "セリフ：「おはよう〜！」を吹き出し文字としてキャラの近くに大きく読みやすく配置する\n"
            "スタイル：LINEスタンプ用のシンプルな塗り、太めの輪郭線、背景要素なし\n"
            "背景：透過（背景に何も描かない。キャラと文字だけを画面いっぱいに配置）"
        ),
    },
]


def generate_one(client: OpenAI, item: dict, retries: int = 3) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{item['id']}.png"

    for attempt in range(1, retries + 1):
        try:
            result = client.images.generate(
                model="gpt-image-1",
                prompt=item["prompt"],
                size="1024x1024",
                background="transparent",
                n=1,
            )
            image_b64 = result.data[0].b64_json
            out_path.write_bytes(base64.b64decode(image_b64))
            return out_path
        except Exception as exc:  # noqa: BLE001
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"  [{item['id']}] エラー: {exc} -> {wait}秒後に再試行", file=sys.stderr)
            time.sleep(wait)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("環境変数 OPENAI_API_KEY が設定されていません。", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print(f"{len(PROMPTS)}件のスタンプを生成します（保存先: {OUTPUT_DIR}）")
    for item in PROMPTS:
        print(f"生成中: {item['id']}（{item['phrase']}）")
        path = generate_one(client, item)
        print(f"  -> 完了: {path}")

    print("すべての生成が完了しました。目視で表情・文字の崩れをチェックしてください。")


if __name__ == "__main__":
    main()
