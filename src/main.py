#!/usr/bin/env python

from __future__ import print_function
import sys
import math

import os
_file_dir = os.path.abspath(os.path.dirname(__file__))
os.environ['PANDA_PRC_DIR'] = os.path.join(_file_dir, 'etc')
os.chdir(_file_dir)

from cefpanda import CEFPanda

from direct.showbase.ShowBase import ShowBase, DirectObject
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui import DirectGui, DirectGuiGlobals

from panda3d.core import *

from monster import Monster
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader
import commands
import appdirs
import uuid
import json

from combat import CombatTeam, CombatWorld

class Trainer(object):
	@classmethod
	def deserialize(cls, json_dictionary):
		ret = cls()
		ret.weeks = json_dictionary['weeks']
		ret.name = json_dictionary['name']
		ret.uuid = json_dictionary['uuid']
		if 'monster' in json_dictionary:
			ret.monster = Monster.deserialize(json_dictionary['monster'])

		return ret

	def __init__(self, name="Trainer", dont_save=False):
		self.name = name
		self.monster = None
		self.weeks = 0
		self.uuid = str(uuid.uuid4())
		self.dont_save = dont_save
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
	def __init__(self, _base, ui=None):
		DirectObject.DirectObject.__init__(self)
		self.base = _base
		self.ui_base = DirectGui.DirectFrame(frameColor=(0, 0, 0, 0))
		self.player = _base.player
		self.quit = False

		if ui is not None:
			template = self.base.ui_env.get_template(ui + '.html')
			self.base.ui.load_string(template.render(), 'ui/' + ui + '.html')

			self.accept('arrow_up', self.base.ui.execute_js, ['navUp()'])
			self.accept('arrow_up-repeat', self.base.ui.execute_js, ['navUp()'])
			self.accept('arrow_down', self.base.ui.execute_js, ['navDown()'])
			self.accept('arrow_down-repeat', self.base.ui.execute_js, ['navDown()'])
			self.accept('k', self.base.ui.execute_js, ['navUp()'])
			self.accept('k-repeat', self.base.ui.execute_js, ['navUp()'])
			self.accept('j', self.base.ui.execute_js, ['navDown()'])
			self.accept('j-repeat', self.base.ui.execute_js, ['navDown()'])
			self.accept('enter', self.base.ui.execute_js, ['navEnter()'])
			self.accept('escape', self.do_escape)

			self.base.ui.execute_js("setupNav({})".format(json.dumps(self.nav.keys())), True)
			self.base.ui.set_js_function("do_nav", self.do_nav)
		else:
			self.base.ui.load(None)

	def do_escape(self):
		pass

	def do_nav(self, nav, item):
		if nav == 'main-menu':
			self.nav[item]()
			return True

		return False

	def update_ui(self):
		pass

	def main_loop(self):
		if self.quit:
			sys.exit()
		self.update_ui()

	def change_player(self, new_player):
		self.player = self.base.player = new_player

	def destroy(self):
		self.ignoreAll()
		self.ui_base.destroy()

		if not self.player.dont_save:
			with open(os.path.join(self.base.save_dir, self.player.uuid) + '.sav', 'w') as f:
				json.dump(self.player.serialize(), f)


class CombatState(GameState):
	def __init__(self, _base):
		GameState.__init__(self, _base)
		self.accept("enter", self.cb_next_turn)

		self.clock = ClockObject()

		g_race = "golem" if self.player.monster.race.lower() == "ogre" else "ogre"
		hpr_list = ((-90, 0, 0), (90, 0, 0))
		pos_list = ((-2, 2, 0), (2, 2, 0))
		monster_list = ((self.player.monster,)*3, (Monster.new_from_race(g_race),)*3)
		# self.teams = [CombatTeam(monster_list[i], pos_list[i], hpr_list[i]) for i in range(2)]
		self.combat_world = CombatWorld()
		self.combat_world.add_team(monster_list[0], pos_list[0], hpr_list[0])
		self.combat_world.add_team(monster_list[1], pos_list[1], hpr_list[1])
		self.teams = self.combat_world.teams

		self.teams[0].set_targets(self.teams[1])
		self.teams[1].set_targets(self.teams[0])

		# Combatants
		self.combatants = {}
		self.combatants['red'] = self.player.monster
		self.combatants['red'].current_stamina = 50
		self.combatants['red'].current_hp = self.combatants['red'].hp
		g_race = "golem" if self.player.monster.race.lower() == "ogre" else "ogre"
		self.combatants['green'] = Monster.new_from_race(g_race)
		self.combatants['green'].current_hp = self.combatants['green'].hp
		self.combatants['green'].current_stamina = 50

		self.combatants['red'].target = self.combatants['green']
		self.combatants['green'].target = self.combatants['red']

		# Combat vars
		self.combat_time = 60.0
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
		for team in self.teams:
			team.destroy()

	def cb_next_turn(self):
		self.player_command = commands.Wait

	def setup_ui(self):
		# Combat clock
		self.ui_turn = DirectGui.DirectLabel(text=str(self.turn),
											 text_fg=(1, 1, 1, 1),
											 text_shadow=(0, 0, 0, 1),
											 frameColor=(0, 0, 0, 0),
											 scale=0.2,
											 pos=(0, 0, 0.8))
		self.ui_turn.reparentTo(self.ui_base)


		# Player team UI
		self.ui_player_healths = []
		self.ui_player_staminas = []
		for i, monster in enumerate(self.teams[0].monsters):
			_range = value = monster.hp
			ui_health = DirectGui.DirectWaitBar(range=_range,
															value=value,
															barColor=(0, 1, 0, 1),
															scale=(0.3, 1, 0.1),
															pos=(-0.6 - i*0.2, 0, 0.45 - i*0.05))
			ui_health.reparentTo(self.ui_base)
			self.ui_player_healths.append(ui_health)

			value = monster.stamina
			ui_stamina = DirectGui.DirectWaitBar(range=100,
															 value=value,
															 barColor=(0, 0, 1, 1),
															 scale=(0.3, 1, 0.05),
															 pos=(-0.6 - i*0.2, 0, 0.44 - i*0.05))
			ui_stamina.reparentTo(self.ui_base)
			self.ui_player_staminas.append(ui_stamina)

		# Enemy team UI
		self.ui_enemy_healths = []
		self.ui_enemy_staminas = []
		for i, monster in enumerate(self.teams[1].monsters):
			_range = value = monster.hp
			ui_health = DirectGui.DirectWaitBar(range=_range,
															value=value,
															barColor=(0, 1, 0, 1),
															scale=(0.3, 1, 0.1),
															pos=(0.6 + i*0.2, 0, 0.45 - i*0.05))
			ui_health.reparentTo(self.ui_base)
			self.ui_enemy_healths.append(ui_health)

			value = monster.stamina
			ui_stamina = DirectGui.DirectWaitBar(range=100,
															 value=value,
															 barColor=(0, 0, 1, 1),
															 scale=(0.3, 1, 0.05),
															 pos=(0.6 + i*0.2, 0, 0.44 - i*0.05))
			ui_stamina.reparentTo(self.ui_base)
			self.ui_enemy_staminas.append(ui_stamina)

		# Command list
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

	def update_ui(self):
		self.ui_turn['text'] = str(self.turn)
		for i, ui_health, ui_stamina in [(i, self.ui_player_healths[i], self.ui_player_staminas[i]) for i in range(len(self.ui_player_healths))]:
			monster = self.teams[0].monsters[i]
			ui_health['value'] = monster.hp
			ui_stamina['value'] = monster.stamina
		for i, ui_health, ui_stamina in [(i, self.ui_enemy_healths[i], self.ui_enemy_staminas[i]) for i in range(len(self.ui_player_healths))]:
			monster = self.teams[1].monsters[i]
			ui_health['value'] = monster.hp
			ui_stamina['value'] = monster.stamina

	def main_loop(self):
		GameState.main_loop(self)

		# Not sure what the behavior is on ClockObject.getDt when there are not
		# two ticks to compare. Making sure to initialize the clock just in case
		if self.clock.getFrameCount() == 0:
			self.clock.tick()
			return

		# Time's up!
		# Resolve combat
		if self.turn <= 0:
			winner = self.teams[0]
			winning_percent = winner.get_percent_hp()
			for team in self.teams[1:]:
				percent = team.get_percent_hp()
				if percent > winning_percent:
					winning_percent = percent
					winner = team

			print("%s win with %.2f%% hp remaining!" %
				(str([monster.data.name for monster in team.monsters]),
				winning_percent))
			self.player.weeks += 1
			self.base.change_state(FarmState)

		self.clock.tick()
		dt = self.clock.getDt()

		self.combat_time -= dt
		self.turn = int(math.ceil(self.combat_time))

		self.combat_world.update(dt)
		for team in self.teams:
			team.update(dt)

		if self.player_command:
			if self.player.monster.initiative > self.combatants['green']:
				self.player_command.run(self.player.monster)
				commands.Attack.run(self.combatants['green'])
			else:
				commands.Attack.run(self.combatants['green'])
				self.player_command.run(self.player.monster)
			# self.turn -= 1
			self.combatants['red'].current_stamina += self.combatants['red'].recovery
			self.combatants['green'].current_stamina += self.combatants['green'].recovery
			self.player_command = None

		if self.combatants['red'].current_hp <= 0 or \
			self.combatants['green'].current_hp <= 0:
			self.player.weeks += 1
			self.base.change_state(FarmState)


class FarmState(GameState):
	def __init__(self, _base):
		self.nav = OrderedDict([
			('Combat', self.do_combat),
			('Training', self.do_training_menu),
			('Rest', self.do_rest),
			('Monster Info', self.do_monster_stats),
			('Quit', self.do_exit),
		])

		GameState.__init__(self, _base, 'farm')

		self.training_options = [
			'Attack',
			'Defense',
			'Intelligence',
			'Stamina',
			'Speed',
			'Back',
		]

		self.base.background.setImage("art/menu_background.png")
		self.base.ui.execute_js('setWeeks({})'.format(self.player.weeks), onload=True)

		if self.player.monster is None:
			self.base.ui.execute_js('switchToTab("{}")'.format('market'), onload=True)
			self.base.ui.execute_js('setupNav({})'.format(json.dumps([i['race'] for i in self.base.monster_data])), onload=True)
			self.in_market = True
		else:
			self.in_market = False
			self.advance_weeks(0)

		def set_monster(race):
			self.player.monster = Monster.new_from_race(race)
			self.load_monster_mesh()
		self.base.ui.set_js_function("set_monster", set_monster)

		if self.player.monster:
			self.load_monster_mesh()
		else:
			self.monster_mesh = None

	def destroy(self):
		GameState.destroy(self)
		if self.monster_mesh:
			self.monster_mesh.removeNode()

	def load_monster_mesh(self):
		self.monster_mesh = self.base.loader.loadModel(self.player.monster.visual)
		self.monster_mesh.reparentTo(self.base.render)
		self.monster_mesh.setH(180)

	def do_escape(self):
		if not self.in_market:
			self.base.ui.execute_js('switchToTab("{}")'.format('main-menu'))

	def do_nav(self, nav, item):
		if not GameState.do_nav(self, nav, item):
			if nav == 'training-menu':
				self.do_training(item.lower())
			elif nav == 'training-results':
				self.do_escape()
				self.advance_weeks()
			elif nav == 'monster-info':
				if item == 'Cancel':
					self.base.ui.execute_js('switchToTab("{}")'.format('market'), onload=True)
					self.base.ui.execute_js('setupNav({})'.format(json.dumps([i['race'] for i in self.base.monster_data])), onload=True)
					self.temp_monster = None
				elif item == 'Buy':
					self.base.ui.execute_js('setMonster()')
					self.in_market = False
					self.do_escape()
				else:
					self.do_escape()
			elif nav == 'market':
				self.base.ui.execute_js('switchToTab("{}")'.format('monster-info'))
				self.base.ui.execute_js('setupNav({})'.format(['Buy', 'Cancel']))
				monster = [i for i in self.base.monster_data if i['race'] == item][0]
				self.base.ui.execute_js('setMonsterInfo({})'.format(json.dumps(monster)))
			else:
				print("Unknown", nav, item)

	def do_combat(self):
		self.base.change_state(CombatState)

	def do_training_menu(self):
		self.base.ui.execute_js('switchToTab("{}")'.format('training-menu'))
		self.base.ui.execute_js('setupNav({})'.format(self.training_options))

	def do_rest(self):
		self.player.monster.fatigue -= 60
		self.advance_weeks()

	def do_training(self, stat):
		stat = stat.lower()
		if stat == 'back':
			self.do_escape()
		else:
			prev_stat = getattr(self.player.monster, stat)
			setattr(self.player.monster, stat, prev_stat + 1)
			self.player.monster.fatigue += 20
			result_str = "Raising stat {} from {} to {}.".format(stat.title(), prev_stat, getattr(self.player.monster, stat))
			print(result_str)
			self.base.ui.execute_js('switchToTab("{}")'.format('training-results'))
			self.base.ui.execute_js('setupNav({})'.format(['Okay']))
			self.base.ui.execute_js('setTrainingResults("{}")'.format(result_str))

	def do_monster_stats(self):
		self.base.ui.execute_js('switchToTab("{}")'.format('monster-info'))
		self.base.ui.execute_js('setupNav({})'.format(['Okay']))
		self.base.ui.execute_js('setMonsterInfo({})'.format(json.dumps(self.player.monster.serialize())))

	def do_exit(self):
		self.base.change_state(TitleState)

	def advance_weeks(self, weeks=1):
		self.player.weeks += weeks
		self.player.monster.age += weeks
		self.base.ui.execute_js('setWeeks({})'.format(self.player.weeks), onload=True)

		# Fatigue message
		monster = self.player.monster
		if monster.fatigue < 0:
			monster.fatigue = 0
		elif monster.fatigue > 100:
			monster.fatigue = 100

		msg = ""
		if monster.fatigue < 20:
			msg = "Monster is very well"
		elif monster.fatigue < 40:
			msg = "Monster is well"
		elif monster.fatigue < 60:
			msg = "Monster seems well"
		elif monster.fatigue < 80:
			msg = "Monster is tired"
		else:
			msg = "Monster is very tired"

		self.base.ui.execute_js('addMessageToQueue("{}")'.format(msg), onload=True)
		self.base.ui.execute_js('displayMessages()', onload=True)

	def main_loop(self):
		GameState.main_loop(self)

		if self.player.monster and self.player.monster.age >= self.player.monster.life_span:
			print("Your monster is dead, lets get a new one.")
			self.player.monster = None
			self.base.change_state(FarmState)


class TitleState(GameState):
	def __init__(self, _base):
		self.nav = OrderedDict([
			('New Trainer', self.do_new),
			('Load Trainer', self.do_load),
			('Exit Game', self.do_exit),
		])

		GameState.__init__(self, _base, 'title')

		self.trainer_saves = {}
		for sav in os.listdir(self.base.save_dir):
			with open(os.path.join(self.base.save_dir, sav)) as f:
				data = json.load(f)
				self.trainer_saves[data['uuid']] = data

		self.setup_ui()

	def setup_ui(self):
		def new_trainer(name):
			self.change_player(Trainer(name))
			#self.player.monster = Monster.new_from_race("ogre")
			#self.player.monster.name = "Red"
			self.base.change_state(FarmState)
		self.base.ui.set_js_function("new_trainer", new_trainer)

		def load_trainer(trainer_uuid):
			self.change_player(Trainer.deserialize(self.trainer_saves[trainer_uuid]))
			self.base.change_state(FarmState)
		self.base.ui.set_js_function("load_trainer", load_trainer)

	def do_escape(self):
		self.base.ui.execute_js('switchToTab("{}")'.format('main-menu'))

	def do_nav(self, nav, item):
		if not GameState.do_nav(self, nav, item):
			if nav == 'load-trainer':
				self.base.ui.execute_js('loadTrainer()')
			else:
				print("Unknown", nav, item)

	def do_new(self):
		self.base.ui.execute_js('switchToTab("{}")'.format('new-trainer'))

	def do_load(self):
		self.base.ui.execute_js('setupSaves({})'.format(json.dumps(self.trainer_saves.values())))
		self.base.ui.execute_js('switchToTab("{}")'.format('load-trainer'))

	def do_exit(self):
		self.quit = True


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		# Increase the texture resolution on DirectGui
		default_font = DirectGuiGlobals.getDefaultFont()
		default_font.clear()
		default_font.setPixelsPerUnit(64)
		DirectGuiGlobals.setDefaultFont(default_font)

		self.accept("f1", sys.exit)
		self.win.setCloseRequestEvent("f1")

		self.background = OnscreenImage(parent=self.render2dp, image="art/menu_background.png")
		self.cam2dp.node().getDisplayRegion(0).setSort(-20)

		# Setup camera
		self.disableMouse()
		self.camera.setPos(0, -5, 2.25)
		self.camera.setHpr(0, -10, 0)
		self.camLens.setFov(65)

		# Setup saves
		self.save_dir = os.path.join(appdirs.user_data_dir('ThorGame', roaming=True), 'saves')
		if not os.path.exists(self.save_dir):
			os.makedirs(self.save_dir)
		self.saved_trainer_ids = [i.split('.')[0] for i in os.listdir(self.save_dir)]

		# Setup UI
		self.ui = CEFPanda()
		src_dir = _file_dir
		template_folder = os.path.join(src_dir, 'ui')
		self.ui_env = Environment(loader=FileSystemLoader(template_folder),
								  trim_blocks=True)
		# HACK - CEFPython requires a regular LoadURL before LoadString works,
		# so we just give it something to work on. This doesn't render nicely,
		# but we replace it immediately with the UI for the first GameState.
		# CEFPython issue: https://code.google.com/p/chromiumembedded/issues/detail?id=763
		self.ui.load('ui/base.html')

		# Load monster data
		data_folder = os.path.join(src_dir, 'data')
		self.monster_data = []
		for i in os.listdir(data_folder):
			if i.startswith('race'):
				with open(os.path.join(data_folder, i)) as f:
					self.monster_data.append(json.load(f))

		# Setup the default player and monster
		self.player = Trainer(dont_save=True)
		self.player.monster = Monster.new_from_race("ogre")

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
