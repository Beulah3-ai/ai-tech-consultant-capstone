import express, { Request, Response, NextFunction } from "express";
import path from "path";
import { fileURLToPath } from "url";
import { ReviewManager } from "./services/reviewManager.js";
import { loadSyntheticEmails } from "./services/syntheticData.js";
import { ReviewRequestSchema } from "./types.js";
import { KnowledgeBrainClient } from "./client/knowledgeBrainClient.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function createApp(reviewManager?: ReviewManager): express.Express {
  const app = express();
  app.use(express.json());

  // Static assets for Human Review UI
  const publicDir = path.resolve(__dirname, "../src/public");
  app.use(express.static(publicDir));

  const kbClient = new KnowledgeBrainClient();
  const manager = reviewManager || new ReviewManager(kbClient);

  // Initialize store with synthetic emails if empty
  const emails = loadSyntheticEmails();
  if (manager.getAllDrafts().length === 0) {
    manager.loadEmails(emails).catch(err => {
      console.error("Failed to initialize drafts with synthetic emails:", err);
    });
  }

  // 1. Health check
  app.get("/health", (_req: Request, res: Response) => {
    res.json({
      status: "ok",
      service: "inbox-agent",
      timestamp: new Date().toISOString(),
      knowledge_brain_url: process.env.KNOWLEDGE_BRAIN_URL || "http://localhost:8000",
      total_emails_loaded: emails.length,
      total_drafts: manager.getAllDrafts().length,
      autonomy_safeguard: manager.getAutonomyStatus(),
    });
  });

  // 2. Get synthetic emails
  app.get("/api/emails", (_req: Request, res: Response) => {
    res.json({ emails, count: emails.length });
  });

  // 3. Process/re-process emails
  app.post("/api/emails/process", async (req: Request, res: Response, next: NextFunction) => {
    try {
      const provider = req.body?.provider as string | undefined;
      const drafts = await manager.loadEmails(emails, provider);
      res.json({ status: "processed", count: drafts.length, drafts });
    } catch (err) {
      next(err);
    }
  });

  // 4. List all drafts with optional filtering
  app.get("/api/drafts", (req: Request, res: Response) => {
    const status = req.query.status as string | undefined;
    const category = req.query.category as string | undefined;
    const drafts = manager.getAllDrafts({ status, category });
    res.json({ drafts, count: drafts.length });
  });

  // 5. Get draft by ID
  app.get("/api/drafts/:id", (req: Request, res: Response) => {
    const draftId = String(req.params.id);
    const draft = manager.getDraftById(draftId);
    if (!draft) {
      res.status(404).json({ error: `Draft '${draftId}' not found.` });
      return;
    }
    res.json(draft);
  });

  // 6. Review decision (approve, edit_and_approve, reject, escalate)
  app.post("/api/drafts/:id/review", (req: Request, res: Response, next: NextFunction) => {
    try {
      const draftId = String(req.params.id);
      const parseResult = ReviewRequestSchema.safeParse(req.body);
      if (!parseResult.success) {
        res.status(422).json({
          error: "Invalid review request payload.",
          details: parseResult.error.format(),
        });
        return;
      }

      const result = manager.submitReview(draftId, parseResult.data);
      res.json({
        status: "reviewed",
        draft: result.draft,
        audit_record: result.auditRecord,
        autonomy_safeguard: result.autonomy,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("not found")) {
        res.status(404).json({ error: msg });
        return;
      }
      next(err);
    }
  });


  // 7. Audit trail
  app.get("/api/audit", (req: Request, res: Response) => {
    const limit = parseInt((req.query.limit as string) || "100", 10);
    const audit = manager.getAuditTrail(limit);
    res.json({ audit, count: audit.length });
  });

  // 8. Feedback records
  app.get("/api/feedback", (_req: Request, res: Response) => {
    const feedback = manager.getFeedbackRecords();
    res.json({ feedback, count: feedback.length });
  });

  // 9. Autonomy safeguard statuses
  app.get("/api/autonomy", (_req: Request, res: Response) => {
    res.json({
      autonomy: manager.getAutonomyStatus(),
      rule: "Category becomes eligible for autonomy only after 20 consecutive approved, unchanged drafts. Any edit or rejection resets counter.",
    });
  });


  // Error handling middleware
  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    console.error("Unhandled error:", err);
    res.status(500).json({
      error: "Internal server error.",
      message: err instanceof Error ? err.message : String(err),
    });
  });

  return app;
}
