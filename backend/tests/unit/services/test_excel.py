"""
tests/unit/services/test_excel.py

pandas フィルタリングロジック (src.services.excel) の単体テスト。
pd.read_excel をモック化し、実ファイルに依存しない。
"""

from datetime import datetime

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from src.services.excel import filter_relevant_rows

# テスト用に使う固定データフレーム
_MOCK_DF = pd.DataFrame(
    {
        "id": [1, 2, 3, 4, 5, 6],
        "category": [
            "経費精算", "経費精算", "勤怠管理",
            "IT・セキュリティ", "福利厚生", "社内制度・規則",
        ],
        "subcategory": [
            "申請手続き", "上限・ルール", "有給休暇",
            "パスワード管理", "健康・医療", "副業・兼業",
        ],
        "title": [
            "経費精算の申請方法を教えてください",
            "交際費の上限はいくらですか？",
            "有給休暇の取得方法と残日数の確認方法",
            "社内システムのパスワードポリシー",
            "健康診断の受診方法とオプション検査",
            "副業・兼業の申請方法と禁止事項",
        ],
        "content": [
            "経費精算は毎月25日までに社内ポータルから申請してください。領収書は原本をスキャンしてください。",
            "社外との会食は1人あたり10,000円が上限です。アルコール費用は認められません。",
            "有給休暇は勤怠システムから申請してください。3営業日前までに申請が必要です。",
            "パスワードは12文字以上で英大文字・英小文字・数字・記号を含めてください。",
            "年1回の定期健康診断は会社負担で受診できます。35歳以上は人間ドックの補助があります。",
            "副業は事前に人事部に申請し承認を得た場合のみ認められます。競合他社への就業は禁止です。",
        ],
        "keywords": [
            "経費,精算,申請,領収書,交通費,承認",
            "交際費,上限,接待,会食,アルコール",
            "有給,休暇,取得,残日数,半日,申請",
            "パスワード,セキュリティ,ポリシー,変更",
            "健康診断,人間ドック,補助,受診,産業医",
            "副業,兼業,申請,承認,競合,禁止",
        ],
        "department": ["総務部", "総務部", "人事部", "IT部", "総務部", "人事部"],
        "applicable_to": [
            "全社員", "全社員", "全社員", "全社員", "正社員", "正社員",
        ],
        "last_updated": [datetime(2024, 10, 1)] * 6,
        "author": [
            "総務部 山田", "総務部 山田", "人事部 鈴木",
            "IT部 高橋", "総務部 中村", "人事部 田中",
        ],
    }
)


@pytest.fixture(autouse=True)
def mock_read_excel(mocker: MockerFixture) -> None:
    """全テストで pd.read_excel をモック化する。"""
    mocker.patch("src.services.excel.pd.read_excel", return_value=_MOCK_DF.copy())


class TestFilterRelevantRows:
    # ── キーワードマッチ ──────────────────────────────────────────────

    def test_returns_csv_string(self) -> None:
        """戻り値が CSV 文字列であること。"""
        result = filter_relevant_rows("経費精算")
        assert isinstance(result, str)
        # CSV のヘッダー行が含まれる
        assert "category" in result
        assert "title" in result
        assert "content" in result

    def test_keyword_match_returns_relevant_rows(self) -> None:
        """クエリに含まれるキーワードに関連する行が抽出されること。"""
        result = filter_relevant_rows("経費精算")
        assert "経費精算" in result

    def test_keyword_match_excludes_irrelevant_rows(self) -> None:
        """クエリに無関係な行はプライマリ結果に含まれないこと。"""
        result = filter_relevant_rows("経費精算")
        # パスワードポリシーは経費と無関係
        assert "パスワードポリシー" not in result

    def test_multiple_keywords_boost_score(self) -> None:
        """複数のキーワードを含む行が上位に返ること。"""
        # "有給 休暇" → 有給休暇の行がマッチするはず
        result = filter_relevant_rows("有給 休暇")
        assert "有給休暇" in result

    def test_content_match(self) -> None:
        """title だけでなく content の文字列にもマッチすること。"""
        # "領収書" は content に含まれる
        result = filter_relevant_rows("領収書")
        assert "経費精算の申請方法" in result

    @pytest.mark.parametrize(
        "query, expected_title",
        [
            ("パスワード", "社内システムのパスワードポリシー"),
            ("健康診断", "健康診断の受診方法とオプション検査"),
            ("副業", "副業・兼業の申請方法と禁止事項"),
        ],
        ids=["password", "health-check", "side-job"],
    )
    def test_various_queries_return_matched_rows(
        self, query: str, expected_title: str
    ) -> None:
        """各カテゴリのクエリに対して対応する行が返ること。"""
        result = filter_relevant_rows(query)
        assert expected_title in result

    # ── フォールバック ────────────────────────────────────────────────

    def test_no_match_returns_fallback(self) -> None:
        """一致する行がない場合は先頭 _MAX_ROWS 行をフォールバックで返すこと。"""
        result = filter_relevant_rows("xyzzy_全くマッチしない文字列_12345")
        # フォールバックなので何らかの行は含まれる
        assert "category" in result
        lines = result.strip().split("\n")
        # ヘッダー + 最大5行 = 最大6行
        assert len(lines) <= 6

    def test_empty_query_returns_fallback(self) -> None:
        """空クエリは先頭 _MAX_ROWS 行のフォールバックを返すこと。"""
        result = filter_relevant_rows("")
        lines = result.strip().split("\n")
        assert len(lines) <= 6

    def test_single_char_query_returns_fallback(self) -> None:
        """1文字クエリは単語として認識されず、フォールバックが返ること。"""
        result = filter_relevant_rows("あ")
        lines = result.strip().split("\n")
        # 2文字未満はスキップするため全データがフォールバックになる
        assert len(lines) <= 6

    # ── 件数の上限 ────────────────────────────────────────────────────

    def test_max_rows_limit(self) -> None:
        """返却行数が _MAX_ROWS (5) + ヘッダー1行 = 6行以下であること。"""
        # 全行にマッチするような広いクエリ
        result = filter_relevant_rows("申請")
        lines = result.strip().split("\n")
        assert len(lines) <= 6

    # ── 出力カラム ────────────────────────────────────────────────────

    def test_output_contains_only_context_columns(self) -> None:
        """出力 CSV に含まれるカラムが指定列のみであること。"""
        result = filter_relevant_rows("経費")
        header = result.split("\n")[0]
        assert "category" in header
        assert "subcategory" in header
        assert "title" in header
        assert "content" in header
        assert "keywords" in header
        # id や author はプロンプトに不要なため含めない
        assert "id" not in header
        assert "author" not in header
        assert "department" not in header
