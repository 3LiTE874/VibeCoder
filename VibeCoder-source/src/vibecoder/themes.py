"""Dark theme palette for QScintilla editors and lexers."""

from __future__ import annotations

from PyQt6.Qsci import QsciLexer, QsciScintilla
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication, QWidget

# Core editor chrome
BG = QColor("#1e1e1e")
FG = QColor("#d4d4d4")
SELECTION_BG = QColor("#264f78")
CARET = QColor("#aeafad")
MARGIN_BG = QColor("#252526")
LINE_NUMBER_FG = QColor("#858585")
CURRENT_LINE_BG = QColor("#2a2d2e")
FOLD_MARGIN_FG = QColor("#6a9955")

# Syntax token colors (VS Code Dark+ inspired)
COLORS = {
    "default": FG,
    "keyword": QColor("#569cd6"),
    "class": QColor("#4ec9b0"),
    "function": QColor("#dcdcaa"),
    "string": QColor("#ce9178"),
    "comment": QColor("#6a9955"),
    "number": QColor("#b5cea8"),
    "operator": QColor("#d4d4d4"),
    "preprocessor": QColor("#c586c0"),
    "regex": QColor("#d16969"),
    "tag": QColor("#569cd6"),
    "attribute": QColor("#9cdcfe"),
    "heading": QColor("#569cd6"),
    "bold": QColor("#dcdcaa"),
    "italic": QColor("#c586c0"),
    "link": QColor("#4ec9b0"),
    "marker": QColor("#d7ba7d"),
    "error": QColor("#f44747"),
}


def apply_dark_palette(lexer: QsciLexer | None) -> None:
    """Apply the full dark syntax palette to a lexer.

    Must be called after every setLexer() so Language → Python (etc.)
    never renders as unstyled plain text.
    """
    if lexer is None:
        return

    lexer.setDefaultPaper(BG)
    lexer.setDefaultColor(FG)
    lexer.setColor(FG, 0)
    lexer.setPaper(BG, 0)

    style_map = {
        "keyword": _styles_for(lexer, "keyword"),
        "class": _styles_for(lexer, "class"),
        "function": _styles_for(lexer, "function"),
        "string": _styles_for(lexer, "string"),
        "comment": _styles_for(lexer, "comment"),
        "number": _styles_for(lexer, "number"),
        "operator": _styles_for(lexer, "operator"),
        "preprocessor": _styles_for(lexer, "preprocessor"),
        "regex": _styles_for(lexer, "regex"),
        "tag": _styles_for(lexer, "tag"),
        "attribute": _styles_for(lexer, "attribute"),
        "heading": _styles_for(lexer, "heading"),
        "bold": _styles_for(lexer, "bold"),
        "italic": _styles_for(lexer, "italic"),
        "link": _styles_for(lexer, "link"),
        "marker": _styles_for(lexer, "marker"),
        "error": _styles_for(lexer, "error"),
    }

    for color_key, style_ids in style_map.items():
        color = COLORS[color_key]
        for style_id in style_ids:
            lexer.setColor(color, style_id)
            lexer.setPaper(BG, style_id)

    font = QFont("Consolas", 11)
    if not font.exactMatch():
        font = QFont("Courier New", 11)
    font.setFixedPitch(True)
    lexer.setDefaultFont(font)


def _styles_for(lexer: QsciLexer, category: str) -> list[int]:
    """Map generic color categories to lexer-specific style IDs."""
    lexer_name = lexer.__class__.__name__

    common = {
        "keyword": [1, 2, 3, 4, 5],
        "string": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        "comment": [1, 2, 3, 4],
        "number": [4, 5, 6],
        "operator": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        "preprocessor": [9, 10, 11],
        "class": [8, 9, 10],
        "function": [5, 6, 7, 8, 9],
        "regex": [14, 15, 16],
        "tag": [1, 2, 3, 4, 5],
        "attribute": [6, 7, 8, 9, 10],
        "heading": [2, 3, 4, 5, 6],
        "bold": [7, 8],
        "italic": [9, 10],
        "link": [11, 12, 13],
        "marker": [14, 15, 16],
        "error": [17, 18, 19],
    }

    specific: dict[str, dict[str, list[int]]] = {
        "QsciLexerPython": {
            "keyword": [5],
            "class": [8],
            "function": [9, 14],
            "string": [3, 4, 6, 7, 16, 17, 18, 19],
            "comment": [1, 12],
            "number": [2],
            "operator": [10],
            "preprocessor": [15],
        },
        "QsciLexerMarkdown": {
            "heading": [2, 3, 4, 5, 6],
            "bold": [7, 8],
            "italic": [9, 10],
            "link": [11, 12, 13],
            "comment": [14, 15],
            "marker": [1],
            "keyword": [16, 17, 18],
            "string": [19, 20, 21],
        },
        "QsciLexerCPP": {
            "keyword": [1, 2, 3],
            "comment": [1, 2, 3, 4],
            "string": [6, 7, 8, 12, 13, 14, 15],
            "number": [4, 5],
            "preprocessor": [9, 10, 11],
            "operator": [17, 18, 19, 20, 21, 22, 23, 24],
        },
        "QsciLexerJavaScript": {
            "keyword": [1, 2, 3, 4, 5],
            "comment": [1, 2, 3, 4],
            "string": [6, 7, 8, 12, 13, 14, 15],
            "number": [4, 5],
            "regex": [14, 15, 16],
        },
        "QsciLexerHTML": {
            "tag": [1, 2, 3, 4, 5, 6, 7],
            "attribute": [8, 9, 10, 11],
            "string": [12, 13, 14, 15, 16, 17, 18, 19],
            "comment": [23, 24, 25, 26, 27],
        },
        "QsciLexerCSS": {
            "keyword": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "string": [10, 11, 12, 13, 14],
            "comment": [9],
            "number": [4, 5, 6],
            "class": [7, 8],
        },
        "QsciLexerJSON": {
            "keyword": [1, 2, 3, 4],
            "string": [5, 6, 7],
            "number": [8, 9],
            "comment": [10, 11],
        },
        "QsciLexerYAML": {
            "keyword": [1, 2, 3, 4, 5],
            "string": [6, 7, 8, 9],
            "comment": [1, 2],
            "number": [10, 11],
        },
        "QsciLexerSQL": {
            "keyword": [1, 2, 3, 4, 5, 6, 7],
            "string": [6, 7, 8],
            "comment": [1, 2, 3, 4],
            "number": [4, 5],
            "operator": [10, 11, 12, 13],
        },
        "QsciLexerBash": {
            "keyword": [1, 2, 3, 4, 5],
            "string": [6, 7, 8, 9],
            "comment": [1, 2],
            "number": [4, 5],
            "operator": [10, 11, 12],
        },
        "QsciLexerXML": {
            "tag": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "attribute": [10, 11, 12, 13, 14, 15],
            "string": [16, 17, 18, 19, 20],
            "comment": [21, 22, 23],
        },
        "KeywordLexer": {
            "keyword": [1],
            "class": [],
            "function": [],
            "string": [2],
            "comment": [3],
            "number": [4],
            "operator": [5],
            "preprocessor": [],
            "regex": [],
            "tag": [],
            "attribute": [],
            "heading": [],
            "bold": [],
            "italic": [],
            "link": [],
            "marker": [],
            "error": [],
        },
    }

    mapping = specific.get(lexer_name, common)
    return mapping.get(category, common.get(category, []))


def style_editor(editor: QsciScintilla) -> None:
    """Apply dark chrome to the QScintilla widget itself."""
    editor.setPaper(BG)
    editor.setColor(FG)

    editor.setMarginsBackgroundColor(MARGIN_BG)
    editor.setMarginsForegroundColor(LINE_NUMBER_FG)
    editor.setCaretForegroundColor(CARET)
    editor.setSelectionBackgroundColor(SELECTION_BG)
    editor.setCaretLineBackgroundColor(CURRENT_LINE_BG)

    font = QFont("Consolas", 11)
    if not font.exactMatch():
        font = QFont("Courier New", 11)
    font.setFixedPitch(True)
    editor.setFont(font)

    editor.setIndentationGuides(True)
    editor.setTabWidth(4)
    editor.setIndentationsUseTabs(False)
    editor.setAutoIndent(True)
    editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
    editor.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)


def apply_app_dark_theme(app: QApplication) -> None:
    """Dark palette for menus, dialogs, and dock widgets."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, BG)
    palette.setColor(QPalette.ColorRole.WindowText, FG)
    palette.setColor(QPalette.ColorRole.Base, QColor("#252526"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2d2d30"))
    palette.setColor(QPalette.ColorRole.Text, FG)
    palette.setColor(QPalette.ColorRole.Button, QColor("#2d2d30"))
    palette.setColor(QPalette.ColorRole.ButtonText, FG)
    palette.setColor(QPalette.ColorRole.Highlight, SELECTION_BG)
    palette.setColor(QPalette.ColorRole.HighlightedText, FG)
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2d2d30"))
    palette.setColor(QPalette.ColorRole.ToolTipText, FG)
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QMainWindow, QWidget { background-color: #1e1e1e; color: #d4d4d4; }
        QMenuBar { background-color: #2d2d30; color: #d4d4d4; }
        QMenuBar::item:selected { background-color: #094771; }
        QMenu { background-color: #252526; color: #d4d4d4; border: 1px solid #3c3c3c; }
        QMenu::item:selected { background-color: #094771; }
        QTabWidget::pane { border: 1px solid #3c3c3c; }
        QTabBar::tab {
            background-color: #2d2d30; color: #969696; padding: 6px 12px;
            border: 1px solid #3c3c3c; border-bottom: none;
        }
        QTabBar::tab:selected { background-color: #1e1e1e; color: #ffffff; }
        QTabBar::tab:hover { background-color: #323233; }
        QDockWidget::title { background-color: #2d2d30; padding: 4px; }
        QTreeView { background-color: #252526; color: #d4d4d4; border: none; }
        QTreeView::item:selected { background-color: #094771; }
        QComboBox { background-color: #2d2d30; color: #d4d4d4; border: 1px solid #3c3c3c; padding: 4px; }
        QComboBox QAbstractItemView { background-color: #252526; color: #d4d4d4; selection-background-color: #094771; }
        QStatusBar { background-color: #007acc; color: #ffffff; }
        QToolBar { background-color: #2d2d30; border: none; }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #252526; color: #d4d4d4; border: 1px solid #3c3c3c;
        }
        QPushButton {
            background-color: #0e639c; color: #ffffff; border: none; padding: 6px 14px;
        }
        QPushButton:hover { background-color: #1177bb; }
        QPushButton:pressed { background-color: #094771; }
        QWidget#topChrome { background-color: #4a4a4a; }
        QLabel#brandTitle {
            background-color: #4a4a4a;
            color: #39ff14;
            font-family: "Segoe UI";
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: 8px 12px;
        }
        """
    )


def style_widget(widget: QWidget) -> None:
    """Ensure child widgets inherit dark styling."""
    widget.setAutoFillBackground(True)
