import { createHmac, timingSafeEqual } from "node:crypto";

/**
 * Validates an HMAC-SHA256 webhook signature (Stripe/GitHub style).
 * See agent decision: "HMAC-SHA256 chosen for timing-attack safety."
 */
export function validateSignature(payload: string, signature: string, secret: string): boolean {
  const expected = createHmac("sha256", secret).update(payload).digest("hex");
  const expectedBuf = Buffer.from(expected, "utf-8");
  const signatureBuf = Buffer.from(signature, "utf-8");
  if (expectedBuf.length !== signatureBuf.length) return false;
  return timingSafeEqual(expectedBuf, signatureBuf);
}
