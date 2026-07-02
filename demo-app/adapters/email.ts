import type { Adapter } from "./adapter.js";

export class EmailAdapter implements Adapter {
  name = "email";

  constructor(private recipient: string) {}

  async send(payload: string): Promise<void> {
    // ponytail: no SMTP client wired up — demo subject app, not the submission itself.
    console.log(`[email → ${this.recipient}] ${payload}`);
  }
}
