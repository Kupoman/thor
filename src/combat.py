import random

from panda3d.core import *
from ai.manager import Manager as AIManager


class CombatMonster(object):
	def __init__(self, monster):
		self.data = monster
		self.hp = self.data.hp
		self.stamina = 50
		self.model = base.loader.loadModel(self.data.visual)
		self.model.reparentTo(base.render)
		self.targets = []
		self.ai_handle = -1

	@property
	def wants_to_cast(self):
		if random.random() < self.stamina/5000.0:
			return 1
		return 0


class CombatTeam(object):
	def __init__(self, monsters, start_pos, start_hpr):
		self.monsters = [CombatMonster(monster) for monster in monsters]

		offsets = [
			Vec3(0, -2, 0),
			Vec3(0, 0, 0),
			Vec3(0, 2, 0),
		]
		for i, monster in enumerate(self.monsters):
			monster.model.setHpr(start_hpr)
			monster.model.setPos(Vec3(start_pos) + offsets[i])

	def set_targets(self, target_team):
		for monster in self.monsters:
			monster.targets = target_team.monsters

	def get_percent_hp(self):
		max = 0.0
		cur = 0.0
		for monster in self.monsters:
			max += monster.data.hp
			cur += monster.hp

		return cur/max * 100

	def update(self, dt):
		for monster in self.monsters:
			if monster.hp <= 0:
				if monster.model:
					monster.model.removeNode()
					monster.model = None
				continue
			monster.stamina += monster.data.recovery * dt

	def destroy(self):
		for monster in self.monsters:
			monster.model.removeNode()


class CombatWorld(object):
	def __init__(self):
		self.teams = []
		self.ai_manager = AIManager()

	def add_team(self, roster, start_pos, start_hpr):
		team = CombatTeam(roster, start_pos, start_hpr)
		self.teams.append(team)
		for monster in team.monsters:
			monster.ai_handle = self.ai_manager.add_agent(monster)

	def update(self, dt):
		for team in self.teams:
			for monster in team.monsters:
				if monster.hp <= 0:
					if monster.ai_handle != -1:
						self.ai_manager.remove_agent(monster.ai_handle)
					monster.ai_handle = -1
			team.update(dt)

		self.ai_manager.update()
