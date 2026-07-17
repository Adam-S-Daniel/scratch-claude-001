# E1 Fallback Probe — SessionStart Hook Test

## (1) git log --oneline -1

```
7958110 Merge pull request #11 from Adam-S-Daniel/e1-hook-fallback
```

## (2) cat /tmp/e1-hook.log

The SessionStart hook DID run — the log file is present. Its contents show the
hook performed a plugin-marketplace add + plugin install:

```
Adding marketplace…Cloning via HTTPS: https://github.com/Adam-S-Daniel/agentskills.git
Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): https://github.com/Adam-S-Daniel/agentskills.git
Clone complete, validating marketplace…
Cleaning up old marketplace cache…
√ Successfully added marketplace: agentskills (declared in user settings)
Installing plugin "pin-actions-to-sha@agentskills"...√ Successfully installed plugin: pin-actions-to-sha@agentskills (scope: user)
```

## (3) e1-hook line visible in session context from hook stdout

Present. The following system line was injected into my session context:

```
SessionStart:startup hook success: e1-hook: ran (exit 0); log at /tmp/e1-hook.log
```

## (4) ~/.claude/plugins/ state

### ls -la ~/.claude/plugins/

```
total 28
drwxr-xr-x 4 root root 4096 Jul 17 00:00 .
drwxr-xr-x 9 root root 4096 Jul 17 00:00 ..
-rw-r--r-- 1 root root   24 Jul 17 00:00 .last_inuse_sweep
drwxr-xr-x 3 root root 4096 Jul 17 00:00 cache
-rw-r--r-- 1 root root  427 Jul 17 00:00 installed_plugins.json
-rw-r--r-- 1 root root  236 Jul 17 00:00 known_marketplaces.json
drwxr-xr-x 3 root root 4096 Jul 17 00:00 marketplaces
```

### cat ~/.claude/plugins/known_marketplaces.json

```json
{
  "agentskills": {
    "source": {
      "source": "github",
      "repo": "Adam-S-Daniel/agentskills"
    },
    "installLocation": "/root/.claude/plugins/marketplaces/agentskills",
    "lastUpdated": "2026-07-17T00:00:37.739Z"
  }
}
```

### cat ~/.claude/plugins/installed_plugins.json

```json
{
  "version": 2,
  "plugins": {
    "pin-actions-to-sha@agentskills": [
      {
        "scope": "user",
        "installPath": "/root/.claude/plugins/cache/agentskills/pin-actions-to-sha/0f4706c07b6b",
        "version": "0f4706c07b6b",
        "installedAt": "2026-07-17T00:00:38.572Z",
        "lastUpdated": "2026-07-17T00:00:38.572Z",
        "gitCommitSha": "0f4706c07b6bd1ad16ee39a86884a81a96270bff"
      }
    ]
  }
}
```

No absences: all three files exist, plus a `cache/` and `marketplaces/`
directory and a `.last_inuse_sweep` marker.

## (5) Is a /pin-actions-to-sha:pin-actions-to-sha skill available in my loaded session context?

**NO.** The plugin is installed on disk (see section 4), but the skill is NOT
present in my loaded session skill listing. The skills exposed to this session
are:

```
session-start-hook, deep-research, dataviz, artifact-design,
artifact-capabilities, update-config, keybindings-help, verify, code-review,
simplify, fewer-permission-prompts, loop, claude-api, run, init, review,
security-review
```

No `pin-actions-to-sha:pin-actions-to-sha` entry appears. The plugin was
installed by the SessionStart hook AFTER the session skill registry was
already built, so the newly-installed skill did not get loaded into this
running session's context.

## (6) claude plugin marketplace list 2>&1 | head -20

```
Configured marketplaces:

  > agentskills
    Source: GitHub (Adam-S-Daniel/agentskills)
```

## Summary

- The SessionStart hook **ran successfully** (exit 0) and its stdout is
  captured both in `/tmp/e1-hook.log` and as a system line in session context.
- The hook's actual work was to add the `agentskills` marketplace and install
  the `pin-actions-to-sha@agentskills` plugin — both persisted to disk under
  `~/.claude/plugins/`.
- Despite successful on-disk installation, the plugin's skill is **not
  available** in this running session (installed after the skill registry was
  built).
