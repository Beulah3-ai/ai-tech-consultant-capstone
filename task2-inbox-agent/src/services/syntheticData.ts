import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { CustomerEmail, CustomerEmailSchema } from "../types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function loadSyntheticEmails(): CustomerEmail[] {
  // Resolve data path relative to project root
  const candidatePaths = [
    path.resolve(__dirname, "../../data/synthetic_emails.json"),
    path.resolve(process.cwd(), "data/synthetic_emails.json"),
  ];

  let rawData = "";
  for (const p of candidatePaths) {
    if (fs.existsSync(p)) {
      rawData = fs.readFileSync(p, "utf-8");
      break;
    }
  }

  if (!rawData) {
    throw new Error("synthetic_emails.json not found in data/ directory.");
  }

  const parsed = JSON.parse(rawData);
  if (!Array.isArray(parsed)) {
    throw new Error("synthetic_emails.json must contain an array of emails.");
  }

  return parsed.map((item, idx) => {
    try {
      return CustomerEmailSchema.parse(item);
    } catch (err) {
      throw new Error(`Invalid synthetic email format at index ${idx}: ${err}`);
    }
  });
}
