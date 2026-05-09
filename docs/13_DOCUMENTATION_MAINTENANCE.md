# Documentation Maintenance

## Rule For Future Codex Sessions

For every future Codex session:

1. Update relevant docs when code/config/launch/URDF/script behavior changes.
2. Update `docs/11_CHANGELOG.md` for meaningful changes.
3. Update `docs/12_CURRENT_STATUS.md` after tests.
4. Update `docs/10_DECISIONS_LOG.md` when a design decision changes.
5. If a new topic appears, create a new `docs/*.md` file and add it to `docs/README.md`.
6. Separate confirmed facts from assumptions and future plans.
7. Do not document unverified claims as facts.
8. Mark outdated legacy behavior clearly.

## What Counts As A Meaningful Change

Update docs when any of these change:

- Docker image/container behavior,
- helper commands,
- launch files,
- URDF/SRDF/transmissions/controllers,
- MoveIt controller mapping,
- camera topics or frames,
- color pointing behavior,
- box geometry or scene layout,
- setup script behavior,
- testing results,
- safety assumptions.

## Where To Update

| Change type | Update files |
| --- | --- |
| Environment/setup | `01_LIGHTNING_DOCKER_ENVIRONMENT.md`, `03_SETUP_HISTORY_AND_TROUBLESHOOTING.md`, `12_CURRENT_STATUS.md` |
| Original repo architecture | `02_ORIGINAL_CR5_REPO_ARCHITECTURE.md`, `12_CURRENT_STATUS.md` |
| Gazebo control | `04_GAZEBO_CONTROL_FIX.md`, `11_CHANGELOG.md`, `12_CURRENT_STATUS.md` |
| Camera/perception | `05_WRIST_CAMERA_AND_PERCEPTION.md`, `11_CHANGELOG.md`, `12_CURRENT_STATUS.md` |
| Color pointing package | `06_COLOR_POINTING_PACKAGE.md`, `07_OPERATION_GUIDE.md`, `11_CHANGELOG.md`, `12_CURRENT_STATUS.md` |
| Sim-to-real plans | `08_SIM_TO_REAL_TRANSFER_PLAN.md`, `10_DECISIONS_LOG.md` |
| New topic | new `docs/*.md`, plus `docs/README.md` |

## Fact Labels

Use clear labels:

| Label | Meaning |
| --- | --- |
| Confirmed | Directly inspected or tested in the current session |
| Reported | Known from project history or prior session output |
| Expected | Intended behavior based on config/scripts |
| Needs verification | Not yet tested in the current state |
| Future work | Planned or optional, not implemented |

## Avoid Stale Docs

If a behavior changes, do not leave old instructions appearing current.

Use a clear note such as:

```text
Legacy note: this was true before the Gazebo ROS control fix. Re-test before using.
```

## Documentation-Only Changes

Documentation-only changes do not require a catkin rebuild.

Still verify file existence:

```bash
find /teamspace/studios/this_studio/docs -maxdepth 1 -type f -name '*.md' | sort
```

