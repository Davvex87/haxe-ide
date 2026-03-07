from functools import partial
from typing import Callable
from pathlib import Path
from textual.command import DiscoveryHit, Hit, Hits, Provider
from resources import resource_path


class ExampleProvider(Provider):

	def read_examples(self) -> list[str]:
		results = resource_path("examples").resolve().glob("*.json")
		return list((p.stem) for p in results)

	async def startup(self) -> None:
		worker = self.app.run_worker(self.read_examples, thread=True)
		self.example_paths = await worker.wait()

	async def discover(self) -> Hits:
		app = self.app
		
		for example in self.example_paths:
			yield DiscoveryHit(example, partial(app.loadExampleData, example))

	async def search(self, query: str) -> Hits:  
		matcher = self.matcher(query)  

		app = self.app

		for example in self.example_paths:
			command = example
			score = matcher.match(command)  
			if score > 0:
				yield Hit(
					score,
					matcher.highlight(command),  
					partial(app.loadExampleData, example),
					help="Open this example file",
				)