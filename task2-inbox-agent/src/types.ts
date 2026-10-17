import { z } from "zod";

export const EmailCategorySchema = z.enum([
  "technical_support",
  "billing",
  "onboarding",
  "feature_requests",
  "account_configuration",
  "out_of_scope",
]);
export type EmailCategory = z.infer<typeof EmailCategorySchema>;

export const PrioritySchema = z.enum(["urgent", "high", "medium", "low"]);
export type Priority = z.infer<typeof PrioritySchema>;

export const ReviewActionSchema = z.enum([
  "approve",
  "edit_and_approve",
  "reject",
  "escalate",
]);
export type ReviewAction = z.infer<typeof ReviewActionSchema>;

export const DraftStatusSchema = z.enum([
  "pending_review",
  "approved",
  "edited",
  "rejected",
  "escalated",
]);
export type DraftStatus = z.infer<typeof DraftStatusSchema>;

export const FeedbackRatingSchema = z.enum([
  "accurate_and_grounded",
  "minor_edits_needed",
  "inaccurate_facts",
  "unhelpful",
  "policy_correct",
]);
export type FeedbackRating = z.infer<typeof FeedbackRatingSchema>;

export const CustomerEmailSchema = z.object({
  id: z.string(),
  synthetic: z.literal(true),
  sender: z.string(),
  subject: z.string(),
  body: z.string(),
  received_at: z.string(),
  expected_category: EmailCategorySchema.optional(),
});
export type CustomerEmail = z.infer<typeof CustomerEmailSchema>;

export const SuggestedDraftSchema = z.object({
  id: z.string(),
  email_id: z.string(),
  sender: z.string(),
  subject: z.string(),
  body: z.string(),
  category: EmailCategorySchema,
  priority: PrioritySchema,
  confidence: z.number().min(0).max(1),
  suggested_reply: z.string(),
  sources: z.array(z.string()),
  answered: z.boolean(),
  needs_escalation: z.boolean(),
  provider: z.string(),
  is_mock: z.boolean(),
  disclaimer: z.string(),
  status: DraftStatusSchema,
  created_at: z.string(),
  reviewed_at: z.string().optional(),
  reviewer_id: z.string().optional(),
  final_reply: z.string().optional(),
  notes: z.string().optional(),
  feedback_rating: FeedbackRatingSchema.optional(),
  feedback_tags: z.array(z.string()).optional(),
});
export type SuggestedDraft = z.infer<typeof SuggestedDraftSchema>;

export const ReviewRequestSchema = z.object({
  action: ReviewActionSchema,
  reviewer_id: z.string().trim().min(1, "Reviewer ID is required"),
  final_reply: z.string().optional(),
  notes: z.string().optional(),
  feedback_rating: FeedbackRatingSchema.optional(),
  feedback_tags: z.array(z.string()).optional(),
});
export type ReviewRequest = z.infer<typeof ReviewRequestSchema>;

export const AuditRecordSchema = z.object({
  id: z.string(),
  email_id: z.string(),
  action: ReviewActionSchema,
  category: EmailCategorySchema,
  reviewer_id: z.string(),
  timestamp: z.string(),
  diff_detected: z.boolean(),
  qualifies_for_autonomy: z.boolean(),
  consecutive_approved_count: z.number(),
  autonomy_eligible: z.boolean(),
  notes: z.string().optional(),
  feedback_rating: FeedbackRatingSchema.optional(),
  feedback_tags: z.array(z.string()).optional(),
});
export type AuditRecord = z.infer<typeof AuditRecordSchema>;

export const AutonomyStatusSchema = z.object({
  category: EmailCategorySchema,
  consecutive_approved_count: z.number(),
  target_threshold: z.number().default(20),
  is_eligible: z.boolean(),
  last_reset_reason: z.string().optional(),
  last_updated: z.string(),
});
export type AutonomyStatus = z.infer<typeof AutonomyStatusSchema>;

export interface KnowledgeBrainQueryResponse {
  query: string;
  answer: string;
  answered: boolean;
  confidence: number;
  provider: string;
  is_mock: boolean;
  sources: string[];
  disclaimer: string;
}
