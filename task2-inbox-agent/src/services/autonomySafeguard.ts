import { EmailCategory, ReviewAction, AutonomyStatus } from "../types.js";

const AUTONOMY_THRESHOLD = 20;

export interface DecisionResult {
  qualifies: boolean;
  consecutive_approved_count: number;
  is_eligible: boolean;
  reset_reason?: string;
}

export class AutonomySafeguardTracker {
  private state: Record<EmailCategory, AutonomyStatus>;

  constructor(initialState?: Partial<Record<EmailCategory, AutonomyStatus>>) {
    const categories: EmailCategory[] = [
      "technical_support",
      "billing",
      "onboarding",
      "feature_requests",
      "account_configuration",
      "out_of_scope",
    ];

    const now = new Date().toISOString();
    this.state = {} as Record<EmailCategory, AutonomyStatus>;

    for (const cat of categories) {
      this.state[cat] = initialState?.[cat] || {
        category: cat,
        consecutive_approved_count: 0,
        target_threshold: AUTONOMY_THRESHOLD,
        is_eligible: false,
        last_reset_reason: undefined,
        last_updated: now,
      };
    }
  }

  recordDecision(
    category: EmailCategory,
    action: ReviewAction,
    diffDetected: boolean
  ): DecisionResult {
    const current = this.state[category];
    const now = new Date().toISOString();

    // Only approved drafts with ZERO reviewer modifications qualify
    if (action === "approve" && !diffDetected) {
      current.consecutive_approved_count += 1;
      current.last_updated = now;
      current.last_reset_reason = undefined;

      if (current.consecutive_approved_count >= AUTONOMY_THRESHOLD) {
        current.is_eligible = true;
      }

      return {
        qualifies: true,
        consecutive_approved_count: current.consecutive_approved_count,
        is_eligible: current.is_eligible,
      };
    }

    // Any edit, rejection, escalation, or modification breaks the streak and resets the count
    let resetReason = "Draft failed qualifying criteria.";
    if (diffDetected || action === "edit_and_approve") {
      resetReason = "Reviewer modified the suggested draft.";
    } else if (action === "reject") {
      resetReason = "Reviewer rejected the suggested draft.";
    } else if (action === "escalate") {
      resetReason = "Ticket was escalated for human specialist resolution.";
    }

    current.consecutive_approved_count = 0;
    current.is_eligible = false;
    current.last_reset_reason = resetReason;
    current.last_updated = now;

    return {
      qualifies: false,
      consecutive_approved_count: 0,
      is_eligible: false,
      reset_reason: resetReason,
    };
  }

  getStatus(category?: EmailCategory): AutonomyStatus[] {
    if (category) {
      return [this.state[category]];
    }
    return Object.values(this.state);
  }

  getStateSnapshot(): Record<EmailCategory, AutonomyStatus> {
    return JSON.parse(JSON.stringify(this.state));
  }

  loadStateSnapshot(snapshot: Record<EmailCategory, AutonomyStatus>): void {
    if (snapshot && typeof snapshot === "object") {
      for (const [key, val] of Object.entries(snapshot)) {
        if (this.state[key as EmailCategory]) {
          this.state[key as EmailCategory] = { ...val };
        }
      }
    }
  }
}

