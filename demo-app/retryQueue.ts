import type { Redis } from "ioredis";

const QUEUE_KEY = "relaycli:retry-queue";
const MAX_ATTEMPTS = 5;

export interface RetryJob {
  payload: string;
  destination: string;
  attempt: number;
}

/** Redis-backed retry queue with exponential backoff (durable across crashes). */
export class RetryQueue {
  constructor(private redis: Redis) {}

  async enqueue(job: RetryJob): Promise<void> {
    await this.redis.rpush(QUEUE_KEY, JSON.stringify(job));
  }

  async requeueWithBackoff(job: RetryJob): Promise<void> {
    if (job.attempt >= MAX_ATTEMPTS) return;
    const next = { ...job, attempt: job.attempt + 1 };
    const delayMs = 2 ** next.attempt * 1000;
    setTimeout(() => this.enqueue(next), delayMs);
  }

  async dequeue(): Promise<RetryJob | null> {
    const raw = await this.redis.lpop(QUEUE_KEY);
    return raw ? (JSON.parse(raw) as RetryJob) : null;
  }
}
