import random


def use_tech(agent):
	if not agent.targets:
		return

	techniques = [t for t in agent.data.techniques if t.cost < agent.stamina]

	if not techniques:
		return

	tech = random.choice(techniques)
	target = random.choice(agent.targets)

	tech.use(agent, target)