"""
社内ナレッジベース Excel の読み込みとキーワードフィルタリング。
ベクトルDBは使用せず、pandas の文字列検索のみで実装する。
"""

import os

import pandas as pd

from src.settings import BASE_DIR

_EXCEL_PATH = os.path.join(BASE_DIR, "data", "sample.xlsx")
_CONTEXT_COLUMNS = ["category", "subcategory", "title", "content", "keywords"]
_MAX_ROWS = 5  # プロンプトに埋め込む最大行数


def _load_excel() -> pd.DataFrame:
    return pd.read_excel(_EXCEL_PATH, engine="openpyxl")


def _score_row(row: pd.Series, words: list[str]) -> int:
    """行のスコア: 検索ワードが title / content / keywords に含まれる数を返す。"""
    target = f"{row['title']} {row['content']} {row['keywords']}".lower()
    return sum(1 for w in words if w in target)


def filter_relevant_rows(query: str) -> str:
    """
    ユーザーの質問に関連する行を pandas でフィルタリングし CSV 文字列で返す。
    マッチする行がなければ先頭 _MAX_ROWS 行をフォールバックとして返す。
    """
    df = _load_excel()

    # 2文字以上の単語のみ対象（助詞などを除外）
    words = [w for w in query.lower().split() if len(w) >= 2]

    if not words:
        return df[_CONTEXT_COLUMNS].head(_MAX_ROWS).to_csv(index=False)

    df = df.copy()
    df["_score"] = df.apply(lambda row: _score_row(row, words), axis=1)
    relevant = df[df["_score"] > 0].sort_values("_score", ascending=False)

    context_df = (relevant if not relevant.empty else df).head(_MAX_ROWS)
    return context_df[_CONTEXT_COLUMNS].to_csv(index=False)
