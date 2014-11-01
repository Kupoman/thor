
import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui import DirectGui, DirectGuiGlobals

from panda3d.core import *


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("escape", sys.exit)
		self.win.setCloseRequestEvent("escape")

		# Combat vars
		self.turn = 60
		self.ui_turn = DirectGui.DirectLabel(text=str(self.turn),
											 frameColor=(0, 0, 0, 0),
											 scale=0.2,
											 pos=(0, 0, 0.8))

		self.player_health = 100
		self.player_max_health = 100
		self.ui_player_health = DirectGui.DirectWaitBar(range=self.player_max_health,
														value=self.player_health,
														barColor=(0, 1, 0, 1),
														scale=0.3,
														pos=(-0.8, 0, 0.4))
		self.player_spells = [
			('One', 'art/attacks/cold-fire.png'),
			('Two', 'art/attacks/cure-1.png'),
		]
		num_spells = len(self.player_spells) - 1
		self.ui_player_spells = [
			DirectGui.DirectButton(image=v[1],
								   scale=0.1,
								   pos=(-0.25*(num_spells - i), 0, -0.6),
								   )
			for i, v in enumerate(self.player_spells)
		]

		self.enemy_health = 100
		self.enemy_max_health = 100
		self.ui_enemy_health = DirectGui.DirectWaitBar(range=self.enemy_max_health,
														value=self.enemy_health,
														barColor=(0, 1, 0, 1),
														scale=0.3,
														pos=(0.8, 0, 0.4))

		self.taskMgr.add(self.main_loop, "MainLoop")

		background = OnscreenImage(parent=render2dp, image="art/background.png")
		base.cam2dp.node().getDisplayRegion(0).setSort(-20)

	def main_loop(self, task):
		self.turn -= 1
		self.player_health -= 1
		self.enemy_health -= 1
		self.ui_turn['text'] = str(self.turn)
		self.ui_player_health['value'] = self.player_health
		self.ui_enemy_health['value'] = self.enemy_health
		return task.cont


app = Game()
app.run()