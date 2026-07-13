"""COSIGNA MCP connector — drive async signature ceremonies from a Claude agent.  # mcp D1

Server-blind by design: the document never leaves the user's machine (only its SHA-256
hash travels), and the connector holds only the local session token + per-ceremony
capability tokens. See README.md for the honest-limits and capability-link disclosures.
"""
__version__ = "0.1.0"
