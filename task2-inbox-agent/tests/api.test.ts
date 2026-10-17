import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { Server } from "http";
import { createApp } from "../src/app.js";
import { ReviewManager } from "../src/services/reviewManager.js";
import { KnowledgeBrainClient } from "../src/client/knowledgeBrainClient.js";

describe("Inbox Agent Express REST API Endpoints", () => {
  let server: Server;
  let baseUrl: string;

  beforeAll(async () => {
    const mockKbClient = new KnowledgeBrainClient({ useMockFallback: true });
    const manager = new ReviewManager(mockKbClient);
    const app = createApp(manager);

    await new Promise<void>((resolve) => {
      server = app.listen(0, () => {
        const addr = server.address();
        if (addr && typeof addr === "object") {
          baseUrl = `http://localhost:${addr.port}`;
        }
        resolve();
      });
    });
  });

  afterAll(async () => {
    await new Promise<void>((resolve) => {
      server.close(() => resolve());
    });
  });

  it("GET /health returns 200 with service status and autonomy data", async () => {
    const res = await fetch(`${baseUrl}/health`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.status).toBe("ok");
    expect(data.service).toBe("inbox-agent");
    expect(data.total_emails_loaded).toBeGreaterThanOrEqual(50);
    expect(Array.isArray(data.autonomy_safeguard)).toBe(true);
  });

  it("GET /api/emails returns list of synthetic customer emails", async () => {
    const res = await fetch(`${baseUrl}/api/emails`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.count).toBeGreaterThanOrEqual(50);
    expect(data.emails[0].synthetic).toBe(true);
  });

  it("GET /api/drafts returns list of suggested drafts", async () => {
    const res = await fetch(`${baseUrl}/api/drafts`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.count).toBeGreaterThan(0);
    expect(data.drafts[0].id).toBeDefined();
  });

  it("POST /api/drafts/:id/review executes review decision and updates autonomy", async () => {
    // 1. Get first draft
    const draftsRes = await fetch(`${baseUrl}/api/drafts`);
    const draftsData = await draftsRes.json();
    const targetDraft = draftsData.drafts[0];

    // 2. Submit approve review
    const reviewRes = await fetch(`${baseUrl}/api/drafts/${targetDraft.id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "approve",
        reviewer_id: "QA Inspector",
        notes: "Approved without changes",
      }),
    });

    expect(reviewRes.status).toBe(200);
    const result = await reviewRes.json();
    expect(result.status).toBe("reviewed");
    expect(result.draft.status).toBe("approved");
    expect(result.audit_record.reviewer_id).toBe("QA Inspector");
  });

  it("POST /api/drafts/:id/review returns 422 for invalid payloads", async () => {
    const res = await fetch(`${baseUrl}/api/drafts/any_id/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "invalid_action",
        reviewer_id: "",
      }),
    });
    expect(res.status).toBe(422);
  });

  it("POST /api/drafts/:id/review returns 404 for nonexistent draft", async () => {
    const res = await fetch(`${baseUrl}/api/drafts/draft_nonexistent_9999/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "approve",
        reviewer_id: "QA Inspector",
      }),
    });
    expect(res.status).toBe(404);
  });

  it("GET /api/audit returns audit records", async () => {
    const res = await fetch(`${baseUrl}/api/audit`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data.audit)).toBe(true);
    expect(data.count).toBeGreaterThanOrEqual(1);
  });

  it("GET /api/feedback returns feedback records", async () => {
    const res = await fetch(`${baseUrl}/api/feedback`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data.feedback)).toBe(true);
  });

  it("GET /api/autonomy returns all 6 categories and safeguard rules", async () => {
    const res = await fetch(`${baseUrl}/api/autonomy`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.autonomy.length).toBe(6);
    expect(data.rule).toContain("20 consecutive");
  });
});

