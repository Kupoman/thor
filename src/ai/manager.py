#   Copyright 2013 Daniel Stokes, Mitchell Stokes
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from .state_machine import StateMachine
from .agent import Agent


default_definition = """
{
	"states":
	[
		{
			"name": "wait",
			"entry_actions": [],
			"actions": [],
			"exit_actions": [],
			"transitions": [
				[["VALUE", "wants_to_cast", "0", "inf"], "use_tech"]
			]
		},
		{
			"name": "use_tech",
			"entry_actions": ["use_tech"],
			"actions": [],
			"exit_actions": [],
			"transitions": [
				[["ALWAYS"], "wait"]
			]
		}
	]
}
"""


class Manager:
	def __init__(self):
		self._agents = [None] * 32
		self._agent_count = 32
		self._action_set = {}
		self._actions = {}
		self._transitions = {}

		from . import actions
		for item in dir(actions):
			if not item.startswith("_"):
				self._action_set[item] = getattr(actions, item)

	def add_agent(self, data, definition=default_definition):
		if self._agent_count == len(self._agents):
			self._agents += [None] * len(self._agents)

		for handle, agent in enumerate(self._agents):
			if agent is None:
				break

		self._agents[handle] = Agent(data, definition)
		return handle

	def remove_agent(self, handle):
		self._agents[handle] = None

	def update(self):
		for agent in self._agents:
			if agent is None:
				continue

			sm = agent.state_machine
			actions = []
			for transition in sm.current_state.transitions:
				if transition.condition.test(agent.data):
					target_state = transition.state
					actions += sm.current_state.exit_actions
					actions += target_state.entry_actions
					sm.current_state = target_state
				else:
					actions = sm.current_state.actions

			for action in actions:
				self._action_set[action](agent.data)
