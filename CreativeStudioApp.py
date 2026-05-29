#!/usr/bin/env python3
"""
Creative Studio - Version 1.2
Self-updating project management system with themes, project switching, and integrated updates.
"""

import sys
import os
import json
import shutil
import re
import tempfile
import subprocess
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

from PySide6.QtCore import Qt, QTimer, Signal, QUrl, QSize, QSettings, QStandardPaths, QProcess
from PySide6.QtGui import (
    QAction, QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
    QPixmap, QIcon, QMovie, QDesktopServices
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QTextEdit,
    QLineEdit, QSplitter, QMenu, QInputDialog, QMessageBox,
    QFileDialog, QFormLayout, QSpinBox, QComboBox, QTextBrowser,
    QToolBar, QFrame, QDialog, QDialogButtonBox, QPlainTextEdit,
    QScrollArea, QGridLayout, QGroupBox, QCheckBox, QTabWidget,
    QStatusBar
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
APP_NAME = "Creative Studio"
VERSION = "1.0"
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/FossilBacon/creative-studio-updates/main/version.txt"  # Replace with actual URL
UPDATE_SCRIPT_URL = "https://raw.githubusercontent.com/FossilBacon/creative-studio-updates/main/creative_studio.py"  # URL to the latest script

# Supported media categories by extension
MEDIA_CATEGORIES = {
    '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
    '.bmp': 'image', '.webp': 'image', '.gif': 'gif',
    '.mp3': 'audio', '.wav': 'audio', '.ogg': 'audio',
    '.obj': 'model3d', '.gltf': 'model3d', '.glb': 'model3d',
}

FIELD_TYPES = {
    "line": "Single Line Text",
    "text": "Multi‑line Text",
    "combo": "Dropdown",
    "spin": "Number (Spin Box)",
}

# ----------------------------------------------------------------------
# Data Helpers
# ----------------------------------------------------------------------
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def default_data(project_name=""):
    return {
        "project_name": project_name,
        "sections": [],
        "pages": {}
    }

# ----------------------------------------------------------------------
# App Settings Manager
# ----------------------------------------------------------------------
@dataclass
class AppSettings:
    theme: str = "dark"
    font_size: int = 12
    open_last_project: bool = True
    auto_save_interval: int = 30  # seconds
    recent_projects: List[str] = field(default_factory=list)
    last_project_path: str = ""

    @classmethod
    def load(cls):
        settings = QSettings(APP_NAME, APP_NAME)
        return cls(
            theme=settings.value("theme", "dark"),
            font_size=int(settings.value("font_size", 12)),
            open_last_project=settings.value("open_last_project", True, type=bool),
            auto_save_interval=int(settings.value("auto_save_interval", 30)),
            recent_projects=settings.value("recent_projects", [], type=list),
            last_project_path=settings.value("last_project_path", "", type=str)
        )

    def save(self):
        settings = QSettings(APP_NAME, APP_NAME)
        settings.setValue("theme", self.theme)
        settings.setValue("font_size", self.font_size)
        settings.setValue("open_last_project", self.open_last_project)
        settings.setValue("auto_save_interval", self.auto_save_interval)
        settings.setValue("recent_projects", self.recent_projects)
        settings.setValue("last_project_path", self.last_project_path)

    def add_recent_project(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        self.recent_projects = self.recent_projects[:10]  # Keep last 10
        self.save()

# ----------------------------------------------------------------------
# Project Manager
# ----------------------------------------------------------------------
class ProjectManager:
    """Handles project loading, saving, and switching."""
    def __init__(self, main_window):
        self.main_window = main_window
        self.base_dir = ""
        self.image_dir = ""
        self.media_dir = ""
        self.save_file = ""
        self.data = {}
        self.app_settings = AppSettings.load()

    def is_project_open(self):
        return bool(self.base_dir and os.path.exists(self.save_file))

    def create_new_project(self):
        dlg = ProjectSetupDialog(parent=self.main_window)
        if dlg.exec():
            name, folder = dlg.get_values()
            # Create project directory structure
            os.makedirs(folder, exist_ok=True)
            images_dir = os.path.join(folder, "images")
            media_dir = os.path.join(folder, "media")
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(media_dir, exist_ok=True)
            save_file = os.path.join(folder, "studio_project.json")
            data = default_data(name)
            with open(save_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.open_project(folder)
            return True
        return False

    def open_project(self, folder_path):
        save_file = os.path.join(folder_path, "studio_project.json")
        if not os.path.exists(save_file):
            QMessageBox.warning(self.main_window, "Invalid Project",
                                f"No studio_project.json found in {folder_path}")
            return False

        # Close current project first
        if self.is_project_open():
            self.main_window.save_data()  # Ensure current data saved

        self.base_dir = folder_path
        self.image_dir = os.path.join(folder_path, "images")
        self.media_dir = os.path.join(folder_path, "media")
        self.save_file = save_file
        self.load_data()

        # Update app settings
        self.app_settings.last_project_path = folder_path
        self.app_settings.add_recent_project(folder_path)
        self.app_settings.save()

        # Update UI
        self.main_window.on_project_loaded()
        return True

    def load_data(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.data.setdefault("project_name", os.path.basename(self.base_dir))
                self.data.setdefault("sections", [])
                self.data.setdefault("pages", {})
                return self.data
            except Exception:
                pass
        self.data = default_data(os.path.basename(self.base_dir))
        return self.data

    def save_data(self):
        if not self.save_file:
            return
        self.data["last_save"] = now()
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def get_project_name(self):
        return self.data.get("project_name", os.path.basename(self.base_dir))

    def rename_project(self, new_name):
        self.data["project_name"] = new_name
        self.save_data()
        return True

# ----------------------------------------------------------------------
# Dialogs
# ----------------------------------------------------------------------
class ProjectSetupDialog(QDialog):
    """Dialog for creating a new project."""
    def __init__(self, current_name="", current_dir="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.resize(500, 200)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(current_name)
        self.name_edit.setPlaceholderText("e.g. My Awesome Project")
        layout.addRow("Project Name:", self.name_edit)

        self.dir_edit = QLineEdit(current_dir)
        self.dir_edit.setPlaceholderText(os.path.join(os.path.expanduser("~"), "MyProject"))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)
        layout.addRow("Project Folder:", dir_layout)

        info_label = QLabel("A folder with this name will be created.")
        info_label.setStyleSheet("color: #8b949e;")
        layout.addRow(info_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _browse(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Parent Folder")
        if dir_path:
            self.dir_edit.setText(dir_path)

    def get_values(self):
        name = self.name_edit.text().strip()
        if not name:
            name = "Untitled Project"
        safe_name = "".join(c if c.isalnum() or c in "_- " else "_" for c in name).strip()
        safe_name = safe_name.replace(" ", "_")
        if not safe_name:
            safe_name = "Untitled_Project"
        folder = self.dir_edit.text().strip()
        if not folder:
            folder = os.path.join(os.path.expanduser("~"), safe_name)
        else:
            folder = os.path.join(folder.rstrip("/\\"), safe_name)
        return name, folder


class SettingsDialog(QDialog):
    """Application settings dialog."""
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        layout = QVBoxLayout(self)

        # Theme selection
        theme_group = QGroupBox("Appearance")
        theme_layout = QFormLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(settings.theme.capitalize())
        theme_layout.addRow("Theme:", self.theme_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(settings.font_size)
        theme_layout.addRow("Font Size:", self.font_size_spin)
        layout.addWidget(theme_group)

        # Startup behavior
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)
        self.open_last_check = QCheckBox("Open last project on startup")
        self.open_last_check.setChecked(settings.open_last_project)
        startup_layout.addRow(self.open_last_check)

        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(10, 300)
        self.auto_save_spin.setSuffix(" seconds")
        self.auto_save_spin.setValue(settings.auto_save_interval)
        startup_layout.addRow("Auto-save interval:", self.auto_save_spin)
        layout.addWidget(startup_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def apply(self):
        self.settings.theme = self.theme_combo.currentText().lower()
        self.settings.font_size = self.font_size_spin.value()
        self.settings.open_last_project = self.open_last_check.isChecked()
        self.settings.auto_save_interval = self.auto_save_spin.value()
        self.settings.save()


class CreditsDialog(QDialog):
    """Credits and about dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.resize(450, 300)
        layout = QVBoxLayout(self)

        title = QLabel(f"<h1>{APP_NAME}</h1>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel(f"<b>Version {VERSION}</b>")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        desc = QLabel("A versatile project management system for organizing content with custom fields, media attachments, and internal linking.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(10)

        credits = QLabel(
            "<b>Created by:</b> Your Name<br>"
            "<b>License:</b> MIT<br>"
            "<b>Built with:</b> Python, PySide6<br>"
            "<b>Icons:</b> Emoji-based for simplicity<br><br>"
            "This app can update itself automatically."
        )
        credits.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits)

        layout.addSpacing(10)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)


class UpdateChecker(QDialog):
    """Check for updates and perform self-update."""
    def __init__(self, parent=None, silent=False):
        super().__init__(parent)
        self.parent_window = parent
        self.silent = silent
        self.setWindowTitle("Check for Updates")
        self.resize(400, 150)
        layout = QVBoxLayout(self)
        self.label = QLabel("Checking for updates..." if not silent else "Checking in background...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton("Close", QDialogButtonBox.RejectRole)
        self.button_box.setEnabled(False)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.on_version_reply)
        self.manager.get(QNetworkRequest(QUrl(UPDATE_CHECK_URL)))
        self.new_version = None

    def on_version_reply(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NoError:
            remote_version = reply.readAll().data().decode().strip()
            if remote_version > VERSION:
                self.new_version = remote_version
                if self.silent and self.parent_window:
                    # Show status bar notification
                    self.parent_window.show_update_available(remote_version)
                    self.reject()
                    return
                else:
                    self.label.setText(f"<b>New version {remote_version} available!</b><br>Current: {VERSION}<br><br>Click 'Update Now' to download and restart.")
                    self.button_box.setEnabled(True)
                    update_btn = self.button_box.addButton("Update Now", QDialogButtonBox.AcceptRole)
                    update_btn.clicked.connect(self.download_update)
            else:
                if self.silent:
                    self.reject()
                    return
                self.label.setText(f"You are using the latest version ({VERSION}).")
                self.button_box.setEnabled(True)
        else:
            if self.silent:
                self.reject()
                return
            self.label.setText(f"Could not check for updates.<br>Please check your internet connection.")
            self.button_box.setEnabled(True)

    def download_update(self):
        self.label.setText("Downloading update...")
        self.button_box.setEnabled(False)
        self.download_manager = QNetworkAccessManager()
        self.download_manager.finished.connect(self.on_download_finished)
        self.download_manager.get(QNetworkRequest(QUrl(UPDATE_SCRIPT_URL)))

    def on_download_finished(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NoError:
            # Save downloaded script to a temporary file
            script_content = reply.readAll().data()
            temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.py')
            temp_file.write(script_content)
            temp_file.close()
            self.apply_update(temp_file.name)
        else:
            self.label.setText("Download failed. Please try again later.")
            self.button_box.setEnabled(True)

    def apply_update(self, new_script_path):
        """Replace current script with new version and restart."""
        current_script = os.path.abspath(sys.argv[0])
        try:
            # Backup current script
            backup_path = current_script + ".bak"
            shutil.copy2(current_script, backup_path)
            # Replace with new script
            shutil.copy2(new_script_path, current_script)
            os.unlink(new_script_path)
            self.label.setText("Update applied! Restarting...")
            QTimer.singleShot(1000, self.restart_app)
        except Exception as e:
            self.label.setText(f"Update failed: {str(e)}")
            self.button_box.setEnabled(True)

    def restart_app(self):
        """Restart the application."""
        self.accept()
        QProcess.startDetached(sys.executable, [sys.argv[0]])
        QApplication.quit()

# ----------------------------------------------------------------------
# Syntax Highlighter
# ----------------------------------------------------------------------
class PageSystemSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#58a6ff"))
        self.link_format.setFontWeight(QFont.Bold)

    def highlightBlock(self, text):
        pattern = re.compile(r"\[\[(.*?)\]\]")
        for match in pattern.finditer(text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self.link_format)

# ----------------------------------------------------------------------
# Media Attachment Gallery
# ----------------------------------------------------------------------
class MediaAttachmentWidget(QScrollArea):
    media_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.setStyleSheet("QScrollArea { border: 1px solid #30363d; border-radius: 6px; background: #0d1117; }")

        container = QWidget()
        self.setWidget(container)
        self.flow_layout = QGridLayout(container)
        self.flow_layout.setContentsMargins(8, 8, 8, 8)
        self.flow_layout.setSpacing(8)
        self.flow_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.attachments: List[Dict[str, str]] = []
        self._cards = []
        self.media_dir = ""

        self.setMinimumHeight(120)

    def set_media_dir(self, path):
        self.media_dir = path

    def set_attachments(self, attachments: List[Dict[str, str]]):
        self.attachments = attachments
        self._rebuild()

    def _rebuild(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        for i, att in enumerate(self.attachments):
            self._add_card(att, i)

        add_btn = QPushButton("+ Add Media")
        add_btn.setFixedSize(100, 100)
        add_btn.setStyleSheet("QPushButton { font-size: 12px; }")
        add_btn.clicked.connect(self._add_media_dialog)
        self.flow_layout.addWidget(add_btn, len(self.attachments) // 4, len(self.attachments) % 4)

    def _add_card(self, att: Dict[str, str], index: int):
        card = QFrame()
        card.setFixedSize(100, 100)
        card.setStyleSheet("QFrame { background: #161b22; border: 1px solid #30363d; border-radius: 6px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        typ = att.get("type", "image")
        filename = att.get("file", "")
        filepath = os.path.join(self.media_dir, filename)

        if typ in ("image", "gif") and os.path.exists(filepath):
            if typ == "gif":
                movie = QMovie(filepath)
                movie.setScaledSize(QSize(80, 60))
                lbl = QLabel()
                lbl.setMovie(movie)
                lbl.setAlignment(Qt.AlignCenter)
                movie.start()
                lbl._movie = movie
            else:
                pix = QPixmap(filepath).scaled(80, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl = QLabel()
                lbl.setPixmap(pix)
                lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)
        elif typ == "audio" and os.path.exists(filepath):
            lbl = QLabel("🔊 Audio")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)
            play_btn = QPushButton("Play")
            play_btn.setFixedHeight(20)
            play_btn.clicked.connect(lambda checked, f=filepath: self._play_audio(f))
            layout.addWidget(play_btn)
        else:
            lbl = QLabel("📦 3D Model" if typ == "model3d" else "📁 File")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        name_lbl = QLabel(os.path.splitext(filename)[0][:10] + "…" if len(filename) > 12 else filename)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("font-size: 9px; color: #8b949e;")
        layout.addWidget(name_lbl)

        card.setContextMenuPolicy(Qt.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos, idx=index: self._show_media_menu(pos, idx))
        self.flow_layout.addWidget(card, index // 4, index % 4)
        self._cards.append((card, typ, filename))

    def _show_media_menu(self, pos, index):
        menu = QMenu()
        remove_action = menu.addAction("Remove")
        action = menu.exec(self._cards[index][0].mapToGlobal(pos))
        if action == remove_action:
            del self.attachments[index]
            self.media_changed.emit()
            self._rebuild()

    def _add_media_dialog(self):
        if not self.media_dir:
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Add Media", "",
            "All Supported (*.png *.jpg *.jpeg *.bmp *.gif *.mp3 *.wav *.ogg *.obj *.gltf *.glb);;"
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;"
            "Audio (*.mp3 *.wav *.ogg);;"
            "3D Models (*.obj *.gltf *.glb)"
        )
        if not filepath:
            return
        self._add_media_file(filepath)

    def _add_media_file(self, src):
        ext = os.path.splitext(src)[1].lower()
        mediatype = MEDIA_CATEGORIES.get(ext, "file")
        base = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{mediatype}_{base}{ext}"
        dest = os.path.join(self.media_dir, filename)
        try:
            shutil.copy2(src, dest)
        except Exception as e:
            QMessageBox.warning(self, "Copy Error", f"Failed to copy media: {e}")
            return
        self.attachments.append({"type": mediatype, "file": filename})
        self.media_changed.emit()
        self._rebuild()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self._add_media_file(url.toLocalFile())
        event.acceptProposedAction()

    def _play_audio(self, filepath):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(filepath))
        self.audio_output.setVolume(0.8)
        self.player.play()

# ----------------------------------------------------------------------
# Category/Field Management Dialogs
# ----------------------------------------------------------------------
class ManageSectionsDialog(QDialog):
    def __init__(self, sections_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.resize(600, 500)
        self.sections = sections_data
        self._setup_ui()
        self._refresh_section_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.section_list = QListWidget()
        top.addWidget(self.section_list, 1)

        btn_layout = QVBoxLayout()
        self.add_btn = QPushButton("Add Category")
        self.add_btn.clicked.connect(self._add_section)
        self.del_btn = QPushButton("Delete Category")
        self.del_btn.clicked.connect(self._delete_section)
        self.rename_btn = QPushButton("Rename Category")
        self.rename_btn.clicked.connect(self._rename_section)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.rename_btn)
        btn_layout.addStretch()
        top.addLayout(btn_layout)
        layout.addLayout(top)

        self.field_group = QFrame()
        self.field_group.setStyleSheet("QFrame { border: 1px solid #30363d; border-radius: 6px; padding: 8px; }")
        field_layout = QVBoxLayout(self.field_group)
        field_layout.addWidget(QLabel("<b>Fields for selected category:</b>"))
        self.field_list = QListWidget()
        field_layout.addWidget(self.field_list, 1)
        field_btns = QHBoxLayout()
        self.add_field_btn = QPushButton("Add Field")
        self.add_field_btn.clicked.connect(self._add_field)
        self.del_field_btn = QPushButton("Delete Field")
        self.del_field_btn.clicked.connect(self._delete_field)
        self.edit_field_btn = QPushButton("Edit Field")
        self.edit_field_btn.clicked.connect(self._edit_field)
        field_btns.addWidget(self.add_field_btn)
        field_btns.addWidget(self.del_field_btn)
        field_btns.addWidget(self.edit_field_btn)
        field_layout.addLayout(field_btns)
        layout.addWidget(self.field_group)

        self.section_list.currentRowChanged.connect(self._on_section_selected)

        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def _refresh_section_list(self):
        self.section_list.clear()
        for sec in self.sections:
            self.section_list.addItem(sec["label"])

    def _add_section(self):
        name, ok = QInputDialog.getText(self, "New Category", "Internal ID (no spaces):")
        if not ok or not name.strip():
            return
        name = name.strip().lower().replace(" ", "_")
        label, ok = QInputDialog.getText(self, "New Category", "Display name:")
        if not ok or not label.strip():
            return
        if any(s["name"] == name for s in self.sections):
            QMessageBox.warning(self, "Error", "A category with this Internal ID already exists.")
            return
        self.sections.append({"name": name, "label": label, "fields": []})
        self._refresh_section_list()
        self.section_list.setCurrentRow(len(self.sections)-1)

    def _delete_section(self):
        row = self.section_list.currentRow()
        if row < 0:
            return
        reply = QMessageBox.question(self, "Delete Category",
                                     f"Delete Category '{self.sections[row]['label']}' and all its pages?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.sections[row]
            self._refresh_section_list()

    def _rename_section(self):
        row = self.section_list.currentRow()
        if row < 0:
            return
        new_label, ok = QInputDialog.getText(self, "Rename Category", "New label:", text=self.sections[row]["label"])
        if ok and new_label.strip():
            self.sections[row]["label"] = new_label.strip()
            self._refresh_section_list()

    def _on_section_selected(self, row):
        if row < 0:
            self.field_list.clear()
            return
        self._refresh_field_list(row)

    def _refresh_field_list(self, section_index=None):
        if section_index is None:
            section_index = self.section_list.currentRow()
        if section_index < 0:
            self.field_list.clear()
            return
        sec = self.sections[section_index]
        self.field_list.clear()
        for fld in sec.get("fields", []):
            self.field_list.addItem(f"{fld['label']} ({fld['type']})")

    def _add_field(self):
        row = self.section_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "No category", "Select a category first.")
            return
        dlg = FieldEditDialog(self)
        if dlg.exec():
            field_def = dlg.get_field_def()
            self.sections[row]["fields"].append(field_def)
            self._refresh_field_list(row)

    def _delete_field(self):
        sec_idx = self.section_list.currentRow()
        field_idx = self.field_list.currentRow()
        if sec_idx < 0 or field_idx < 0:
            return
        del self.sections[sec_idx]["fields"][field_idx]
        self._refresh_field_list(sec_idx)

    def _edit_field(self):
        sec_idx = self.section_list.currentRow()
        field_idx = self.field_list.currentRow()
        if sec_idx < 0 or field_idx < 0:
            return
        current = self.sections[sec_idx]["fields"][field_idx]
        dlg = FieldEditDialog(self, current)
        if dlg.exec():
            self.sections[sec_idx]["fields"][field_idx] = dlg.get_field_def()
            self._refresh_field_list(sec_idx)


class FieldEditDialog(QDialog):
    def __init__(self, parent=None, field_def=None):
        super().__init__(parent)
        self.setWindowTitle("Field Definition")
        self.resize(400, 300)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        layout.addRow("Field Name (key):", self.name_edit)

        self.label_edit = QLineEdit()
        layout.addRow("Display name:", self.label_edit)

        self.type_combo = QComboBox()
        for key, label in FIELD_TYPES.items():
            self.type_combo.addItem(label, key)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addRow("Type:", self.type_combo)

        self.options_edit = QLineEdit()
        self.options_edit.setPlaceholderText("Comma separated options")
        layout.addRow("Options (for dropdown):", self.options_edit)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(-9999, 9999)
        self.max_spin = QSpinBox()
        self.max_spin.setRange(-9999, 9999)
        self.max_spin.setValue(100)
        layout.addRow("Minimum:", self.min_spin)
        layout.addRow("Maximum:", self.max_spin)

        if field_def:
            self.name_edit.setText(field_def.get("name", ""))
            self.label_edit.setText(field_def.get("label", ""))
            idx = self.type_combo.findData(field_def.get("type", "line"))
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            if field_def.get("options"):
                self.options_edit.setText(", ".join(field_def["options"]))
            self.min_spin.setValue(field_def.get("min", 0))
            self.max_spin.setValue(field_def.get("max", 100))

        self._on_type_changed()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_type_changed(self):
        typ = self.type_combo.currentData()
        self.options_edit.setEnabled(typ == "combo")
        self.min_spin.setEnabled(typ == "spin")
        self.max_spin.setEnabled(typ == "spin")

    def get_field_def(self):
        typ = self.type_combo.currentData()
        field = {
            "name": self.name_edit.text().strip(),
            "label": self.label_edit.text().strip(),
            "type": typ,
        }
        if typ == "combo":
            opts = [x.strip() for x in self.options_edit.text().split(",") if x.strip()]
            field["options"] = opts if opts else ["Option 1"]
        if typ == "spin":
            field["min"] = self.min_spin.value()
            field["max"] = self.max_spin.value()
        return field


class ProjectSelectorDialog(QDialog):
    """Shows recent projects and options to create/open."""
    def __init__(self, recent_projects, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Welcome to {APP_NAME}")
        self.resize(500, 400)
        layout = QVBoxLayout(self)

        title = QLabel(f"<h1>{APP_NAME}</h1>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Recent projects
        recent_group = QGroupBox("Recent Projects")
        recent_layout = QVBoxLayout(recent_group)
        self.recent_list = QListWidget()
        for proj in recent_projects:
            if os.path.exists(os.path.join(proj, "studio_project.json")):
                self.recent_list.addItem(proj)
        if self.recent_list.count() == 0:
            self.recent_list.addItem("No recent projects")
            self.recent_list.setEnabled(False)
        recent_layout.addWidget(self.recent_list)
        layout.addWidget(recent_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("Create New Project")
        self.open_btn = QPushButton("Open Existing Project")
        self.open_selected_btn = QPushButton("Open Selected")
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.open_selected_btn)
        layout.addLayout(btn_layout)

        self.new_btn.clicked.connect(self.accept)
        self.open_btn.clicked.connect(self.reject)  # Will handle separately
        self.open_selected_btn.clicked.connect(self._open_selected)

        self.selected_project = None

    def _open_selected(self):
        item = self.recent_list.currentItem()
        if item and item.text() != "No recent projects":
            self.selected_project = item.text()
            self.done(2)  # Custom return code

# ----------------------------------------------------------------------
# Main Window
# ----------------------------------------------------------------------
class CreativeStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project = ProjectManager(self)
        self.current_section = None
        self.current_index = None
        self._field_widgets = {}
        self.app_settings = self.project.app_settings

        self.setWindowTitle(APP_NAME)
        self.resize(1200, 700)
        self._setup_ui()
        self._apply_app_settings()

        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.save_current_page_and_data)
        self.auto_save_timer.start(self.app_settings.auto_save_interval * 1000)

        # Check for updates in background after startup
        QTimer.singleShot(5000, self.check_for_updates_background)

    def _setup_ui(self):
        self.setStyleSheet(self._get_dark_style())  # Initial dark theme

        # Menu Bar
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self._new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction("Open Project...", self)
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)

        self.recent_menu = QMenu("Recent Projects", self)
        file_menu.addMenu(self.recent_menu)

        file_menu.addSeparator()
        save_all_action = QAction("Save All", self)
        save_all_action.triggered.connect(self.save_all)
        file_menu.addAction(save_all_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings)
        edit_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        updates_action = QAction("Check for Updates", self)
        updates_action.triggered.connect(self._check_updates)
        help_menu.addAction(updates_action)
        credits_action = QAction("About / Credits", self)
        credits_action.triggered.connect(self._show_credits)
        help_menu.addAction(credits_action)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        save_btn = QAction("💾 Save All", self)
        save_btn.triggered.connect(self.save_all)
        toolbar.addAction(save_btn)

        manage_cats_action = QAction("📂 Manage Categories", self)
        manage_cats_action.triggered.connect(self._manage_sections)
        toolbar.addAction(manage_cats_action)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Category:"))
        self.section_combo = QComboBox()
        self.section_combo.currentIndexChanged.connect(self._on_section_combo)
        toolbar.addWidget(self.section_combo)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search pages...")
        self.search_box.setMaximumWidth(250)
        self.search_box.textChanged.connect(self._filter_list)
        toolbar.addWidget(self.search_box)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(4, 4, 4, 4)

        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._list_context_menu)
        self.list_widget.currentRowChanged.connect(self._on_list_selection_changed)
        left_layout.addWidget(self.list_widget)

        btn_new = QPushButton("+ New Page")
        btn_new.clicked.connect(self._new_page)
        left_layout.addWidget(btn_new)

        splitter.addWidget(left_frame)

        # Right panel
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Page Title...")
        right_layout.addWidget(self.title_edit)

        self.media_gallery = MediaAttachmentWidget()
        self.media_gallery.media_changed.connect(self._on_media_changed)
        right_layout.addWidget(self.media_gallery)

        self.fields_container = QWidget()
        self.fields_layout = QFormLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(6)
        right_layout.addWidget(self.fields_container)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Write content. Link pages with [[Page Title]] ...")
        self.highlighter = PageSystemSyntaxHighlighter(self.editor.document())
        self.editor.textChanged.connect(self._update_preview)
        right_layout.addWidget(self.editor, 1)

        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenLinks(False)
        self.preview_browser.anchorClicked.connect(self._on_page_system_link_clicked)
        self.preview_browser.setMaximumHeight(150)
        self.preview_browser.setVisible(False)
        right_layout.addWidget(self.preview_browser)

        btn_save = QPushButton("💾 Save Page")
        btn_save.clicked.connect(self._save_page)
        right_layout.addWidget(btn_save)

        splitter.addWidget(right_frame)
        splitter.setSizes([300, 900])

        # Status bar with clickable update notification
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.update_label = QLabel()
        self.update_label.setStyleSheet("color: #58a6ff; text-decoration: underline;")
        self.update_label.hide()
        self.update_label.linkActivated.connect(self._check_updates_manual)
        self.status_bar.addPermanentWidget(self.update_label)

        # Initially disable UI until a project is loaded
        self._set_ui_enabled(False)

    def _set_ui_enabled(self, enabled):
        self.section_combo.setEnabled(enabled)
        self.search_box.setEnabled(enabled)
        self.list_widget.setEnabled(enabled)
        self.title_edit.setEnabled(enabled)
        self.media_gallery.setEnabled(enabled)
        self.editor.setEnabled(enabled)
        # Don't disable buttons that create/open projects

    def _apply_app_settings(self):
        # Apply font size
        font = QFont()
        font.setPointSize(self.app_settings.font_size)
        QApplication.setFont(font)
        # Apply theme
        if self.app_settings.theme == "light":
            self.setStyleSheet(self._get_light_style())
        else:
            self.setStyleSheet(self._get_dark_style())

    def _get_dark_style(self):
        return """
            QMainWindow { background-color: #0d1117; }
            QWidget {
                background-color: #0d1117;
                color: #e6edf3;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QListWidget, QTextEdit, QPlainTextEdit, QLineEdit, QSpinBox, QComboBox {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
                color: #e6edf3;
                selection-background-color: #1f6feb;
            }
            QListWidget::item:selected { background-color: #1f6feb; }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #30363d; border-color: #58a6ff; }
            QPushButton:pressed { background-color: #1f6feb; }
            QToolBar { background-color: #161b22; border: none; padding: 4px; spacing: 8px; }
            QSplitter::handle { background-color: #30363d; width: 2px; }
            QScrollBar:vertical { background: #0d1117; width: 10px; }
            QScrollBar::handle:vertical { background: #30363d; border-radius: 4px; min-height: 20px; }
            QMenuBar { background-color: #161b22; color: #e6edf3; }
            QMenuBar::item:selected { background-color: #1f6feb; }
            QMenu { background-color: #161b22; color: #e6edf3; border: 1px solid #30363d; }
            QMenu::item:selected { background-color: #1f6feb; }
            QStatusBar { background-color: #161b22; color: #8b949e; }
        """

    def _get_light_style(self):
        return """
            QMainWindow { background-color: #f6f8fa; }
            QWidget {
                background-color: #f6f8fa;
                color: #24292f;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QListWidget, QTextEdit, QPlainTextEdit, QLineEdit, QSpinBox, QComboBox {
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 6px;
                color: #24292f;
                selection-background-color: #0969da;
            }
            QListWidget::item:selected { background-color: #0969da; color: white; }
            QPushButton {
                background-color: #f6f8fa;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f3f4f6; border-color: #0969da; }
            QPushButton:pressed { background-color: #eaeef2; }
            QToolBar { background-color: #ffffff; border: none; border-bottom: 1px solid #d0d7de; padding: 4px; }
            QSplitter::handle { background-color: #d0d7de; width: 2px; }
            QMenuBar { background-color: #ffffff; color: #24292f; border-bottom: 1px solid #d0d7de; }
            QMenuBar::item:selected { background-color: #0969da; color: white; }
            QMenu { background-color: #ffffff; color: #24292f; border: 1px solid #d0d7de; }
            QMenu::item:selected { background-color: #0969da; color: white; }
            QStatusBar { background-color: #ffffff; color: #57606a; border-top: 1px solid #d0d7de; }
        """

    # ------------------------------------------------------------------
    # Update Handling
    # ------------------------------------------------------------------
    def check_for_updates_background(self):
        """Silent check for updates; shows notification in status bar if available."""
        self.update_checker = UpdateChecker(self, silent=True)
        # Dialog not shown; it will call show_update_available if needed

    def show_update_available(self, new_version):
        """Show clickable label in status bar."""
        self.update_label.setText(f'<a href="#">Update v{new_version} available - click to update</a>')
        self.update_label.show()
        self.status_bar.showMessage("", 0)  # clear temporary message

    def _check_updates(self):
        """Manual update check."""
        dlg = UpdateChecker(self, silent=False)
        dlg.exec()

    def _check_updates_manual(self, link):
        """Called when clicking the status bar update label."""
        self._check_updates()

    # ------------------------------------------------------------------
    # Project Management
    # ------------------------------------------------------------------
    def _new_project(self):
        if self.project.create_new_project():
            self._update_recent_menu()
            self.status_bar.showMessage(f"Opened project: {self.project.get_project_name()}", 3000)

    def _open_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if folder:
            if self.project.open_project(folder):
                self._update_recent_menu()
                self.status_bar.showMessage(f"Opened project: {self.project.get_project_name()}", 3000)

    def _open_recent_project(self, path):
        if self.project.open_project(path):
            self._update_recent_menu()
            self.status_bar.showMessage(f"Opened project: {self.project.get_project_name()}", 3000)

    def _update_recent_menu(self):
        self.recent_menu.clear()
        for path in self.project.app_settings.recent_projects:
            if os.path.exists(os.path.join(path, "studio_project.json")):
                action = QAction(os.path.basename(path), self)
                action.setData(path)
                action.triggered.connect(lambda checked, p=path: self._open_recent_project(p))
                self.recent_menu.addAction(action)
        if self.recent_menu.isEmpty():
            self.recent_menu.addAction("No recent projects").setEnabled(False)

    def on_project_loaded(self):
        self._set_ui_enabled(True)
        self.setWindowTitle(f"{APP_NAME} - {self.project.get_project_name()}")
        self.media_gallery.set_media_dir(self.project.media_dir)
        self._populate_section_combo()
        self._switch_section(None)
        if self.section_combo.count() > 0:
            self.section_combo.setCurrentIndex(0)
        self.save_all()  # Ensure data is consistent

    # ------------------------------------------------------------------
    # Data Access Helpers
    # ------------------------------------------------------------------
    def get_section_by_name(self, name):
        for sec in self.project.data["sections"]:
            if sec["name"] == name:
                return sec
        return None

    def current_list(self) -> List[Dict]:
        if self.current_section is None:
            return []
        if self.current_section not in self.project.data["pages"]:
            self.project.data["pages"][self.current_section] = []
        return self.project.data["pages"][self.current_section]

    def save_data(self):
        self.project.save_data()

    def save_current_page_and_data(self):
        if self.current_index is not None and self.current_section is not None:
            self._save_page()
        else:
            self.save_data()

    def save_all(self):
        if self.project.is_project_open():
            if self.current_index is not None:
                self._save_page()
            else:
                self.save_data()
            QMessageBox.information(self, "Saved", "All data saved.")
            self.status_bar.showMessage("All data saved", 2000)

    # ------------------------------------------------------------------
    # Section & Category Management
    # ------------------------------------------------------------------
    def _populate_section_combo(self):
        self.section_combo.blockSignals(True)
        self.section_combo.clear()
        for sec in self.project.data["sections"]:
            self.section_combo.addItem(sec["label"], sec["name"])
        self.section_combo.blockSignals(False)
        if self.section_combo.count() > 0:
            self.section_combo.setCurrentIndex(0)

    def _manage_sections(self):
        dlg = ManageSectionsDialog(self.project.data["sections"], self)
        if dlg.exec():
            for sec in self.project.data["sections"]:
                if sec["name"] not in self.project.data["pages"]:
                    self.project.data["pages"][sec["name"]] = []
            existing_names = {s["name"] for s in self.project.data["sections"]}
            for name in list(self.project.data["pages"].keys()):
                if name not in existing_names:
                    del self.project.data["pages"][name]
            self.save_data()
            self._populate_section_combo()
            if self.current_section is None and self.section_combo.count() > 0:
                self._switch_section(self.section_combo.currentData())

    def _switch_section(self, section_name):
        if section_name is None:
            self.current_section = None
            self.current_index = None
            self._rebuild_fields_ui()
            self._refresh_list()
            self.title_edit.clear()
            self.editor.clear()
            self.media_gallery.set_attachments([])
            self.preview_browser.setVisible(False)
            return
        self.current_section = section_name
        self.current_index = None
        self._rebuild_fields_ui()
        self._refresh_list()
        self.title_edit.clear()
        self.editor.clear()
        self.media_gallery.set_attachments([])
        self.preview_browser.setVisible(False)

    def _on_section_combo(self, index):
        if index < 0:
            return
        name = self.section_combo.currentData()
        self._switch_section(name)

    # ------------------------------------------------------------------
    # Dynamic Fields UI
    # ------------------------------------------------------------------
    def _rebuild_fields_ui(self):
        while self.fields_layout.count():
            child = self.fields_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._field_widgets = {}
        if self.current_section is None:
            return
        sec = self.get_section_by_name(self.current_section)
        if not sec:
            return
        for fdef in sec.get("fields", []):
            label = QLabel(fdef["label"] + ":")
            typ = fdef["type"]
            if typ == "line":
                w = QLineEdit()
            elif typ == "text":
                w = QPlainTextEdit()
                w.setMaximumHeight(80)
            elif typ == "combo":
                w = QComboBox()
                w.addItems(fdef.get("options", []))
            elif typ == "spin":
                w = QSpinBox()
                w.setMinimum(fdef.get("min", 0))
                w.setMaximum(fdef.get("max", 99999))
            else:
                w = QLineEdit()
            self.fields_layout.addRow(label, w)
            self._field_widgets[fdef["name"]] = w

    def _refresh_list(self):
        self.list_widget.clear()
        if self.current_section is None:
            return
        pages = self.current_list()
        filter_text = self.search_box.text().lower()
        for i, page in enumerate(pages):
            title = page.get("title", f"Untitled {i+1}")
            if filter_text and filter_text not in title.lower():
                continue
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, i)
            self.list_widget.addItem(item)

    def _filter_list(self):
        self._refresh_list()

    def _new_page(self):
        if self.current_section is None:
            QMessageBox.information(self, "No Category", "Create a category first (Manage Categories).")
            return
        sec = self.get_section_by_name(self.current_section)
        page = {"title": "New Page", "content": "", "fields": {}, "media": []}
        for fdef in sec.get("fields", []):
            name = fdef["name"]
            if fdef["type"] == "spin":
                page["fields"][name] = fdef.get("min", 0)
            elif fdef["type"] == "combo":
                options = fdef.get("options", [])
                page["fields"][name] = options[0] if options else ""
            else:
                page["fields"][name] = ""
        self.current_list().append(page)
        self._refresh_list()
        self.list_widget.setCurrentRow(len(self.current_list()) - 1)
        self.save_data()

    def _delete_page(self):
        if self.current_index is None:
            return
        reply = QMessageBox.question(self, "Delete", "Delete this page?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.current_list()[self.current_index]
            self.current_index = None
            self._refresh_list()
            self.title_edit.clear()
            self.editor.clear()
            self.media_gallery.set_attachments([])
            self.save_data()

    def _list_context_menu(self, pos):
        if self.list_widget.count() == 0:
            return
        menu = QMenu()
        del_action = menu.addAction("Delete page")
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == del_action:
            self._delete_page()

    def _on_list_selection_changed(self, row):
        if row < 0 or row >= self.list_widget.count():
            return
        item = self.list_widget.item(row)
        if item is None:
            return
        real_index = item.data(Qt.UserRole)
        if real_index is not None and real_index >= 0:
            self.current_index = real_index
            self._load_page_data(real_index)

    def _load_page_data(self, index):
        pages = self.current_list()
        if index < 0 or index >= len(pages):
            return
        page = pages[index]
        self.title_edit.setText(page.get("title", ""))
        self.media_gallery.set_attachments(page.get("media", []))
        for fname, w in self._field_widgets.items():
            value = page.get("fields", {}).get(fname)
            if isinstance(w, QLineEdit):
                w.setText(str(value) if value is not None else "")
            elif isinstance(w, QPlainTextEdit):
                w.setPlainText(str(value) if value is not None else "")
            elif isinstance(w, QComboBox):
                if value and value in [w.itemText(i) for i in range(w.count())]:
                    w.setCurrentText(value)
                else:
                    w.setCurrentIndex(0)
            elif isinstance(w, QSpinBox):
                try:
                    w.setValue(int(value) if value else 0)
                except:
                    w.setValue(0)
        self.editor.setPlainText(page.get("content", ""))
        self._update_preview()

    def _save_page(self):
        if self.current_index is None or self.current_section is None:
            return
        page = self.current_list()[self.current_index]
        page["title"] = self.title_edit.text()
        page["fields"] = {}
        for fname, w in self._field_widgets.items():
            if isinstance(w, QLineEdit):
                page["fields"][fname] = w.text()
            elif isinstance(w, QPlainTextEdit):
                page["fields"][fname] = w.toPlainText()
            elif isinstance(w, QComboBox):
                page["fields"][fname] = w.currentText()
            elif isinstance(w, QSpinBox):
                page["fields"][fname] = w.value()
        page["media"] = self.media_gallery.attachments
        page["content"] = self.editor.toPlainText()
        self.save_data()
        self._refresh_list()

    def _on_media_changed(self):
        pass

    # ------------------------------------------------------------------
    # Page System Links
    # ------------------------------------------------------------------
    def _update_preview(self):
        text = self.editor.toPlainText()
        if "[[" in text and "]]" in text:
            html = self._page_system_to_html(text)
            self.preview_browser.setHtml(html)
            self.preview_browser.setVisible(True)
        else:
            self.preview_browser.setVisible(False)

    def _page_system_to_html(self, text: str) -> str:
        def replace_link(match):
            title = match.group(1)
            for sec_name, pages in self.project.data["pages"].items():
                for page in pages:
                    if page.get("title", "").lower() == title.lower():
                        return f'<a href="{sec_name}:{title}" style="color:#58a6ff; text-decoration:none; font-weight:bold;">{title}</a>'
            return f'<span style="color:#8b949e;">{title}</span>'
        html = re.sub(r"\[\[(.*?)\]\]", replace_link, text)
        return html.replace("\n", "<br>")

    def _on_page_system_link_clicked(self, url):
        link = url.toString()
        if ":" in link:
            sec_name, title = link.split(":", 1)
            for i in range(self.section_combo.count()):
                if self.section_combo.itemData(i) == sec_name:
                    self.section_combo.setCurrentIndex(i)
                    break
            pages = self.project.data["pages"].get(sec_name, [])
            for idx, page in enumerate(pages):
                if page.get("title", "").lower() == title.lower():
                    self.list_widget.setCurrentRow(idx)
                    return
        QMessageBox.information(self, "Link", "Page not found.")

    def _show_settings(self):
        dlg = SettingsDialog(self.app_settings, self)
        if dlg.exec():
            self.app_settings = AppSettings.load()  # Reload after save
            self._apply_app_settings()
            self.auto_save_timer.setInterval(self.app_settings.auto_save_interval * 1000)

    def _show_credits(self):
        dlg = CreditsDialog(self)
        dlg.exec()


# ----------------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Load settings
    settings = AppSettings.load()
    window = CreativeStudio()

    # Show project selector if no recent project or open last project is disabled
    if settings.open_last_project and settings.last_project_path and os.path.exists(os.path.join(settings.last_project_path, "studio_project.json")):
        window.project.open_project(settings.last_project_path)
    else:
        # Show project selector dialog
        selector = ProjectSelectorDialog(settings.recent_projects, window)
        result = selector.exec()
        if result == QDialog.Accepted:
            window.project.create_new_project()
        elif result == 2 and selector.selected_project:
            window.project.open_project(selector.selected_project)
        else:
            # User canceled, create default empty project
            default_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), "CreativeStudio_Default")
            if not os.path.exists(default_path):
                os.makedirs(default_path, exist_ok=True)
                images_dir = os.path.join(default_path, "images")
                media_dir = os.path.join(default_path, "media")
                os.makedirs(images_dir, exist_ok=True)
                os.makedirs(media_dir, exist_ok=True)
                save_file = os.path.join(default_path, "studio_project.json")
                with open(save_file, "w") as f:
                    json.dump(default_data("Default Project"), f, indent=4)
            window.project.open_project(default_path)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
