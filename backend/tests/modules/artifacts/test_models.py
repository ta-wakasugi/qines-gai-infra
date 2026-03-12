"""
Artifacts module models unit tests

スライドクラスのビジネスロジックをテストする
Pptxライブラリのみをモックし、スライド作成ロジックが正しく動作することを確認する
"""

from unittest.mock import MagicMock


from qines_gai_backend.modules.artifacts.models import (
    TablePage,
    TableSection,
    TableSlide,
    TextPage,
    TextSection,
    TextSlide,
    TitleSlide,
)


class TestTitleSlide:
    """TitleSlideクラスのテストクラス"""

    def test_title_slide_create_slide(self):
        """タイトルスライドが作成されることを確認する"""
        # Arrange
        mock_presentation = MagicMock()
        mock_slide_layout = MagicMock()
        mock_slide = MagicMock()
        mock_placeholder = MagicMock()

        mock_presentation.slide_layouts = [mock_slide_layout]
        mock_presentation.slides.add_slide.return_value = mock_slide
        mock_slide.placeholders = {0: mock_placeholder}

        title_slide = TitleSlide(mock_presentation, "Test Title")

        # Act
        title_slide.create_slide()

        # Assert
        mock_presentation.slides.add_slide.assert_called_once_with(mock_slide_layout)
        assert mock_placeholder.text == "Test Title"


class TestTextSlide:
    """TextSlideクラスのテストクラス"""

    def test_text_slide_create_slide(self):
        """テキストスライドが作成されることを確認する"""
        # Arrange
        mock_presentation = MagicMock()
        mock_slide_layout = MagicMock()
        mock_slide = MagicMock()
        mock_title_placeholder = MagicMock()
        mock_content_placeholder = MagicMock()
        mock_text_frame = MagicMock()

        mock_presentation.slide_layouts = [None, mock_slide_layout]
        mock_presentation.slides.add_slide.return_value = mock_slide
        mock_slide.placeholders = {
            0: mock_title_placeholder,
            1: mock_content_placeholder,
        }
        mock_content_placeholder.text_frame = mock_text_frame

        page_data = TextPage(
            header="Test Header",
            content="Content",
            template="text",
            policy="Policy",
            sections=[TextSection(title="Section 1", content=["Point 1", "Point 2"])],
        )
        text_slide = TextSlide(mock_presentation, page_data)

        # Act
        text_slide.create_slide()

        # Assert
        mock_presentation.slides.add_slide.assert_called_once_with(mock_slide_layout)
        assert mock_title_placeholder.text == "Test Header"
        mock_text_frame.clear.assert_called_once()


class TestTableSlide:
    """TableSlideクラスのテストクラス"""

    def test_table_slide_create_slide(self):
        """表スライドが作成されることを確認する"""
        # Arrange
        mock_presentation = MagicMock()
        mock_slide_layout = MagicMock()
        mock_slide = MagicMock()
        mock_title_placeholder = MagicMock()
        mock_content_placeholder = MagicMock()
        mock_shapes = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_presentation.slide_layouts = [None, mock_slide_layout]
        mock_presentation.slides.add_slide.return_value = mock_slide
        mock_slide.placeholders = {
            0: mock_title_placeholder,
            1: mock_content_placeholder,
        }
        mock_slide.shapes = mock_shapes
        mock_shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        # テーブルのセルをモック
        mock_cell = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()

        mock_table.cell.return_value = mock_cell
        mock_cell.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run]

        page_data = TablePage(
            header="Table Header",
            content="Content",
            template="table",
            policy="Policy",
            table_section=TableSection(
                title="Test Table", table_data=[["A", "B"], ["C", "D"]]
            ),
        )
        table_slide = TableSlide(mock_presentation, page_data)

        # Act
        table_slide.create_slide()

        # Assert
        mock_presentation.slides.add_slide.assert_called_once_with(mock_slide_layout)
        assert mock_title_placeholder.text == "Table Header"
        mock_shapes.add_table.assert_called_once()
