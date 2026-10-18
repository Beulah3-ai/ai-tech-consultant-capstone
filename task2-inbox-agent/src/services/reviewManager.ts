import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { v4 as uuidv4 } from "uuid";
import {
  CustomerEmail,
  SuggestedDraft,
  ReviewRequest,
  ReviewRequestSchema,
  AuditRecord,
  AutonomyStatus,
  EmailCategory,
} from "../types.js";
import { EmailClassifier } from "./classifier.js";
import { DraftGenerator } from "./draftGenerator.js";
import { AutonomySafeguardTracker, DecisionResult } from "./autonomySafeguard.js";
import { KnowledgeBrainClient } from "../client/knowledgeBrainClient.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface PersistedStoreData {
  version: string;
  saved_at: string;
  drafts: Record<string, SuggestedDraft>;
  auditTrail: AuditRecord[];
  autonomyState: Record<EmailCategory, AutonomyStatus>;
}

export class ReviewManager {
  private emails = new Map<string, CustomerEmail>();
  private drafts = new Map<string, SuggestedDraft>();
  private auditTrail: AuditRecord[] = [];
  private autonomyTracker: AutonomySafeguardTracker;
  private classifier: EmailClassifier;
  private draftGenerator: DraftGenerator;
  private persistPath: string | null;

  constructor(
    kbClient?: KnowledgeBrainClient,
    autonomyTracker?: AutonomySafeguardTracker,
    persistPath?: string | null
  ) {
    const client = kbClient || new KnowledgeBrainClient();
    this.autonomyTracker = autonomyTracker || new AutonomySafeguardTracker();
    this.classifier = new EmailClassifier();
    this.draftGenerator = new DraftGenerator(client);

    if (persistPath === null) {
      this.persistPath = null;
    } else {
      this.persistPath =
        persistPath ||
        process.env.STORE_PATH ||
        path.resolve(__dirname, "../../data/inbox_store.json");
    }

    this.loadFromDisk();
  }

  private loadFromDisk(): void {
    if (!this.persistPath || !fs.existsSync(this.persistPath)) {
      return;
    }

    try {
      const raw = fs.readFileSync(this.persistPath, "utf-8");
      const data = JSON.parse(raw) as PersistedStoreData;

      if (data && typeof data === "object") {
        if (data.drafts) {
          for (const [id, draft] of Object.entries(data.drafts)) {
            this.drafts.set(id, draft);
          }
        }
        if (Array.isArray(data.auditTrail)) {
          this.auditTrail = data.auditTrail;
        }
        if (data.autonomyState) {
          this.autonomyTracker.loadStateSnapshot(data.autonomyState);
        }
      }
    } catch (err) {
      console.error(`Warning: Failed to load store from ${this.persistPath}:`, err);
    }
  }

  saveToDisk(): void {
    if (!this.persistPath) {
      return;
    }

    try {
      const dir = path.dirname(this.persistPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      const draftsObj: Record<string, SuggestedDraft> = {};
      for (const [id, d] of this.drafts.entries()) {
        draftsObj[id] = d;
      }

      const payload: PersistedStoreData = {
        version: "1.0",
        saved_at: new Date().toISOString(),
        drafts: draftsObj,
        auditTrail: this.auditTrail,
        autonomyState: this.autonomyTracker.getStateSnapshot(),
      };

      fs.writeFileSync(this.persistPath, JSON.stringify(payload, null, 2), "utf-8");
    } catch (err) {
      console.error(`Warning: Failed to save store to ${this.persistPath}:`, err);
    }
  }

  async loadEmails(
    emails: CustomerEmail[],
    providerOverride?: string
  ): Promise<SuggestedDraft[]> {
    const generated: SuggestedDraft[] = [];

    for (const email of emails) {
      this.emails.set(email.id, email);
      const draftId = `draft_${email.id}`;

      // If draft was already reviewed or persisted, preserve existing status and final reply
      const existing = this.drafts.get(draftId);
      if (existing && existing.status !== "pending_review") {
        generated.push(existing);
        continue;
      }

      const classification = this.classifier.classify(email.subject, email.body);
      const draft = await this.draftGenerator.generateDraft(
        email,
        classification,
        providerOverride
      );
      this.drafts.set(draft.id, draft);
      generated.push(draft);
    }

    this.saveToDisk();
    return generated;
  }

  getAllDrafts(filter?: { status?: string; category?: string }): SuggestedDraft[] {
    let list = Array.from(this.drafts.values());
    if (filter?.status) {
      list = list.filter(d => d.status === filter.status);
    }
    if (filter?.category) {
      list = list.filter(d => d.category === filter.category);
    }
    // Sort latest first
    return list.sort((a, b) => b.created_at.localeCompare(a.created_at));
  }

  getDraftById(id: string): SuggestedDraft | undefined {
    return this.drafts.get(id);
  }

  submitReview(
    draftId: string,
    rawReview: ReviewRequest
  ): { draft: SuggestedDraft; auditRecord: AuditRecord; autonomy: DecisionResult } {
    const validated = ReviewRequestSchema.parse(rawReview);
    const draft = this.drafts.get(draftId);

    if (!draft) {
      throw new Error(`Draft with ID '${draftId}' not found.`);
    }
    // Prevent approval of answered drafts with missing or placeholder citations.
const isApproval =
  validated.action === "approve" ||
  validated.action === "edit_and_approve";

const hasVerifiableSources =
  draft.sources.length > 0 &&
  draft.sources.every(
    source =>
      /https?:\/\/\S+/i.test(source) &&
      !/^doc\d+$/i.test(source.trim())
  );

if (isApproval && draft.answered && !hasVerifiableSources) {
  throw new Error(
    "Approval blocked: this draft contains an answer without verifiable source URLs. Escalate it for human review."
  );
}

    const now = new Date().toISOString();
    const finalReply = validated.final_reply !== undefined ? validated.final_reply : draft.suggested_reply;

    // Detect if reviewer made edits to the suggested text
    const diffDetected =
      finalReply.trim() !== draft.suggested_reply.trim() ||
      validated.action === "edit_and_approve";

    // Determine target draft status
    let newStatus: SuggestedDraft["status"] = "pending_review";
    if (validated.action === "approve") {
      newStatus = diffDetected ? "edited" : "approved";
    } else if (validated.action === "edit_and_approve") {
      newStatus = "edited";
    } else if (validated.action === "reject") {
      newStatus = "rejected";
    } else if (validated.action === "escalate") {
      newStatus = "escalated";
    }

    // Update draft record
    draft.status = newStatus;
    draft.reviewed_at = now;
    draft.reviewer_id = validated.reviewer_id;
    draft.final_reply = finalReply;
    draft.notes = validated.notes;
    draft.feedback_rating = validated.feedback_rating;
    draft.feedback_tags = validated.feedback_tags;

    // Update autonomy safeguard counter
    const autonomy = this.autonomyTracker.recordDecision(
      draft.category,
      validated.action,
      diffDetected
    );

    // Create persistent audit trail entry
    const auditRecord: AuditRecord = {
      id: `audit_${uuidv4().replace(/-/g, "").slice(0, 12)}`,
      email_id: draft.email_id,
      action: validated.action,
      category: draft.category,
      reviewer_id: validated.reviewer_id,
      timestamp: now,
      diff_detected: diffDetected,
      qualifies_for_autonomy: autonomy.qualifies,
      consecutive_approved_count: autonomy.consecutive_approved_count,
      autonomy_eligible: autonomy.is_eligible,
      notes: validated.notes,
      feedback_rating: validated.feedback_rating,
      feedback_tags: validated.feedback_tags,
    };

    this.auditTrail.unshift(auditRecord);

    // Persist to disk immediately
    this.saveToDisk();

    return { draft, auditRecord, autonomy };
  }

  getAuditTrail(limit = 100): AuditRecord[] {
    return this.auditTrail.slice(0, limit);
  }

  getFeedbackRecords(): AuditRecord[] {
    return this.auditTrail.filter(
      r => r.feedback_rating || (r.feedback_tags && r.feedback_tags.length > 0) || r.notes
    );
  }

  getAutonomyStatus(category?: any): AutonomyStatus[] {
    return this.autonomyTracker.getStatus(category);
  }
}
