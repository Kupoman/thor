from __future__ import print_function
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
		self.ui_base = DirectGui.DirectFrame(frameColor=(0, 0, 0, 0))
		self.player_monster = _base.player_monster

	def update_ui(self):
		pass

	def main_loop(self):
		self.update_ui()

	def destroy(self):
		self.ignoreAll()
		self.ui_base.destroy()


class CombatState(GameState):
	def __init__(self, _base):
		GameState.__init__(self, _base)
		self.accept("enter", self.cb_next_turn)

		# Combatants
		self.combatants = {}
		self.combatants['red'] = self.player_monster
		self.combatants['green'] = Monster(name="Green", stamina=2)
		self.combatants['red'].target = self.combatants['green']
		self.combatants['green'].target = self.combatants['red']

		# Combat vars
		self.turn = 60
		self.player_spells = [
			commands.Attack,
			commands.Wait,
			]

		self.background = OnscreenImage(parent=self.base.render2dp, image="art/background.png")
		self.base.cam2dp.node().getDisplayRegion(0).setSort(-20)

		self.turn_end = False

		self.setup_ui()

	def destroy(self):
		GameState.destroy(self)
		self.background.destroy()

	def cb_next_turn(self):
		self.turn_end = True

	def setup_ui(self):
		self.ui_turn = DirectGui.DirectLabel(text=str(self.turn),
											 text_fg=(1, 1, 1, 1),
											 text_shadow=(0, 0, 0, 1),
											 frameColor=(0, 0, 0, 0),
											 scale=0.2,
											 pos=(0, 0, 0.8))
		self.ui_turn.reparentTo(self.ui_base)

		_range = value = self.combatants['red'].current_hp
		self.ui_player_health = DirectGui.DirectWaitBar(range=_range,
														value=value,
														barColor=(0, 1, 0, 1),
														scale=0.3,
														pos=(-0.8, 0, 0.4))
		self.ui_player_health.reparentTo(self.ui_base)

		self.ui_player_stamina = DirectGui.DirectWaitBar(range=100,
														 value=0,
														 barColor=(0, 0, 1, 1),
														 scale=(0.3, 1, 0.15),
														 pos=(-0.8, 0, 0.37))
		self.ui_player_stamina.reparentTo(self.ui_base)

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
		for i in self.ui_player_spells:
			i.reparentTo(self.ui_base)

		_range = value = self.combatants['green'].current_hp
		self.ui_enemy_health = DirectGui.DirectWaitBar(range=_range,
													   value=value,
													   barColor=(0, 1, 0, 1),
													   scale=0.3,
													   pos=(0.8, 0, 0.4))
		self.ui_enemy_health.reparentTo(self.ui_base)

		self.ui_enemy_stamina = DirectGui.DirectWaitBar(range=100,
														value=0,
														barColor=(0, 0, 1, 1),
														scale=(0.3, 1, 0.15),
														pos=(0.8, 0, 0.37))
		self.ui_enemy_stamina.reparentTo(self.ui_base)

	def update_ui(self):
		self.ui_turn['text'] = str(self.turn)
		self.ui_player_health['value'] = self.combatants['red'].current_hp
		self.ui_player_stamina['value'] = self.combatants['red'].current_stamina
		self.ui_enemy_health['value'] = self.combatants['green'].current_hp
		self.ui_enemy_stamina['value'] = self.combatants['green'].current_stamina

	def main_loop(self):
		GameState.main_loop(self)

		if self.turn_end:
			self.turn -= 1
			self.combatants['red'].current_stamina += self.combatants['red'].recovery
			self.combatants['green'].current_stamina += self.combatants['green'].recovery
			self.turn_end = False


class FarmState(GameState):
	def __init__(self, _base):
		GameState.__init__(self, _base)

		self.options = [
			('Combat', self.do_combat),
			('Training', self.do_training_menu),
		]

		self.training_options = [
			'attack',
			'defense',
			'intelligence',
			'stamina',
			'speed',
			'back',
		]

		self.setup_ui()

	def do_combat(self):
		self.base.change_state(CombatState)

	def do_training_menu(self):
		self.ui_main_menu.hide()
		self.ui_training_menu.show()

	def do_training(self, stat):
		if stat != 'back':
			prev_stat = getattr(self.player_monster, stat)
			print("Raising stat", stat, "from", prev_stat, "to ", end='')
			setattr(self.player_monster, stat, prev_stat + 1)
			print(getattr(self.player_monster, stat))

		self.ui_training_menu.hide()
		self.ui_main_menu.show()

	def setup_ui(self):
		# Main menu
		self.ui_main_menu = DirectGui.DirectFrame(frameColor=(0, 0, 0, 0))
		self.ui_main_menu.reparentTo(self.ui_base)

		for i, v in enumerate(self.options):
			btn = DirectGui.DirectButton(text=v[0],
								   command=v[1],
								   scale=0.2,
								   pos=(0, 0, 0.8 - 0.3 * i),
								   )
			btn.reparentTo(self.ui_main_menu)

		# Training menu
		self.ui_training_menu = DirectGui.DirectFrame(frameColor=(0, 0, 0, 0))
		self.ui_training_menu.reparentTo(self.ui_base)
		self.ui_training_menu.hide()

		for i, v in enumerate(self.training_options):
			btn = DirectGui.DirectButton(text=v.title(),
										 command=self.do_training,
										 extraArgs=[v],
										 scale=0.2,
										 pos=(0, 0, 0.8 - 0.3 * i),
										 )
			btn.reparentTo(self.ui_training_menu)


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		# Increase the texture resolution on DirectGui
		default_font = DirectGuiGlobals.getDefaultFont()
		default_font.clear()
		default_font.setPixelsPerUnit(64)
		DirectGuiGlobals.setDefaultFont(default_font)

		self.accept("escape", sys.exit)
		self.win.setCloseRequestEvent("escape")

		# Setup the player's monster
		self.player_monster = Monster(name="Red", defense=2)

		# Setup game states
		self.game_state = FarmState(self)
		self.taskMgr.add(self.main_loop, "MainLoop")

	def change_state(self, new_state):
		self.game_state.destroy()
		self.game_state = new_state(self)

	def main_loop(self, task):
		self.game_state.main_loop()
		return task.cont


app = Game()
app.run()