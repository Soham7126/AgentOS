/** Common interface for all relay destinations (agent decision: one interface, not per-destination branching). */
export interface Adapter {
  name: string;
  send(payload: string): Promise<void>;
}
