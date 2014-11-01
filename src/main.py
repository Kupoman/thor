
import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import *


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("escape", sys.exit)
		self.win.setCloseRequestEvent("escape")

		self.taskMgr.add(self.main_loop, "MainLoop")

		background = OnscreenImage(parent=render2dp, image="art/background.png")
		base.cam2dp.node().getDisplayRegion(0).setSort(-20)

	def main_loop(self, task):
		return task.cont


app = Game()
app.run()