import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";

const MAGIC = Buffer.from("ASBK1");
const IV_LEN = 12;

export function encryptBytes(plain, key) {
  if (!Buffer.isBuffer(key) || key.length !== 32) {
    const error = new Error("bad_key");
    error.code = "bad_key";
    throw error;
  }
  const iv = randomBytes(IV_LEN);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const body = Buffer.concat([cipher.update(plain), cipher.final(), cipher.getAuthTag()]);
  return Buffer.concat([MAGIC, iv, body]);
}

export function decryptBytes(blob, key) {
  if (!Buffer.isBuffer(key) || key.length !== 32) {
    const error = new Error("bad_key");
    error.code = "bad_key";
    throw error;
  }
  if (!Buffer.isBuffer(blob) || blob.length < MAGIC.length + IV_LEN + 16 || !blob.subarray(0, MAGIC.length).equals(MAGIC)) {
    const error = new Error("tamper");
    error.code = "tamper";
    throw error;
  }
  const iv = blob.subarray(MAGIC.length, MAGIC.length + IV_LEN);
  const tag = blob.subarray(blob.length - 16);
  const data = blob.subarray(MAGIC.length + IV_LEN, blob.length - 16);
  try {
    const decipher = createDecipheriv("aes-256-gcm", key, iv);
    decipher.setAuthTag(tag);
    return Buffer.concat([decipher.update(data), decipher.final()]);
  } catch {
    const error = new Error("tamper");
    error.code = "tamper";
    throw error;
  }
}
