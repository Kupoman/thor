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


import json
import os

from .state_machine import StateMachine


class Agent:
	def __init__(self, data=None, definition=None):
		self.data = data
		self.actions = []
		self.state_machine = None

		if definition:
			self.load_definition(definition)

	def load_definition(self, definition):
		if os.access(definition, os.F_OK):
			with open(definition, 'r') as f:
					dict = json.load(f)
		else:
			dict = json.loads(definition)

		self.state_machine = StateMachine(self.data, dict)
