
import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

from direct.showbase.ShowBase import ShowBase, DirectObject
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui import DirectGui, DirectGuiGlobals

from panda3d.core import *

from monster import Monster
import commands


class GameState(object, DirectObject.DirectObject):
	def __init__(self, _base):
		DirectObject.DirectObject.__init__(self)
		self.base = _base

	def setup_ui(self):
		pass

	def update_ui(self):
		pass

	def main_loop(self):
		self.update_ui()

	def destroy(self):
		self.ignoreAll()


class CombatState(GameState):
	def __init__(self, _base):
		GameState.__init__(self, _base)
		self.accept("enter", self.cb_next_turn)

		# Increase the texture resolution on DirectGui
		default_font = DirectGuiGlobals.getDefaultFont()
		default_font.clear()
		default_font.setPixelsPerUnit(64)
		DirectGuiGlobals.setDefaultFont(default_font)

		# Combatants
		self.combatants = {}
		self.combatants['red'] = Monster(name="Red", hp=250, recovery=1)
		self.combatants['green'] = Monster(name="Green", hp=100, recovery=2)
		self.combatants['red'].target = self.combatants['green']
		self.combatants['green'].target = self.combatants['red']

		# Combat vars
		self.turn = 60
		self.ui_turn = DirectGui.DirectLabel(text=str(self.turn),
											 text_fg=(1, 1, 1, 1),
											 text_shadow=(0, 0, 0, 1),
											 frameColor=(0, 0, 0, 0),
											 scale=0.2,
											 pos=(0, 0, 0.8))

		_range = value = self.combatants['red'].current_hp
		self.ui_player_health = DirectGui.DirectWaitBar(range=_range,
														value=value,
														barColor=(0, 1, 0, 1),
														scale=0.3,
														pos=(-0.8, 0, 0.4))

		self.ui_player_stamina = DirectGui.DirectWaitBar(range=100,
														 value=0,
														 barColor=(0, 0, 1, 1),
														 scale=(0.3, 1, 0.15),
														 pos=(-0.8, 0, 0.37))
		self.player_spells = [
			commands.Attack,
			commands.Wait,
			]
		num_spells = len(self.player_spells) - 1
		def use_command(command, combatant):
			command.run(combatant)
			self.turn_end = True
		self.ui_player_spells = [
			DirectGui.DirectButton(image=v.icon,
								   scale=0.05,
								   pos=(-1.0 + (0.125 * i), 0, -0.8 + 0.075 * (i % 2)),
								   command=use_command,
								   extraArgs=[v, self.combatants['red']],
								   )
			for i, v in enumerate(self.player_spells)
		]

		_range = value = self.combatants['green'].current_hp
		self.ui_enemy_health = DirectGui.DirectWaitBar(range=_range,
													   value=value,
													   barColor=(0, 1, 0, 1),
													   scale=0.3,
													   pos=(0.8, 0, 0.4))

		self.ui_enemy_stamina = DirectGui.DirectWaitBar(range=100,
														value=0,
														barColor=(0, 0, 1, 1),
														scale=(0.3, 1, 0.15),
														pos=(0.8, 0, 0.37))

		background = OnscreenImage(parent=self.base.render2dp, image="art/background.png")
		self.base.cam2dp.node().getDisplayRegion(0).setSort(-20)

		self.turn_end = False

	def cb_next_turn(self):
		self.turn_end = True

	def main_loop(self):
		if not self.turn_end:
			return

		self.turn -= 1
		self.combatants['red'].current_stamina += self.combatants['red'].recovery
		self.combatants['green'].current_stamina += self.combatants['green'].recovery
		self.ui_turn['text'] = str(self.turn)
		self.ui_player_health['value'] = self.combatants['red'].current_hp
		self.ui_player_stamina['value'] = self.combatants['red'].current_stamina
		self.ui_enemy_health['value'] = self.combatants['green'].current_hp
		self.ui_enemy_stamina['value'] = self.combatants['green'].current_stamina
		self.turn_end = False


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("escape", sys.exit)
		self.win.setCloseRequestEvent("escape")

		self.game_state = CombatState(self)
		self.taskMgr.add(self.main_loop, "MainLoop")

	def main_loop(self, task):
		self.game_state.main_loop()
		return task.cont


app = Game()
app.run()