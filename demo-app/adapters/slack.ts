import type { Adapter } from "./adapter.js";

export class SlackAdapter implements Adapter {
  name = "slack";

  constructor(private webhookUrl: string) {}

  async send(payload: string): Promise<void> {
    await fetch(this.webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: payload }),
    });
  }
}
