"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp


class AppSettings(qtw.QWidget):
    """
    Widget for application settings.
    """

    on_change_signal = qtc.Signal()
    """
    This signal gets emitted every time
    the user changes some setting.
    """

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.settings

        self.setObjectName("root")

        flayout = qtw.QFormLayout()
        self.setLayout(flayout)

        self.logs_num_box = qtw.QSpinBox()
        self.logs_num_box.setRange(-1, 100)
        self.logs_num_box.setValue(self.app.app_config["keep_logs_num"])
        self.logs_num_box.valueChanged.connect(self.on_change)
        flayout.addRow(self.mloc.keep_logs_num, self.logs_num_box)

        self.log_level_box = qtw.QComboBox()
        self.log_level_box.addItems(
            [loglevel.capitalize() for loglevel in utils.LOG_LEVELS.values()]
        )
        self.log_level_box.setCurrentText(self.app.app_config["log_level"].capitalize())
        self.log_level_box.currentTextChanged.connect(self.on_change)
        flayout.addRow(self.mloc.log_level, self.log_level_box)

        self.app_lang_box = qtw.QComboBox()
        self.app_lang_box.addItem("System")
        self.app_lang_box.addItems(self.app.loc.get_available_langs())
        self.app_lang_box.setCurrentText(self.app.app_config["language"])
        self.app_lang_box.currentTextChanged.connect(self.on_change)
        flayout.addRow(self.mloc.app_lang, self.app_lang_box)

        color_hlayout = qtw.QHBoxLayout()
        self.accent_color_entry = qtw.QLineEdit()
        self.accent_color_entry.setText(self.app.app_config["accent_color"])
        self.accent_color_entry.textChanged.connect(self.on_change)
        color_hlayout.addWidget(self.accent_color_entry)
        self.choose_color_button = qtw.QPushButton()

        def choose_color():
            colordialog = qtw.QColorDialog(self.app.root)
            colordialog.setOption(
                colordialog.ColorDialogOption.DontUseNativeDialog, on=True
            )
            colordialog.setCustomColor(0, qtg.QColor("#8197ec"))
            color = self.accent_color_entry.text()
            if qtg.QColor.isValidColor(color):
                colordialog.setCurrentColor(qtg.QColor(color))
            if colordialog.exec():
                self.accent_color_entry.setText(
                    colordialog.currentColor().name(qtg.QColor.NameFormat.HexRgb)
                )
                self.choose_color_button.setIcon(
                    qta.icon(
                        "mdi6.square-rounded", color=self.accent_color_entry.text()
                    )
                )

        self.choose_color_button.setText(self.mloc.choose_color)
        self.choose_color_button.setIconSize(qtc.QSize(24, 24))
        self.choose_color_button.clicked.connect(choose_color)
        self.choose_color_button.setIcon(
            qta.icon("mdi6.square-rounded", color=self.app.app_config["accent_color"])
        )
        color_hlayout.addWidget(self.choose_color_button)
        flayout.addRow(self.mloc.accent_color, color_hlayout)

        self.confidence_box = qtw.QDoubleSpinBox()
        self.confidence_box.setLocale(qtc.QLocale.Language.English)
        self.confidence_box.setRange(0, 1)
        self.confidence_box.setSingleStep(0.05)
        self.confidence_box.setValue(self.app.app_config["detector_confidence"])
        self.confidence_box.valueChanged.connect(self.on_change)
        flayout.addRow(self.mloc.detector_confidence, self.confidence_box)

        self.bind_nxm_checkbox = qtw.QCheckBox(
            self.mloc.auto_bind_nxm + " [EXPERIMENTAL]"
        )
        self.bind_nxm_checkbox.setChecked(self.app.app_config["auto_bind_nxm"])
        self.bind_nxm_checkbox.stateChanged.connect(self.on_change)
        flayout.addRow(self.bind_nxm_checkbox)

    def on_change(self, *args):
        """
        This emits change signal without passing parameters.
        """

        self.on_change_signal.emit()

    def get_settings(self):
        return {
            "keep_logs_num": self.logs_num_box.value(),
            "log_level": self.log_level_box.currentText().lower(),
            "language": self.app_lang_box.currentText(),
            "accent_color": self.accent_color_entry.text(),
            "detector_confidence": self.confidence_box.value(),
            "auto_bind_nxm": self.bind_nxm_checkbox.isChecked(),
        }
