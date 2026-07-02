# Judging Checklist

Run through before submitting (PRD.md §8 + §10).

## Impact & Usefulness
- [ ] README explains the context-loss problem in the first paragraph
- [ ] Demo shows a real handoff replacing manual re-briefing

## Creativity
- [ ] Cross-agent, cross-session handoff is the framing (not single-agent memory)

## Technical Excellence
- [ ] `cli/`, `bridge/`, `seed/`, `integrations/`, `demo-app/` stay separated
- [ ] `cli/` never imports Cognee directly — only via `bridge/`
- [ ] All 6 CLI commands + `log` + `forget` run against live Cognee Cloud

## Best Use of Cognee
- [ ] `remember()` demonstrated: seed data, `agent assign`, `agent log`, Claude plugin auto-capture
- [ ] `recall()` demonstrated: `assigned`, `handoff`, `status`, `workspace`, `timeline`, `why`
- [ ] `improve()` demonstrated: Claude plugin's `SessionEnd` hook (point to it explicitly in README)
- [ ] `forget()` demonstrated: `agent forget` with a clear before/after

## User Experience
- [ ] `agent handoff` output is clean human-readable text, not raw JSON
- [ ] `agent why` fails gracefully on no match (no crash)

## Presentation Quality
- [ ] README has architecture diagram + setup steps + demo video link
- [ ] Demo video ≤5 min, leads with `agent handoff`
- [ ] Cognee Cloud track selected on submission
