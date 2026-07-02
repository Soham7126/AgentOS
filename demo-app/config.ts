import { readFileSync } from "node:fs";
import { z } from "zod";

const ConfigSchema = z.object({
  port: z.number().default(3000),
  destinations: z.array(
    z.object({
      name: z.string(),
      type: z.enum(["slack", "email"]),
      target: z.string(),
    })
  ),
  redisUrl: z.string().default("redis://localhost:6379"),
});

export type RelayConfig = z.infer<typeof ConfigSchema>;

export function loadConfig(path = "relay.config.json"): RelayConfig {
  const raw = JSON.parse(readFileSync(path, "utf-8"));
  return ConfigSchema.parse(raw);
}
