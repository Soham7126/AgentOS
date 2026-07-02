#!/usr/bin/env node
import { Command } from "commander";
import { Redis } from "ioredis";
import { loadConfig } from "./config.js";
import { validateSignature } from "./validateSignature.js";
import { RetryQueue } from "./retryQueue.js";
import { SlackAdapter } from "./adapters/slack.js";
import { EmailAdapter } from "./adapters/email.js";
import type { Adapter } from "./adapters/adapter.js";

const program = new Command();
program.name("relaycli").description("Webhook relay CLI tool").version("0.1.0");

program
  .command("relay")
  .description("Start the webhook relay server")
  .option("-c, --config <path>", "path to relay.config.json", "relay.config.json")
  .action((opts: { config: string }) => {
    const config = loadConfig(opts.config);
    const redis = new Redis(config.redisUrl);
    const queue = new RetryQueue(redis);

    const adapters: Adapter[] = config.destinations.map((d) =>
      d.type === "slack" ? new SlackAdapter(d.target) : new EmailAdapter(d.target)
    );

    console.log(`RelayCLI listening on port ${config.port}, ${adapters.length} destination(s) configured.`);
    void queue; // wired by POST /webhooks/:source handler (API layer, out of scope for this stub)
  });

program.parse(process.argv);
