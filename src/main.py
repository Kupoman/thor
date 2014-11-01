
import sys

import os
from direct.gui import DirectLabel

os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import *

from direct.gui import DirectGui


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("escape", sys.exit)
		self.win.setCloseRequestEvent("escape")

		# Combat vars
		self.turn = 60
		self.ui_turn = DirectGui.DirectLabel(text=str(self.turn), frameColor=(0, 0, 0, 0))

		self.taskMgr.add(self.main_loop, "MainLoop")

		background = OnscreenImage(parent=render2dp, image="art/background.png")
		base.cam2dp.node().getDisplayRegion(0).setSort(-20)

	def main_loop(self, task):
		self.turn -= 1
		self.ui_turn['text'] = str(self.turn)
		return task.cont


app = Game()
app.run()