from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from jarvis.memory.repository import MemoryRepository


class MemoryPanel(QWidget):
    """Interactive management panel for user notes, memory records, and audit logs."""

    note_changed = Signal()

    def __init__(self, memory_repo: MemoryRepository, parent=None):
        super().__init__(parent)
        self.memory = memory_repo
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("MEMORY & SYSTEM ARCHIVE")
        title.setStyleSheet("color: #4deaff; font-size: 13px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #17475a; background: #07121e; border-radius: 6px; }
            QTabBar::tab { background: #0b1e2e; color: #8ec3d6; padding: 6px 14px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-size: 11px; }
            QTabBar::tab:selected { background: #093c4f; color: #4deaff; font-weight: bold; }
            """
        )

        # Tab 1: Notes Management
        notes_widget = QWidget()
        notes_layout = QVBoxLayout(notes_widget)
        notes_layout.setContentsMargins(8, 8, 8, 8)
        notes_layout.setSpacing(8)

        # Search bar
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search saved notes...")
        self.search_input.textChanged.connect(self._filter_notes)
        search_row.addWidget(self.search_input)
        notes_layout.addLayout(search_row)

        # List of notes
        self.notes_list = QListWidget()
        self.notes_list.setStyleSheet(
            """
            QListWidget { background: #050d17; border: 1px solid #14394b; border-radius: 6px; color: #d8f7ff; font-size: 12px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #0f2736; }
            QListWidget::item:selected { background: #0d3b4c; color: #ffffff; }
            """
        )
        notes_layout.addWidget(self.notes_list, 1)

        # Action buttons
        btns_row = QHBoxLayout()
        del_btn = QPushButton("DELETE SELECTED")
        del_btn.setStyleSheet("background: #38202a; border: 1px solid #824050; color: #ffc8d1; padding: 6px 12px; border-radius: 5px;")
        del_btn.clicked.connect(self._delete_selected_note)

        clear_btn = QPushButton("CLEAR ALL")
        clear_btn.setStyleSheet("background: #471a23; border: 1px solid #993248; color: #ff94a5; padding: 6px 12px; border-radius: 5px;")
        clear_btn.clicked.connect(self._clear_all_notes)

        refresh_btn = QPushButton("REFRESH")
        refresh_btn.setStyleSheet("background: #0d3447; border: 1px solid #24788b; color: #a9f6ff; padding: 6px 12px; border-radius: 5px;")
        refresh_btn.clicked.connect(self.refresh)

        btns_row.addWidget(del_btn)
        btns_row.addWidget(clear_btn)
        btns_row.addStretch()
        btns_row.addWidget(refresh_btn)
        notes_layout.addLayout(btns_row)

        tabs.addTab(notes_widget, "NOTES")

        # Tab 2: Audit Logs
        audit_widget = QWidget()
        audit_layout = QVBoxLayout(audit_widget)
        audit_layout.setContentsMargins(8, 8, 8, 8)

        self.audit_table = QTableWidget(0, 4)
        self.audit_table.setHorizontalHeaderLabels(["Time", "Action", "Status", "Details"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.audit_table.setStyleSheet(
            """
            QTableWidget { background: #050d17; border: 1px solid #14394b; color: #d8f7ff; font-size: 11px; }
            QHeaderView::section { background: #0b1e2e; color: #4deaff; padding: 4px; border: 1px solid #17475a; }
            """
        )
        audit_layout.addWidget(self.audit_table)
        tabs.addTab(audit_widget, "AUDIT LOG")

        layout.addWidget(tabs, 1)

    def refresh(self):
        """Reloads notes and audit logs from database."""
        self.notes_list.clear()
        notes = self.memory.get_notes(limit=50)
        for n in notes:
            item = QListWidgetItem(f"#{n['id']} [{n['created_at']}] — {n['note']}")
            item.setData(Qt.UserRole, n['id'])
            self.notes_list.addItem(item)

        # Refresh audit logs
        logs = self.memory.get_recent_audit_logs(limit=25)
        self.audit_table.setRowCount(len(logs))
        for row, entry in enumerate(logs):
            self.audit_table.setItem(row, 0, QTableWidgetItem(str(entry.get("created_at", ""))))
            self.audit_table.setItem(row, 1, QTableWidgetItem(str(entry.get("action_type", ""))))
            self.audit_table.setItem(row, 2, QTableWidgetItem(str(entry.get("status", ""))))
            self.audit_table.setItem(row, 3, QTableWidgetItem(str(entry.get("details", ""))))

    def _filter_notes(self, query: str):
        if not query.strip():
            self.refresh()
            return
        self.notes_list.clear()
        results = self.memory.search_notes(query.strip())
        for n in results:
            item = QListWidgetItem(f"#{n['id']} [{n['created_at']}] — {n['note']}")
            item.setData(Qt.UserRole, n['id'])
            self.notes_list.addItem(item)

    def _delete_selected_note(self):
        current_item = self.notes_list.currentItem()
        if not current_item:
            return
        note_id = current_item.data(Qt.UserRole)
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete Note #{note_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.memory.delete_note(note_id)
            self.refresh()
            self.note_changed.emit()

    def _clear_all_notes(self):
        confirm = QMessageBox.warning(
            self,
            "Purge All Notes",
            "This will permanently erase all saved notes in local storage. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.memory.clear_all_notes()
            self.refresh()
            self.note_changed.emit()
