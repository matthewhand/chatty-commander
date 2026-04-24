# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHER DEALS INCIENTS,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""Agent Fleet Launcher.

Provides CLI and API interfaces for launching and managing agent fleets.
Supports launching from blueprints, CLI commands, and programmatic usage.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from typing import Any

from chatty_commander.ai.agents.fleet import (
    AgentFleet,
    AgentFleetConfig,
    AgentInstance,
)

logger = logging.getLogger(__name__)


@dataclass
class LaunchConfig:
    """Configuration for launching a fleet of agents."""

    # Fleet settings
    fleet_name: str = "default"
    max_agents: int = 10
    max_concurrent_tasks: int = 5

    # Default agent settings
    default_model: str = "gpt-4"
    default_temperature: float = 0.7

    # Agent blueprints to launch (by ID or path)
    blueprints: list[str] = field(default_factory=list)
    blueprints_path: str | None = None

    # Team composition
    researcher_count: int = 0
    analyst_count: int = 0
    coder_count: int = 0
    writer_count: int = 0
    general_count: int = 0

    # Capability requirements
    required_capabilities: list[str] = field(default_factory=list)

    # Liveness
    auto_start: bool = True
    persistence_dir: str = "~/.chatty_commander/fleet"


def create_fleet_from_config(config: LaunchConfig) -> tuple[AgentFleet, list[AgentInstance]]:
    """Create and launch an agent fleet from configuration.

    Args:
        config: Launch configuration

    Returns:
        Tuple of (fleet, launched_agents)
    """
    fleet_config = AgentFleetConfig(
        default_model=config.default_model,
        default_temperature=config.default_temperature,
        max_agents=config.max_agents,
        max_concurrent_tasks=config.max_concurrent_tasks,
        persistence_dir=config.persistence_dir,
    )

    # Set up capability distribution based on team roles
    fleet_config.capability_distribution = {
        "researcher": ["search", "analyze", "summarize", "fact_check"],
        "analyst": ["analyze", "interpret", "compare", "evaluate"],
        "coder": ["write_code", "debug", "refactor", "test"],
        "writer": ["write", "edit", "proofread", "format"],
        "general": ["converse", "answer", "explain"],
    }

    # Add custom capabilities
    for cap in config.required_capabilities:
        fleet_config.capability_distribution.setdefault("general", []).append(cap)

    fleet = AgentFleet(config=fleet_config)

    return fleet, []


def launch_preset_fleet(
    preset: str = "balanced",
    count: int = 3,
    **kwargs: Any,
) -> tuple[AgentFleet, list[AgentInstance]]:
    """Launch a preset fleet configuration.

    Args:
        preset: Fleet preset name ("balanced", "research", "development", "writing")
        count: Number of agents per role in the preset
        **kwargs: Additional launch configuration

    Returns:
        Tuple of (fleet, launched_agents)
    """
    configs: dict[str, LaunchConfig] = {
        "balanced": LaunchConfig(
            fleet_name="balanced",
            researcher_count=count,
            analyst_count=count,
            coder_count=count,
        ),
        "research": LaunchConfig(
            fleet_name="research",
            researcher_count=count * 2,
            analyst_count=count,
        ),
        "development": LaunchConfig(
            fleet_name="development",
            coder_count=count * 2,
            analyst_count=count,
        ),
        "writing": LaunchConfig(
            fleet_name="writing",
            writer_count=count * 2,
            researcher_count=count,
        ),
    }

    config = configs.get(preset, configs["balanced"])
    for key, value in kwargs.items():
        setattr(config, key, value)

    fleet, agents = create_fleet_from_config(config)
    return fleet, agents


async def launch_fleet_async(
    config: LaunchConfig | None = None,
    preset: str | None = None,
    from_blueprints: bool = False,
    blueprint_ids: list[str] | None = None,
) -> tuple[AgentFleet, list[AgentInstance]]:
    """Launch a fleet of agents asynchronously.

    Args:
        config: Explicit launch configuration, or None
        preset: Preset fleet name, or None
        from_blueprints: Whether to load from stored blueprints
        blueprint_ids: Specific blueprint IDs to launch, or None for all

    Returns:
        Tuple of (fleet, launched_agents)
    """
    if config and preset:
        raise ValueError("Cannot specify both config and preset")

    if preset:
        fleet, agents = launch_preset_fleet(preset)
    elif config:
        fleet, agents = create_fleet_from_config(config)
    else:
        config = LaunchConfig()
        fleet, agents = create_fleet_from_config(config)

    await fleet.start()

    if from_blueprints:
        launched = await fleet.launch_agents_from_blueprints(
            blueprints_path=config.blueprints_path,
            blueprint_ids=blueprint_ids,
        )
        agents.extend(launched)

    # Launch agents based on presets
    if preset or config:
        cfg = config or launch_preset_fleet(preset)[0].config
        roles_and_counts = [
            ("researcher", cfg.researcher_count),
            ("analyst", cfg.analyst_count),
            ("coder", cfg.coder_count),
            ("writer", cfg.writer_count),
            ("general", cfg.general_count),
        ]

        for role, count in roles_and_counts:
            for _ in range(max(0, count)):
                agent = fleet.launch_agent(
                    name=f"{role.title()}-{len([a for a in fleet.agents.values() if a.team_role == role]) + 1}",
                    persona_id=f"{role}-{len([a for a in fleet.agents.values() if a.team_role == role]) + 1}",
                    team_role=role,
                    model=cfg.default_model,
                    temperature=cfg.default_temperature,
                )
                agents.append(agent)

    return fleet, agents


def launch_fleet(
    config: LaunchConfig | None = None,
    preset: str | None = None,
    from_blueprints: bool = False,
    blueprint_ids: list[str] | None = None,
    blocking: bool = True,
) -> tuple[AgentFleet, list[AgentInstance]]:
    """Launch a fleet of agents synchronously.

    Args:
        config: Explicit launch configuration, or None
        preset: Preset fleet name, or None
        from_blueprints: Whether to load from stored blueprints
        blueprint_ids: Specific blueprint IDs to launch, or None for all
        blocking: Whether to block until fleet is stopped

    Returns:
        Tuple of (fleet, launched_agents)
    """
    async def _main():
        return await launch_fleet_async(
            config=config,
            preset=preset,
            from_blueprints=from_blueprints,
            blueprint_ids=blueprint_ids,
        )

    fleet, agents = asyncio.run(_main())

    if blocking:
        try:
            asyncio.run(fleet.stop(graceful=True))
        except RuntimeError:
            # Event loop already closed
            pass

    return fleet, agents


# CLI Interface

def create_cli_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for fleet operations."""
    parser = argparse.ArgumentParser(
        description="ChattyCommander Agent Fleet Manager - Launch and manage AI agent fleets"
    )

    subparsers = parser.add_subparsers(dest="command", title="Commands")

    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch a fleet of agents")
    launch_parser.add_argument(
        "--preset",
        choices=["balanced", "research", "development", "writing"],
        help="Preset fleet configuration",
    )
    launch_parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of agents per role (default: 3)",
    )
    launch_parser.add_argument(
        "--from-blueprints",
        action="store_true",
        help="Launch from stored agent blueprints",
    )
    launch_parser.add_argument(
        "--blueprint-ids",
        nargs="+",
        help="Specific blueprint IDs to launch",
    )
    launch_parser.add_argument(
        "--max-agents",
        type=int,
        help="Maximum number of agents",
    )
    launch_parser.add_argument(
        "--model",
        default="gpt-4",
        help="Default LLM model (default: gpt-4)",
    )
    launch_parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Default sampling temperature (default: 0.7)",
    )
    launch_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # List command
    subparsers.add_parser("list", help="List active fleets and agents")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a fleet or agent")
    stop_parser.add_argument(
        "--fleet-name",
        help="Name of the fleet to stop",
    )
    stop_parser.add_argument(
        "--agent-id",
        help="ID of a specific agent to stop",
    )
    stop_parser.add_argument(
        "--all",
        action="store_true",
        help="Stop all fleets and agents",
    )

    # Status command
    subparsers.add_parser("status", help="Show fleet status")

    # Assign command
    assign_parser = subparsers.add_parser("assign", help="Assign a task to an agent")
    assign_parser.add_argument(
        "--fleet-name",
        required=True,
        help="Name of the fleet",
    )
    assign_parser.add_argument(
        "--task",
        required=True,
        help="Task description or prompt",
    )
    assign_parser.add_argument(
        "--agent-id",
        help="Specific agent ID to assign to",
    )
    assign_parser.add_argument(
        "--role",
        help="Assign to agent with this role",
    )
    assign_parser.add_argument(
        "--capability",
        help="Assign to agent with this capability",
    )

    return parser


def run_cli() -> int:
    """Run the fleet manager CLI.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_cli_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    try:
        if args.command == "launch":
            config = LaunchConfig(
                preset=args.preset,
                count=args.count,
                model=args.model,
                temperature=args.temperature,
                max_agents=args.max_agents,
            )
            fleet, agents = launch_fleet(
                config=config if not args.preset else None,
                preset=args.preset,
                from_blueprints=args.from_blueprints,
                blueprint_ids=args.blueprint_ids,
                blocking=False,
            )
            print(f"✅ Launched fleet with {len(agents)} agents:")
            for agent in agents:
                print(f"  - {agent.name} ({agent.agent_id[:8]}) [{agent.team_role}]")
            print(f"\nFleet stats: {json.dumps(fleet.get_fleet_stats(), indent=2)}")

        elif args.command == "list":
            # In a real implementation, we'd track active fleets
            print("List command: Not yet implemented (requires fleet registry)")
            return 1

        elif args.command == "stop":
            print("Stop command: Not yet implemented (requires fleet registry)")
            return 1

        elif args.command == "status":
            print("Status command: Not yet implemented (requires fleet registry)")
            return 1

        elif args.command == "assign":
            print("Assign command: Not yet implemented (requires active fleet)")
            return 1

        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error("Error: %s", e, exc_info=True)
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    return 0


def main() -> int:
    """Entry point for fleet manager CLI."""
    return run_cli()


if __name__ == "__main__":
    sys.exit(main())
