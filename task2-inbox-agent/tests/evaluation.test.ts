import { describe, it, expect, beforeEach } from "vitest";
import { EmailClassifier } from "../src/services/classifier.js";
import { DraftGenerator } from "../src/services/draftGenerator.js";
import { AutonomySafeguardTracker } from "../src/services/autonomySafeguard.js";
import { ReviewManager } from "../src/services/reviewManager.js";
import { KnowledgeBrainClient } from "../src/client/knowledgeBrainClient.js";
import { loadSyntheticEmails } from "../src/services/syntheticData.js";
import { CustomerEmail, ReviewRequestSchema } from "../src/types.js";

describe("Task 2: Inbox Agent Evaluation & Safeguard Test Suite", () => {
  let classifier: EmailClassifier;
  let autonomyTracker: AutonomySafeguardTracker;

  beforeEach(() => {
    classifier = new EmailClassifier();
    autonomyTracker = new AutonomySafeguardTracker();
  });

  // 1. Classification Tests
  it("Test 1: Classifies technical support inquiries correctly", () => {
    const result = classifier.classify(
      "A-Record DNS question",
      "How do I update my A-Record to point to the directory IP address?"
    );
    expect(result.category).toBe("technical_support");
    expect(result.confidence).toBeGreaterThan(0.7);
  });

  it("Test 2: Classifies billing inquiries correctly", () => {
    const result = classifier.classify(
      "Duplicate charge on monthly subscription",
      "I was billed twice on Stripe for our monthly invoice. Please issue a refund."
    );
    expect(result.category).toBe("billing");
    expect(result.confidence).toBeGreaterThan(0.7);
  });

  it("Test 3: Classifies onboarding inquiries correctly", () => {
    const result = classifier.classify(
      "Member import CSV template question",
      "We have 500 members to bulk import using the CSV checklist. Where is the template?"
    );
    expect(result.category).toBe("onboarding");
    expect(result.confidence).toBeGreaterThan(0.7);
  });

  it("Test 4: Classifies feature requests correctly", () => {
    const result = classifier.classify(
      "Feature request: Zapier integration",
      "We would love an official Zapier or Make connector on your product roadmap."
    );
    expect(result.category).toBe("feature_requests");
    expect(result.priority).toBe("low");
  });

  it("Test 5: Classifies account configuration inquiries correctly", () => {
    const result = classifier.classify(
      "Sub-admin permission settings",
      "How do I invite a team member with limited permissions to manage member listings?"
    );
    expect(result.category).toBe("account_configuration");
  });

  it("Test 6: Classifies out-of-scope inquiries correctly", () => {
    const result = classifier.classify(
      "Sourdough starter hydration ratio",
      "What is the recommended hydration percentage and fermentation temperature for rye sourdough?"
    );
    expect(result.category).toBe("out_of_scope");
    expect(result.priority).toBe("low");
  });

  // 2. Priority Assignment Tests
  it("Test 7: Assigns urgent priority to system outages and 500 errors", () => {
    const result = classifier.classify(
      "CRITICAL OUTAGE: 500 error",
      "The entire site is down and throwing 500 Internal Server Error for all users!"
    );
    expect(result.priority).toBe("urgent");
  });

  it("Test 8: Assigns high priority to duplicate charges and payment failures", () => {
    const result = classifier.classify(
      "Duplicate charge refund immediately",
      "Your billing system charged our card twice. Please reverse the duplicate charge."
    );
    expect(result.priority).toBe("high");
  });

  it("Test 9: Assigns low priority to general feature requests and out-of-scope questions", () => {
    const feat = classifier.classify("Feature request: dark mode", "Can you add dark mode?");
    expect(feat.priority).toBe("low");

    const oos = classifier.classify("Car transmission noise", "My Honda Civic is whining.");
    expect(oos.priority).toBe("low");
  });

  // 3. Grounding & Citations Tests
  it("Test 10: Generates grounded draft with citations when Task 1 evidence is found", async () => {
    const mockKbClient = {
      query: async () => ({
        success: true,
        data: {
          query: "How to connect domain?",
          answer: "Point A-Record to 54.208.12.34.",
          answered: true,
          confidence: 0.95,
          provider: "local_retrieval",
          is_mock: false,
          sources: ["Connecting Custom Domains (https://support.brilliantdirectories.com/articles/custom-domains)"],
          disclaimer: "Retrieved from local documentation.",
        },
      }),
    } as unknown as KnowledgeBrainClient;

    const generator = new DraftGenerator(mockKbClient);
    const email: CustomerEmail = {
      id: "test_01",
      synthetic: true,
      sender: "Test User <test@example.synthetic.test>",
      subject: "A-Record Question",
      body: "What IP should I use for A-Record?",
      received_at: "2026-10-17T12:00:00Z",
    };

    const draft = await generator.generateDraft(email, {
      category: "technical_support",
      priority: "medium",
      confidence: 0.9,
      matchedKeywords: ["a-record"],
    });

    expect(draft.answered).toBe(true);
    expect(draft.needs_escalation).toBe(false);
    expect(draft.sources.length).toBe(1);
    expect(draft.sources[0]).toContain("https://support.brilliantdirectories.com");
    expect(draft.suggested_reply).toContain("54.208.12.34");
  });

  // 4. Abstention Tests
  it("Test 11: Explicitly abstains and flags for escalation when Task 1 returns answered: false", async () => {
    const mockKbClient = {
      query: async () => ({
        success: true,
        data: {
          query: "Unknown question",
          answer: "Insufficient evidence found.",
          answered: false,
          confidence: 0.0,
          provider: "local_retrieval",
          is_mock: false,
          sources: [],
          disclaimer: "Abstained.",
        },
      }),
    } as unknown as KnowledgeBrainClient;

    const generator = new DraftGenerator(mockKbClient);
    const email: CustomerEmail = {
      id: "test_02",
      synthetic: true,
      sender: "Test User <test@example.synthetic.test>",
      subject: "Obscure integration",
      body: "How to integrate with proprietary AS400 mainframe?",
      received_at: "2026-10-17T12:00:00Z",
    };

    const draft = await generator.generateDraft(email, {
      category: "technical_support",
      priority: "medium",
      confidence: 0.8,
      matchedKeywords: [],
    });

    expect(draft.answered).toBe(false);
    expect(draft.needs_escalation).toBe(true);
    expect(draft.sources.length).toBe(0);
    expect(draft.suggested_reply).toContain("insufficient verified evidence");
  });

  it("Test 12: Handles out-of-scope inquiries without calling knowledge retrieval", async () => {
    const mockKbClient = {
      query: async () => {
        throw new Error("Should not be called for out_of_scope!");
      },
    } as unknown as KnowledgeBrainClient;

    const generator = new DraftGenerator(mockKbClient);
    const email: CustomerEmail = {
      id: "test_03",
      synthetic: true,
      sender: "Chef <chef@example.synthetic.test>",
      subject: "Baking bread",
      body: "How do I make sourdough bread?",
      received_at: "2026-10-17T12:00:00Z",
    };

    const draft = await generator.generateDraft(email, {
      category: "out_of_scope",
      priority: "low",
      confidence: 0.95,
      matchedKeywords: ["sourdough"],
    });

    expect(draft.answered).toBe(false);
    expect(draft.category).toBe("out_of_scope");
    expect(draft.suggested_reply).toContain("outside the scope of our directory platform");
  });

  // 5. API Failure Resilience
  it("Test 13: Handles Task 1 API failure safely and routes to human specialist", async () => {
    const mockKbClient = {
      query: async () => ({
        success: false,
        error: "Connection refused: http://localhost:8000",
      }),
    } as unknown as KnowledgeBrainClient;

    const generator = new DraftGenerator(mockKbClient);
    const email: CustomerEmail = {
      id: "test_04",
      synthetic: true,
      sender: "User <user@example.synthetic.test>",
      subject: "Help",
      body: "My domain is broken",
      received_at: "2026-10-17T12:00:00Z",
    };

    const draft = await generator.generateDraft(email, {
      category: "technical_support",
      priority: "high",
      confidence: 0.8,
      matchedKeywords: [],
    });

    expect(draft.answered).toBe(false);
    expect(draft.needs_escalation).toBe(true);
    expect(draft.provider).toBe("system_fallback");
    expect(draft.disclaimer).toContain("Knowledge retrieval error");
  });

  // 6. Review Actions & Diff Detection
  it("Test 14: Review action 'approve' without modifications qualifies for autonomy (+1)", () => {
    const dec = autonomyTracker.recordDecision("technical_support", "approve", false);
    expect(dec.qualifies).toBe(true);
    expect(dec.consecutive_approved_count).toBe(1);
    expect(dec.is_eligible).toBe(false);
  });

  it("Test 15: Review action 'edit_and_approve' resets consecutive autonomy count to 0", () => {
    autonomyTracker.recordDecision("billing", "approve", false);
    autonomyTracker.recordDecision("billing", "approve", false);
    expect(autonomyTracker.getStatus("billing")[0].consecutive_approved_count).toBe(2);

    const dec = autonomyTracker.recordDecision("billing", "edit_and_approve", true);
    expect(dec.qualifies).toBe(false);
    expect(dec.consecutive_approved_count).toBe(0);
    expect(dec.reset_reason).toContain("modified");
  });

  it("Test 16: Review action 'approve' with modified text detects diff and resets count to 0", () => {
    autonomyTracker.recordDecision("onboarding", "approve", false);
    const dec = autonomyTracker.recordDecision("onboarding", "approve", true); // diff detected
    expect(dec.qualifies).toBe(false);
    expect(dec.consecutive_approved_count).toBe(0);
  });

  it("Test 17: Review action 'reject' resets consecutive autonomy count to 0", () => {
    autonomyTracker.recordDecision("technical_support", "approve", false);
    const dec = autonomyTracker.recordDecision("technical_support", "reject", false);
    expect(dec.qualifies).toBe(false);
    expect(dec.consecutive_approved_count).toBe(0);
    expect(dec.reset_reason).toContain("rejected");
  });

  it("Test 18: Review action 'escalate' records escalation and resets autonomy count to 0", () => {
    autonomyTracker.recordDecision("technical_support", "approve", false);
    const dec = autonomyTracker.recordDecision("technical_support", "escalate", false);
    expect(dec.qualifies).toBe(false);
    expect(dec.consecutive_approved_count).toBe(0);
    expect(dec.reset_reason).toContain("escalated");
  });

  // 7. Autonomy Safeguard 20-Draft Rule
  it("Test 19: Category becomes eligible for autonomy ONLY after 20 consecutive qualifying approvals", () => {
    // 19 consecutive approvals
    for (let i = 1; i <= 19; i++) {
      const dec = autonomyTracker.recordDecision("technical_support", "approve", false);
      expect(dec.consecutive_approved_count).toBe(i);
      expect(dec.is_eligible).toBe(false);
    }

    // 20th consecutive approval -> becomes eligible!
    const finalDec = autonomyTracker.recordDecision("technical_support", "approve", false);
    expect(finalDec.consecutive_approved_count).toBe(20);
    expect(finalDec.is_eligible).toBe(true);

    const status = autonomyTracker.getStatus("technical_support")[0];
    expect(status.is_eligible).toBe(true);
    expect(status.consecutive_approved_count).toBe(20);
  });

  it("Test 20: Autonomy streak resets to 0 if draft 20 is edited or rejected", () => {
    // 19 consecutive approvals
    for (let i = 1; i <= 19; i++) {
      autonomyTracker.recordDecision("billing", "approve", false);
    }
    expect(autonomyTracker.getStatus("billing")[0].consecutive_approved_count).toBe(19);

    // 20th draft is edited!
    const dec = autonomyTracker.recordDecision("billing", "approve", true); // diff detected
    expect(dec.consecutive_approved_count).toBe(0);
    expect(dec.is_eligible).toBe(false);
    expect(autonomyTracker.getStatus("billing")[0].is_eligible).toBe(false);
  });

  // 8. Review Manager & Audit Trail
  it("Test 21: ReviewManager records full audit trail with reviewer ID, diff detection, and timestamps", async () => {
    const mockKbClient = {
      query: async () => ({
        success: true,
        data: {
          query: "DNS",
          answer: "DNS answer",
          answered: true,
          confidence: 0.9,
          provider: "local_retrieval",
          is_mock: false,
          sources: ["doc1"],
          disclaimer: "ok",
        },
      }),
    } as unknown as KnowledgeBrainClient;

    const manager = new ReviewManager(mockKbClient, autonomyTracker,null);
    const email: CustomerEmail = {
      id: "email_audit_01",
      synthetic: true,
      sender: "Auditor <auditor@example.synthetic.test>",
      subject: "DNS Question",
      body: "DNS details please",
      received_at: "2026-10-17T12:00:00Z",
    };

    const [draft] = await manager.loadEmails([email]);

    const reviewRes = manager.submitReview(draft.id, {
      action: "approve",
      reviewer_id: "Lead Consultant 01",
      notes: "Verified DNS IP address matches documentation.",
    });

    expect(reviewRes.draft.status).toBe("approved");
    expect(reviewRes.auditRecord.reviewer_id).toBe("Lead Consultant 01");
    expect(reviewRes.auditRecord.diff_detected).toBe(false);
    expect(reviewRes.auditRecord.qualifies_for_autonomy).toBe(true);

    const auditTrail = manager.getAuditTrail();
    expect(auditTrail.length).toBe(1);
    expect(auditTrail[0].email_id).toBe("email_audit_01");
  });

  // 9. Schema Validation
  it("Test 22: Zod schema validation rejects review payload with missing or empty reviewer_id", () => {
    const invalidPayload = {
      action: "approve",
      reviewer_id: "   ",
    };
    const res = ReviewRequestSchema.safeParse(invalidPayload);
    expect(res.success).toBe(false);
  });

  // 10. Synthetic Dataset Integrity
  it("Test 23: Synthetic email dataset contains >= 50 emails and covers all 6 categories", () => {
    const emails = loadSyntheticEmails();
    expect(emails.length).toBeGreaterThanOrEqual(50);

    const categoriesFound = new Set(emails.map(e => e.expected_category).filter(Boolean));
    expect(categoriesFound.size).toBe(6);
    expect(categoriesFound.has("technical_support")).toBe(true);
    expect(categoriesFound.has("billing")).toBe(true);
    expect(categoriesFound.has("onboarding")).toBe(true);
    expect(categoriesFound.has("feature_requests")).toBe(true);
    expect(categoriesFound.has("account_configuration")).toBe(true);
    expect(categoriesFound.has("out_of_scope")).toBe(true);

    // Every email must be explicitly labeled synthetic
    for (const e of emails) {
      expect(e.synthetic).toBe(true);
      expect(e.sender).toContain("synthetic");
    }
  });

  // 11. Mock Transparency
  it("Test 24: Offline mock provider clearly labels mock status and never claims to be Claude", async () => {
    const client = new KnowledgeBrainClient({ useMockFallback: true });
    const res = await client.query("How do I connect my custom domain?");

    expect(res.success).toBe(true);
    expect(res.data?.is_mock).toBe(true);
    expect(res.data?.provider).toBe("mock");
    expect(res.data?.answer).toContain("[MOCK PROVIDER]");
    expect(res.data?.disclaimer).toContain("Mock AI Response");
  });

  // 12. Autonomy Safeguard Category Isolation
  it("Test 25: Autonomy streak counts are isolated per category; resets in one do not affect another", () => {
    // 5 approvals in technical_support
    for (let i = 0; i < 5; i++) {
      autonomyTracker.recordDecision("technical_support", "approve", false);
    }
    // 3 approvals in billing
    for (let i = 0; i < 3; i++) {
      autonomyTracker.recordDecision("billing", "approve", false);
    }

    expect(autonomyTracker.getStatus("technical_support")[0].consecutive_approved_count).toBe(5);
    expect(autonomyTracker.getStatus("billing")[0].consecutive_approved_count).toBe(3);

    // Edit occurs in billing -> resets billing ONLY
    autonomyTracker.recordDecision("billing", "edit_and_approve", true);

    expect(autonomyTracker.getStatus("billing")[0].consecutive_approved_count).toBe(0);
    // technical_support remains intact at 5!
    expect(autonomyTracker.getStatus("technical_support")[0].consecutive_approved_count).toBe(5);
  });

  // 13. Persistence of Audit Records & Feedback to Disk
  it("Test 26: ReviewManager persists decisions, feedback rating, and autonomy state to disk and rehydrates", async () => {
    const os = await import("os");
    const path = await import("path");
    const fs = await import("fs");

    const tmpStoreFile = path.join(os.tmpdir(), `test_store_${Date.now()}.json`);

    try {
      const mockKbClient = {
        query: async () => ({
          success: true,
          data: {
            query: "Q",
            answer: "A",
            answered: true,
            confidence: 0.9,
            provider: "local_retrieval",
            is_mock: false,
            sources: ["s1"],
            disclaimer: "ok",
          },
        }),
      } as unknown as KnowledgeBrainClient;

      const email: CustomerEmail = {
        id: "persist_email_01",
        synthetic: true,
        sender: "User <user@example.synthetic.test>",
        subject: "Subject",
        body: "Body",
        received_at: "2026-10-17T12:00:00Z",
      };

      // Instance 1: loads email, reviews it with feedback, saves to disk
      const manager1 = new ReviewManager(mockKbClient, undefined, tmpStoreFile);
      const [draft] = await manager1.loadEmails([email]);

      manager1.submitReview(draft.id, {
        action: "approve",
        reviewer_id: "Senior Architect",
        notes: "Excellent grounded citation",
        feedback_rating: "accurate_and_grounded",
        feedback_tags: ["accurate_citations"],
      });

      // Verify file was written to disk
      expect(fs.existsSync(tmpStoreFile)).toBe(true);

      // Instance 2: restarts and rehydrates from disk
      const manager2 = new ReviewManager(mockKbClient, undefined, tmpStoreFile);
      const rehydratedDraft = manager2.getDraftById(draft.id);

      expect(rehydratedDraft).toBeDefined();
      expect(rehydratedDraft?.status).toBe("approved");
      expect(rehydratedDraft?.reviewer_id).toBe("Senior Architect");
      expect(rehydratedDraft?.feedback_rating).toBe("accurate_and_grounded");

      const auditRecords = manager2.getAuditTrail();
      expect(auditRecords.length).toBe(1);
      expect(auditRecords[0].feedback_rating).toBe("accurate_and_grounded");
      expect(auditRecords[0].notes).toBe("Excellent grounded citation");

      const feedbackRecords = manager2.getFeedbackRecords();
      expect(feedbackRecords.length).toBe(1);
    } finally {
      const fs = await import("fs");
      if (fs.existsSync(tmpStoreFile)) {
        fs.unlinkSync(tmpStoreFile);
      }
    }
  });
});

