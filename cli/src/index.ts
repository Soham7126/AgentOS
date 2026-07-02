#!/usr/bin/env node
import { Command } from "commander";
import * as cognee from "./cogneeClient.js";
import { resultText, isEmpty } from "./format.js";

const AGENTS = ["claude", "codex", "copilot"] as const;
type Agent = (typeof AGENTS)[number];

function requireAgent(agent: string): asserts agent is Agent {
  if (!AGENTS.includes(agent as Agent)) {
    console.error(`Unknown agent "${agent}". Expected one of: ${AGENTS.join(", ")}`);
    process.exit(1);
  }
}

const program = new Command();
program.name("agent").description("AgentOS — multi-agent coordination over Cognee").version("0.1.0");

program
  .command("assign <task> <agent>")
  .description("Assign a task to an agent")
  .action(async (task: string, agent: string) => {
    requireAgent(agent);
    await cognee.remember(`Task: ${task}. Assigned to ${agent}. Status: in progress.`, {
      agent,
      type: "task",
      status: "in_progress",
    });
    console.log(`Assigned "${task}" to ${agent}.`);
  });

program
  .command("assigned <agent>")
  .description("Show what an agent is assigned to")
  .action(async (agent: string) => {
    requireAgent(agent);
    const { results } = await cognee.recall(`tasks assigned to ${agent}`, { agent, type: "task" });
    console.log(`\n${cap(agent)} is assigned to:\n`);
    if (isEmpty(results)) {
      console.log("  (nothing found)");
      return;
    }
    for (const r of results) console.log(`  - ${resultText(r)}`);
  });

program
  .command("status")
  .description("Show what every agent is doing right now")
  .action(async () => {
    console.log();
    for (const agent of AGENTS) {
      const { results } = await cognee.recall(`the in-progress task assigned to ${agent}`, {
        agent,
        type: "task",
      });
      console.log(cap(agent));
      if (isEmpty(results)) {
        console.log("  Working on: (nothing found)\n");
        continue;
      }
      console.log(`  Working on: ${resultText(results[0])}\n`);
    }
  });

program
  .command("workspace <agent>")
  .description("Show an agent's owned files, tasks, and decisions")
  .action(async (agent: string) => {
    requireAgent(agent);
    const [files, tasks, decisions] = await Promise.all([
      cognee.recall(`files created by ${agent}`, { agent, type: "file" }),
      cognee.recall(`tasks assigned to ${agent}`, { agent, type: "task" }),
      cognee.recall(`decisions made by ${agent}`, { agent, type: "decision" }),
    ]);
    console.log(`\n${cap(agent)}'s Workspace`);
    console.log("─".repeat(30));
    console.log("\nCreated:");
    printList(files.results);
    console.log("\nTasks:");
    printList(tasks.results);
    console.log("\nDecisions made:");
    printList(decisions.results);
  });

program
  .command("handoff <agent>")
  .description("Generate a structured handoff context package for an agent")
  .action(async (agent: string) => {
    requireAgent(agent);
    const [task, decisions, deps, bugs] = await Promise.all([
      cognee.recall(`current in-progress task for ${agent}`, { agent, type: "task" }),
      cognee.recall(`decisions relevant to ${agent}'s current work`, { type: "decision" }),
      cognee.recall("project dependencies", { type: "dependency" }),
      cognee.recall("open unresolved bugs", { type: "bug", status: "open" }),
    ]);

    const line = "═".repeat(35);
    console.log(`\n${line}`);
    console.log(`HANDOFF CONTEXT → ${cap(agent)}`);
    console.log(line);

    console.log("\nCurrent Task:");
    console.log(isEmpty(task.results) ? "  (none found)" : `  ${resultText(task.results[0])}`);

    console.log("\nRelevant Decisions:");
    printList(decisions.results.slice(0, 3));

    console.log("\nDependencies:");
    console.log(isEmpty(deps.results) ? "  (none found)" : `  ${resultText(deps.results[0])}`);

    console.log("\nOpen Issues:");
    if (isEmpty(bugs.results)) {
      console.log("  (none found)");
    } else {
      for (const b of bugs.results) console.log(`  ⚠ ${resultText(b)}`);
    }
    console.log(line);
  });

program
  .command("timeline")
  .description("Show every event chronologically across all agents")
  .action(async () => {
    const { results } = await cognee.recall("chronological history of all project events", {}, 50);
    console.log("\nTimeline\n");
    if (isEmpty(results)) {
      console.log("  (nothing found)");
      return;
    }
    for (const r of results) console.log(`  ${resultText(r)}`);
  });

program
  .command("why <decision>")
  .description("Explain the reasoning behind a past decision")
  .action(async (decision: string) => {
    const { results } = await cognee.recall(`why was the decision about ${decision} made`, {
      type: "decision",
    });
    if (isEmpty(results)) {
      console.log(`\nNo decision found matching "${decision}".`);
      return;
    }
    console.log(`\n${resultText(results[0])}`);
  });

program
  .command("log <message>")
  .description("Manually record an activity entry (used for Codex/Copilot)")
  .option("-a, --agent <agent>", "agent this log entry belongs to")
  .action(async (message: string, opts: { agent?: string }) => {
    await cognee.remember(message, opts.agent ? { agent: opts.agent, type: "log" } : { type: "log" });
    console.log("Logged.");
  });

program
  .command("forget <task>")
  .description("Remove a resolved task or closed bug from memory")
  .action(async (task: string) => {
    const result = await cognee.forget(task);
    if (result.status === "forgotten") {
      console.log(`Forgot: "${task}".`);
    } else {
      console.log(`Nothing matching "${task}" was found in memory.`);
    }
  });

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function printList(results: cognee.RecallResult[]): void {
  if (isEmpty(results)) {
    console.log("  (none found)");
    return;
  }
  for (const r of results) console.log(`  - ${resultText(r)}`);
}

program.parseAsync(process.argv).catch((err) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
