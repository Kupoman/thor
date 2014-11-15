import random


def use_tech(agent):
	targets = [t for t in agent.targets if t.hp > 0]
	if not targets:
		return

	techniques = [t for t in agent.data.techniques if t.cost < agent.stamina]
	if not techniques:
		return

	tech = random.choice(techniques)
	target = random.choice(targets)

	tech.use(agent, target)