from panda3d.core import *


class CombatMonster(object):
	def __init__(self, monster):
		self.data = monster
		self.hp = self.data.hp
		self.stamina = 50
		self.model = base.loader.loadModel(self.data.visual)
		self.model.reparentTo(base.render)


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

	def update(self):
		for monster in self.monsters:
			monster.stamina += 1

	def destroy(self):
		for monster in self.monsters:
			monster.model.removeNode()