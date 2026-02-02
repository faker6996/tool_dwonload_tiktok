from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QAbstractItemView, QComboBox, QListView


class BoundedComboBox(QComboBox):
    def __init__(self, *args, max_popup_height: int = 280, max_visible_items: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_popup_height = int(max_popup_height)
        self.setMaxVisibleItems(int(max_visible_items))
        self._init_popup_view()

    def _init_popup_view(self) -> None:
        view = QListView()
        view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setStyleSheet(
            """
            QListView {
                background-color: #18181b;
                color: #e5e5e5;
                border: 1px solid #27272a;
                outline: 0;
            }
            QListView::item {
                padding: 6px 10px;
                height: 28px;
                color: #e5e5e5;
                background-color: transparent;
            }
            QListView::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            QListView::item:selected {
                background-color: #4f46e5;
                color: #ffffff;
            }
            """
        )
        self.setView(view)

    def _apply_popup_constraints(self) -> None:
        view = self.view()
        view.setMaximumHeight(self._max_popup_height)
        container = view.window()
        if container is not None:
            container.setMaximumHeight(self._max_popup_height)

    def showPopup(self) -> None:
        self._apply_popup_constraints()
        super().showPopup()
        QTimer.singleShot(0, self._apply_popup_constraints)
