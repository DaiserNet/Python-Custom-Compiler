from app.core.lexer import LexicalAnalyzer


class CompilerEngine:
	"""Core entrypoint for compiler stages.

	For now this class exposes lexical analysis used by the editor.
	"""

	def __init__(self):
		self.lexer = LexicalAnalyzer()

	def analyze_lexically(self, source_code: str):
		return self.lexer.analyze(source_code)

	def tokenize(self, source_code: str):
		return self.lexer.tokenize(source_code)
