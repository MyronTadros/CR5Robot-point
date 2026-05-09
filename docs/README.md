# CR5 Project Documentation Index

This folder contains topic-based documentation for the Dobot CR5 ROS Melodic project running on Lightning AI.

Read these documents before changing setup, launch, URDF, controller, perception, or demo behavior.

## Numbered Topic Docs

| File | Topic |
| --- | --- |
| [00_PROJECT_OVERVIEW.md](00_PROJECT_OVERVIEW.md) | Project identity, goals, constraints, confirmed/reported status |
| [01_LIGHTNING_DOCKER_ENVIRONMENT.md](01_LIGHTNING_DOCKER_ENVIRONMENT.md) | Lightning AI, Docker, TurboVNC/noVNC, helper commands, ports |
| [02_ORIGINAL_CR5_REPO_ARCHITECTURE.md](02_ORIGINAL_CR5_REPO_ARCHITECTURE.md) | Original `CR5_ROS` package layout and launch architecture |
| [03_SETUP_HISTORY_AND_TROUBLESHOOTING.md](03_SETUP_HISTORY_AND_TROUBLESHOOTING.md) | Setup problems, fixes, warnings, troubleshooting checks |
| [04_GAZEBO_CONTROL_FIX.md](04_GAZEBO_CONTROL_FIX.md) | Gravity-on Gazebo ROS control fix and validation |
| [05_WRIST_CAMERA_AND_PERCEPTION.md](05_WRIST_CAMERA_AND_PERCEPTION.md) | Wrist RGB-D camera, topics, HSV/depth perception plan |
| [06_COLOR_POINTING_PACKAGE.md](06_COLOR_POINTING_PACKAGE.md) | `cr5_color_pointing` package design, files, launch flow, caveats |
| [07_OPERATION_GUIDE.md](07_OPERATION_GUIDE.md) | Day-to-day commands for RViz, MoveIt, Gazebo, camera, boxes |
| [08_SIM_TO_REAL_TRANSFER_PLAN.md](08_SIM_TO_REAL_TRANSFER_PLAN.md) | Simulation-to-real assumptions and transfer checklist |
| [09_FUTURE_WORK_AND_ROADMAP.md](09_FUTURE_WORK_AND_ROADMAP.md) | Remaining milestones and future project directions |
| [10_DECISIONS_LOG.md](10_DECISIONS_LOG.md) | Design decision record |
| [11_CHANGELOG.md](11_CHANGELOG.md) | Meaningful changes by date/session |
| [12_CURRENT_STATUS.md](12_CURRENT_STATUS.md) | Current confirmed, reported, and needs-verification status |
| [13_DOCUMENTATION_MAINTENANCE.md](13_DOCUMENTATION_MAINTENANCE.md) | Documentation rules for future Codex sessions |
| [14_NEXT_AGENT_TODO.md](14_NEXT_AGENT_TODO.md) | Handoff TODO for the next agent: achieved state, current blocker, exact next steps |

## Legacy Docs

These earlier docs are still useful and may overlap with the numbered set:

| File | Topic |
| --- | --- |
| [CR5_LIGHTNING_WORKFLOW.md](CR5_LIGHTNING_WORKFLOW.md) | Earlier Lightning runbook |
| [CR5_VERIFICATION_CHECKLIST.md](CR5_VERIFICATION_CHECKLIST.md) | Earlier setup verification checklist |
| [CR5_CAMERA.md](CR5_CAMERA.md) | Earlier wrist camera notes |
| [CR5_TROUBLESHOOTING.md](CR5_TROUBLESHOOTING.md) | Earlier troubleshooting notes |
| [CR5_MAINTENANCE.md](CR5_MAINTENANCE.md) | Earlier maintenance and safety notes |

If behavior changes, update the numbered docs first, then refresh the legacy docs if they would otherwise become misleading.
