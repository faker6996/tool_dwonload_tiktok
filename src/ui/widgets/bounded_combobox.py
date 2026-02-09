from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QAbstractItemView, QComboBox, QListView, QStyledItemDelegate


class _PopupItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, min_height: int = 30):
        super().__init__(parent)
        self._min_height = int(min_height)

    def sizeHint(self, option, index):
        hint = super().sizeHint(option, index)
        if hint.height() < self._min_height:
            hint.setHeight(self._min_height)
        return hint


class BoundedComboBox(QComboBox):
    def __init__(self, *args, max_popup_height: int = 280, max_visible_items: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_popup_height = int(max_popup_height)
        self._item_min_height = 30
        self.setMaxVisibleItems(int(max_visible_items))
        self._init_popup_view()

    def _init_popup_view(self) -> None:
        view = QListView(self)
        view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        view.setUniformItemSizes(True)
        view.setSpacing(2)
        view.setWordWrap(False)
        view.setTextElideMode(Qt.TextElideMode.ElideRight)
        view.setItemDelegate(_PopupItemDelegate(view, min_height=self._item_min_height))
        self.setView(view)

    def _apply_popup_constraints(self) -> None:
        view = self.view()
        view.setMaximumHeight(self._max_popup_height)
        model = self.model()
        max_text_width = 0
        if model is not None:
            metrics = self.fontMetrics()
            column = self.modelColumn()
            for row in range(model.rowCount()):
                model_index = model.index(row, column)
                text = str(model_index.data(Qt.ItemDataRole.DisplayRole) or "")
                text_width = metrics.horizontalAdvance(text)
                if text_width > max_text_width:
                    max_text_width = text_width
        popup_width = max(self.width(), max_text_width + 52)
        container = view.window()
        if container is not None:
            container.setMaximumHeight(self._max_popup_height)
            container.setMinimumWidth(popup_width)

    def showPopup(self) -> None:
        self._apply_popup_constraints()
        super().showPopup()
        QTimer.singleShot(0, self._apply_popup_constraints)
