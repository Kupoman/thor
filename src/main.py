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
import appdirs
import uuid
import json


class Trainer(object):
	@classmethod
	def deserialize(cls, json_dictionary):
		ret = cls()
		ret.weeks = json_dictionary['weeks']
		ret.uuid = json_dictionary['uuid']
		if 'monster' in json_dictionary:
			ret.monster = Monster.deserialize(json_dictionary['monster'])

		return ret

	def __init__(self, name="Trainer"):
		self.name = name
		self.monster = None
		self.weeks = 0
		self.uuid = str(uuid.uuid4())
		while uuid in base.saved_trainer_ids:
			self.uuid = str(uuid.uuid4())

	def serialize(self):
		data = {}
		data['weeks'] = self.weeks
		data['name'] = self.name
		data['uuid'] = self.uuid
		if self.monster:
			data['monster'] = self.monster.serialize()

		return data


class GameState(object, DirectObject.DirectObject):
	def __init__(self, _base):
		DirectObject.DirectObject.__init__(self)
		self.base = _base
		self.ui_base = DirectGui.DirectFrame(frameColor=(0, 0, 0, 0))
		self.player = _base.player

	def update_ui(self):
		pass

	def main_loop(self):
		self.update_ui()

	def change_player(self, new_player):
		self.player = self.base.player = new_player

	def destroy(self):
		self.ignoreAll()
		self.ui_base.destroy()

		with open(os.path.join(self.base.save_dir, self.player.uuid) + '.sav', 'w') as f:
			json.dump(self.player.serialize(), f)


class CombatState(GameState):
	def __init__(self, _base):
		GameState.__init__(self, _base)
		self.accept("enter", self.cb_next_turn)

		# Set Camera
		self.base.disableMouse()
		self.base.camera.setPos(0, -5, 2.25)
		self.base.camera.setHpr(0, -10, 0)
		self.base.camLens.setFov(65)

		# Combatants
		self.combatants = {}
		self.combatants['red'] = self.player.monster
		self.combatants['red'].current_stamina = 50
		self.combatants['red'].current_hp = self.combatants['red'].hp
		self.model_red = None
		if self.combatants['red'].visual:
			self.model_red = base.loader.loadModel(self.combatants['red'].visual)
			self.model_red.setPos(-2, 1.5, 0)
			self.model_red.setHpr(-90, 0, 0)
			self.model_red.reparentTo(base.render)
		g_race = "golem" if self.player.monster.race.lower() == "ogre" else "ogre"
		self.combatants['green'] = Monster.new_from_race(g_race)
		self.combatants['green'].current_hp = self.combatants['green'].hp
		self.combatants['green'].current_stamina = 50
		if self.combatants['green'].visual:
			self.model_green = base.loader.loadModel(self.combatants['green'].visual)
			self.model_green.setPos(2, 1.5, 0)
			self.model_green.setHpr(90, 0, 0)
			self.model_green.reparentTo(base.render)

		self.combatants['red'].target = self.combatants['green']
		self.combatants['green'].target = self.combatants['red']

		# Combat vars
		self.turn = 60
		self.player_spells = [
			commands.Attack,
			commands.Wait,
			]

		self.base.background.setImage("art/background.png")

		self.player_command = None

		self.setup_ui()

	def destroy(self):
		GameState.destroy(self)
		if self.model_red:
			self.model_red.removeNode()
		if self.model_green:
			self.model_green.removeNode()

	def cb_next_turn(self):
		self.player_command = commands.Wait

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
		def use_command(command):
			self.player_command = command
		self.ui_player_spells = [
			DirectGui.DirectButton(image=v.icon,
								   scale=0.05,
								   pos=(-1.0 + (0.125 * i), 0, -0.8 + 0.075 * (i % 2)),
								   command=use_command,
								   extraArgs=[v],
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

		if self.player_command:
			if self.player.monster.initiative > self.combatants['green']:
				self.player_command.run(self.player.monster)
				commands.Attack.run(self.combatants['green'])
			else:
				commands.Attack.run(self.combatants['green'])
				self.player_command.run(self.player.monster)
			self.turn -= 1
			self.combatants['red'].current_stamina += self.combatants['red'].recovery
			self.combatants['green'].current_stamina += self.combatants['green'].recovery
			self.player_command = None

		if self.combatants['red'].current_hp <= 0 or \
			self.combatants['green'].current_hp <= 0:
			self.player.weeks += 1
			self.base.change_state(FarmState)


class FarmState(GameState):
	def __init__(self, _base):
		GameState.__init__(self, _base)

		self.options = [
			('Combat', self.do_combat),
			('Training', self.do_training_menu),
			('Monster Info', self.do_monster_stats),
			('Quit', self.do_exit),
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


		self.base.background.setImage("art/menu_background.png")

	def do_combat(self):
		self.base.change_state(CombatState)

	def do_training_menu(self):
		self.ui_main_menu.hide()
		self.ui_training_menu.show()

	def do_training(self, stat):
		if stat == 'back':
			self.ui_training_menu.hide()
			self.ui_main_menu.show()
		else:
			prev_stat = getattr(self.player.monster, stat)
			setattr(self.player.monster, stat, prev_stat + 1)
			result_str = "Raising stat {} from {} to {}.".format(stat.title(), prev_stat, getattr(self.player.monster, stat))
			print(result_str)
			self.ui_training_results_text['text'] = result_str

			self.ui_training_menu.hide()
			self.ui_training_results.show()

	def do_monster_stats(self):
		self.ui_main_menu.hide()
		self.ui_monster_stats.show()

	def do_exit(self):
		self.base.change_state(TitleState)

	def setup_ui(self):
		# Main menu
		self.ui_main_menu = DirectGui.DirectFrame(frameSize=(-4.0/3, 4.0/3, -1, 1),
			frameColor=(0, 0, 0, 0))
		self.ui_main_menu.reparentTo(self.ui_base)

		for i, v in enumerate(self.options):
			btn = DirectGui.DirectButton(text=v[0],
										 text_fg=(1, 1, 1, 1),
										 text_shadow=(0, 0, 0, 1),
										 relief=None,
										 command=v[1],
										 scale=0.2,
										 pos=(0, 0, 0.7 - 0.35 * i),
										 )
			btn.reparentTo(self.ui_main_menu)

		self.ui_weeks = DirectGui.DirectLabel(text='',
											  text_fg=(1, 1, 1, 1),
											  text_shadow=(0, 0, 0, 1),
											  scale=0.1,
											  pos=(-1.0, 0, -0.9),
											  )
		self.ui_weeks.reparentTo(self.ui_base)

		# Training menu
		self.ui_training_menu = DirectGui.DirectFrame(frameColor=(0, 0, 0, 0))
		self.ui_training_menu.reparentTo(self.ui_base)
		self.ui_training_menu.hide()

		for i, v in enumerate(self.training_options):
			btn = DirectGui.DirectButton(text=v.title(),
										 text_fg=(1, 1, 1, 1),
										 text_shadow=(0, 0, 0, 1),
										 relief=None,
										 command=self.do_training,
										 extraArgs=[v],
										 scale=0.15,
										 pos=(0, 0, 0.8 - 0.25 * i),
										 )
			btn.reparentTo(self.ui_training_menu)

		# Training results
		self.ui_training_results = DirectGui.DirectFrame(frameColor=(0, 0, 0, 0))
		self.ui_training_results.reparentTo(self.ui_base)
		self.ui_training_results.hide()

		self.ui_training_results_text = DirectGui.DirectLabel(text='',
															  text_fg=(1, 1, 1, 1),
															  text_shadow = (0, 0, 0, 1),
															  scale=0.2,
															  pos=(0, 0, 0.6),
															  )
		self.ui_training_results_text.reparentTo(self.ui_training_results)

		def training_results_okay():
			self.ui_training_results.hide()
			self.ui_main_menu.show()
			self.player.weeks += 1
		self.ui_training_results_okay = DirectGui.DirectButton(text="Okay",
															   command=training_results_okay,
															   scale=0.2,
															   pos=(0, 0, -0.2),
															   )
		self.ui_training_results_okay.reparentTo(self.ui_training_results)

		# Monster stats
		self.ui_monster_stats = DirectGui.DirectFrame(frameColor=(1, 1, 1, 0.33),
													  frameSize=(-1, 1, -0.7, 0.9),
													  relief=DirectGuiGlobals.GROOVE,
													  borderWidth=(0.01, 0.01),
													  )
		self.ui_monster_stats.reparentTo(self.ui_base)
		self.ui_monster_stats.hide()

		self.ui_monster_name = DirectGui.DirectLabel(text='',
													 frameColor=(0, 0, 0, 0),
													 scale=0.1,
													 )
		self.ui_monster_name['text'] = "{} [{}]".format(self.player.monster.name, self.player.monster.race)
		self.ui_monster_name.resetFrameSize()
		self.ui_monster_name.setPos(0, 0, 0.7)
		self.ui_monster_name.reparentTo(self.ui_monster_stats)
		self.ui_monster_base_stats = {}
		for i, v in enumerate(self.training_options):
			if v == 'back':
				continue

			label = DirectGui.DirectLabel(text=v.title(),
									  frameColor=(0, 0, 0, 0),
									  scale=0.05,
									  pos=(-0.8, 0, 0.55 - 0.1 * i),
									  )
			label.reparentTo(self.ui_monster_stats)
			bar = DirectGui.DirectWaitBar(range=100,
										  value=0,
										  scale=0.3,
										  pos=(-0.35, 0, 0.56 - 0.1 * i),
										  )
			bar.reparentTo(self.ui_monster_stats)
			self.ui_monster_base_stats[v] = bar

		def monster_stats_okay():
			self.ui_monster_stats.hide()
			self.ui_main_menu.show()
		self.ui_monster_stats_okay = DirectGui.DirectButton(text="Okay",
															text_fg=(1, 1, 1, 1),
															text_shadow=(0, 0, 0, 1),
															relief=None,
															command=monster_stats_okay,
															scale=0.1,
															pos=(0, 0, -0.6),
															)
		self.ui_monster_stats_okay.reparentTo(self.ui_monster_stats)

	def update_ui(self):
		self.ui_weeks['text'] = "Weeks: {}".format(self.player.weeks)

		for k, v in self.ui_monster_base_stats.iteritems():
			v['value'] = getattr(self.player.monster, k)


class TitleState(GameState):
	def __init__(self, _base):
		GameState.__init__(self, _base)

		self.options = [
			('New Trainer', self.do_new),
			('Load Trainer', self.do_load),
			('Exit Game', self.do_exit),
		]

		self.trainer_saves = {}
		for sav in os.listdir(self.base.save_dir):
			with open(os.path.join(self.base.save_dir, sav)) as f:
				self.trainer_saves[sav.split('.')[0]] = json.load(f)

		self.setup_ui()

	def do_new(self):
		self.ui_main_menu.hide()
		self.ui_new_trainer.show()

	def do_load(self):
		self.ui_main_menu.hide()
		self.ui_load_trainer.show()

	def do_exit(self):
		sys.exit()

	def setup_ui(self):
		self.ui_main_menu = DirectGui.DirectFrame(frameSize=(-4.0/3, 4.0/3, -1, 1),
												  frameColor=(0, 0, 0, 0))
		self.ui_main_menu.reparentTo(self.ui_base)

		for i, v in enumerate(self.options):
			btn = DirectGui.DirectButton(text=v[0],
										 text_fg=(1, 1, 1, 1),
										 text_shadow=(0, 0, 0, 1),
										 relief=None,
										 command=v[1],
										 scale=0.2,
										 pos=(0, 0, 0.4 - 0.35 * i),
										 )
			btn.reparentTo(self.ui_main_menu)

		# New Trainer
		self.ui_new_trainer = DirectGui.DirectFrame()
		self.ui_new_trainer.reparentTo(self.ui_base)
		self.ui_new_trainer.hide()

		self.ui_new_trainer_name = DirectGui.DirectEntry(initialText='Trainer',
														 frameColor=(1, 1, 1, 0.33),
														 scale=0.1,
														 pos=(-0.5, 0, 0),
														 )
		self.ui_new_trainer_name.reparentTo(self.ui_new_trainer)

		def new_trainer_okay():
			self.change_player(Trainer(self.ui_new_trainer_name.get()))
			self.player.monster = Monster.new_from_race("ogre")
			self.player.monster.name = "Red"
			self.base.change_state(FarmState)
		self.ui_new_trainer_okay = DirectGui.DirectButton(text="Okay",
														  text_fg=(1, 1, 1, 1),
														  text_shadow=(0, 0, 0, 1),
														  relief=None,
														  command=new_trainer_okay,
														  scale=0.1,
														  pos=(0, 0, -0.6),
														  )
		self.ui_new_trainer_okay.reparentTo(self.ui_new_trainer,)

		# Load Trainer
		self.ui_load_trainer = DirectGui.DirectFrame()
		self.ui_load_trainer.reparentTo(self.ui_base)
		self.ui_load_trainer.hide()

		def load_trainer(data):
			self.change_player(Trainer.deserialize(data))
			self.base.change_state(FarmState)
		i = 0
		for tid, data in self.trainer_saves.iteritems():
			btn = DirectGui.DirectButton(text=data['name'],
										 text_fg=(1,1,1,1),
										 text_shadow=(0, 0, 0,1),
										 scale=0.1,
										 frameColor=(0.7, 0.7, 0.7, 0.33),
										 pos=(0, 0, 0.8 - 0.2 * i),
										 command=load_trainer,
										 extraArgs=[data],
										 )
			btn.reparentTo(self.ui_load_trainer)
			i += 1


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

		self.background = OnscreenImage(parent=self.render2dp, image="art/menu_background.png")
		self.cam2dp.node().getDisplayRegion(0).setSort(-20)

		# Setup saves
		self.save_dir = os.path.join(appdirs.user_data_dir('ThorGame'), 'saves')
		if not os.path.exists(self.save_dir):
			os.makedirs(self.save_dir)
		self.saved_trainer_ids = [i.split('.')[0] for i in os.listdir(self.save_dir)]

		# Setup the player and the player's monster
		self.player = None
		#self.player = Trainer()
		#self.player.monster = Monster(name="Red", defense=25, speed=15)

		# Setup game states
		self.game_state = TitleState(self)
		self.taskMgr.add(self.main_loop, "MainLoop")

	def change_state(self, new_state):
		self.game_state.destroy()
		self.game_state = new_state(self)

	def main_loop(self, task):
		self.game_state.main_loop()
		return task.cont


app = Game()
app.run()