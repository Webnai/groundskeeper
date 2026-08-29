"""Groundskeeper: a grounding auditor for LLM fine-tuning datasets.

Verifies that generated training examples (e.g. from training_data_bot) are
actually supported by the source text they claim to come from, before you
spend compute fine-tuning on them. See README.md for the full problem
statement and CHANGELOG.md for how this was built and evaluated.
"""

__version__ = "0.1.0"
