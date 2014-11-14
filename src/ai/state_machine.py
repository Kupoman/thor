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

from .conditions import get_condition


class State:
	__slots__ = ["actions", "entry_actions", "exit_actions", "transitions"]

	def __init__(self, actions, entry_actions, exit_actions, transitions):
		self.actions = actions
		self.entry_actions = entry_actions
		self.exit_actions = exit_actions
		self.transitions = transitions


class Transition:
	__slots__ = ["condition", "state"]

	def __init__(self, condition, state):
		self.condition = condition
		self.state = state


class StateMachine:
	def __init__(self, agent, data=None):
		self.states = {}
		self.current_state = None
		self.agent = agent

		if data:
			self.load(data)

	def load(self, data):
		# Load states
		for state in data["states"]:
			actions = state["actions"]
			entry_actions = state["entry_actions"]
			exit_actions = state["exit_actions"]

			transitions = []
			for transition in state["transitions"]:
				condition = get_condition(transition[0])
				target_state = transition[1]
				transitions.append(Transition(condition, target_state))

			self.states[state["name"]] = State(actions, entry_actions,
					exit_actions, transitions)

			if not self.current_state:
				self.current_state = self.states[state["name"]]

		# Link transitions
		for state in self.states.values():
			for transition in state.transitions:
				transition.state = self.states[transition.state]
