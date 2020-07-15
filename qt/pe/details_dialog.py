# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QAbstractItemView, QSizePolicy, QGridLayout, QSplitter, QFrame)

from hscommon.trans import trget
from hscommon.plat import ISWINDOWS
from ..details_dialog import DetailsDialog as DetailsDialogBase
from ..details_table import DetailsTable
from .image_viewer import (
    ViewerToolBar, ScrollAreaImageViewer, ScrollAreaController)
tr = trget("ui")


class DetailsDialog(DetailsDialogBase):
    def __init__(self, parent, app):
        self.vController = None
        super().__init__(parent, app)

    def _setupUi(self):
        self.setWindowTitle(tr("Details"))
        self.resize(502, 502)
        self.setMinimumSize(QSize(250, 250))
        self.splitter = QSplitter(Qt.Vertical)
        self.topFrame = QFrame()
        self.topFrame.setFrameShape(QFrame.StyledPanel)
        self.horizontalLayout = QGridLayout()
        # Minimum width for the toolbar in the middle:
        self.horizontalLayout.setColumnMinimumWidth(1, 10)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setColumnStretch(0, 32)
        # Smaller value for the toolbar in the middle to avoid excessive resize
        self.horizontalLayout.setColumnStretch(1, 2)
        self.horizontalLayout.setColumnStretch(2, 32)
        # This avoids toolbar getting incorrectly partially hidden when window resizes
        self.horizontalLayout.setRowStretch(0, 1)
        self.horizontalLayout.setRowStretch(1, 24)
        self.horizontalLayout.setRowStretch(2, 1)
        self.horizontalLayout.setSpacing(1)  # probably not important

        self.selectedImageViewer = ScrollAreaImageViewer(self, "selectedImage")
        self.horizontalLayout.addWidget(self.selectedImageViewer, 0, 0, 3, 1)
        # Use a specific type of controller depending on the underlying viewer type
        self.vController = ScrollAreaController(self)

        self.verticalToolBar = ViewerToolBar(self, self.vController)
        self.verticalToolBar.setOrientation(Qt.Orientation(Qt.Vertical))
        self.horizontalLayout.addWidget(self.verticalToolBar, 1, 1, 1, 1, Qt.AlignCenter)

        self.referenceImageViewer = ScrollAreaImageViewer(self, "referenceImage")
        self.horizontalLayout.addWidget(self.referenceImageViewer, 0, 2, 3, 1)
        self.topFrame.setLayout(self.horizontalLayout)
        self.splitter.addWidget(self.topFrame)
        self.splitter.setStretchFactor(0, 8)

        self.tableView = DetailsTable(self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.tableView.setSizePolicy(sizePolicy)
        # self.tableView.setMinimumSize(QSize(0, 190))
        # self.tableView.setMaximumSize(QSize(16777215, 190))
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setShowGrid(False)
        self.splitter.addWidget(self.tableView)
        self.splitter.setStretchFactor(1, 1)
        # Late population needed here for connections to the toolbar
        self.vController.setupViewers(
            self.selectedImageViewer, self.referenceImageViewer)
        # self.setCentralWidget(self.splitter)  # only as QMainWindow
        self.setWidget(self.splitter)  # only as QDockWidget

    def _update(self):
        if self.vController is None:  # Not yet constructed!
            return
        if not self.app.model.selected_dupes:
            # No item from the model, disable and clear everything.
            self.vController.resetViewersState()
            return
        dupe = self.app.model.selected_dupes[0]
        group = self.app.model.results.get_group_of_duplicate(dupe)
        ref = group.ref

        self.vController.updateView(ref, dupe, group)

    # --- Override
    def resizeEvent(self, event):
        self.ensure_same_sizes()
        if self.vController is None or not self.vController.bestFit:
            return
        # Only update the scaled down pixmaps
        self.vController.updateBothImages()

    def show(self):
        # Compute the maximum size the table view can reach
        # Assuming all rows below headers have the same height
        self.tableView.setMaximumHeight(
            self.tableView.rowHeight(1)
            * self.tableModel.model.row_count()
            + self.tableView.verticalHeader().sectionSize(0)
            # Windows seems to add a few pixels more to the table somehow
            + (5 if ISWINDOWS else 0))
        DetailsDialogBase.show(self)
        self.ensure_same_sizes()
        self._update()

    def ensure_same_sizes(self):
        # HACK This ensures same size while shrinking.
        # ReferenceViewer might be 1 pixel shorter in width
        # due to the toolbar in the middle keeping the same width,
        # so resizing in the GridLayout's engine leads to not enough space
        # left for the panel on the right.
        # This work as a QMainWindow, but doesn't work as a QDockWidget:
        # resize can only grow. Might need some custom sizeHint somewhere...
        # self.horizontalLayout.setColumnMinimumWidth(
        #     0, self.selectedImageViewer.size().width())
        # self.horizontalLayout.setColumnMinimumWidth(
        #     2, self.selectedImageViewer.size().width())

        # This works when expanding but it's ugly:
        if self.selectedImageViewer.size().width() > self.referenceImageViewer.size().width():
            # print(f"""Before selected size: {self.selectedImageViewer.size()}\n""",
            #       f"""Before reference size: {self.referenceImageViewer.size()}""")
            self.selectedImageViewer.resize(self.referenceImageViewer.size())
            # print(f"""After selected size: {self.selectedImageViewer.size()}\n""",
            #       f"""After reference size: {self.referenceImageViewer.size()}""")

    # model --> view
    def refresh(self):
        DetailsDialogBase.refresh(self)
        if self.isVisible():
            self._update()
