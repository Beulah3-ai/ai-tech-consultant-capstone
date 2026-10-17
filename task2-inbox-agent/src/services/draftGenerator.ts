import { CustomerEmail, SuggestedDraft } from "../types.js";
import { ClassificationResult } from "./classifier.js";
import { KnowledgeBrainClient } from "../client/knowledgeBrainClient.js";

export class DraftGenerator {
  constructor(private kbClient: KnowledgeBrainClient) {}

  async generateDraft(
    email: CustomerEmail,
    classification: ClassificationResult,
    providerOverride?: string
  ): Promise<SuggestedDraft> {
    const now = new Date().toISOString();

    // 1. Explicit abstention for out-of-scope inquiries
    if (classification.category === "out_of_scope") {
      return {
        id: `draft_${email.id}`,
        email_id: email.id,
        sender: email.sender,
        subject: email.subject,
        body: email.body,
        category: "out_of_scope",
        priority: "low",
        confidence: 0.95,
        suggested_reply:
          "Hello,\n\nThank you for contacting our consulting team. It appears your inquiry falls outside the scope of our directory platform technical documentation and support services. We specialize in directory architecture, member onboarding, and platform configurations.\n\nIf you have a question regarding your directory software, please let us know and we will be glad to assist!\n\nBest regards,\nTechnical Consultant Support",
        sources: [],
        answered: false,
        needs_escalation: false,
        provider: "policy_guardrail",
        is_mock: false,
        disclaimer: "Out-of-scope query identified by safeguard rules; polite refusal generated without calling knowledge base.",
        status: "pending_review",
        created_at: now,
      };
    }

    // 2. Query Knowledge Brain for grounded technical information
    const kbResult = await this.kbClient.query(email.body, providerOverride);

    // 3. Handle Knowledge Brain network/server failures
    if (!kbResult.success || !kbResult.data) {
      return {
        id: `draft_${email.id}`,
        email_id: email.id,
        sender: email.sender,
        subject: email.subject,
        body: email.body,
        category: classification.category,
        priority: classification.priority,
        confidence: 0.0,
        suggested_reply:
          "Hello,\n\nThank you for contacting technical support. Our knowledge retrieval engine is currently undergoing maintenance. Your inquiry has been prioritized and routed to a human specialist for manual investigation.\n\nBest regards,\nTechnical Consultant Support",
        sources: [],
        answered: false,
        needs_escalation: true,
        provider: "system_fallback",
        is_mock: false,
        disclaimer: `Knowledge retrieval error: ${kbResult.error || "Service unavailable"}. Safely escalated for human review.`,
        status: "pending_review",
        created_at: now,
      };
    }

    const kbData = kbResult.data;

    // 4. Grounded answer when Knowledge Brain found verified documentation
    if (kbData.answered) {
      const formattedSources = kbData.sources.length > 0
        ? `\n\nReferenced Documentation:\n${kbData.sources.map(s => `- ${s}`).join("\n")}`
        : "";

      return {
        id: `draft_${email.id}`,
        email_id: email.id,
        sender: email.sender,
        subject: email.subject,
        body: email.body,
        category: classification.category,
        priority: classification.priority,
        confidence: kbData.confidence,
        suggested_reply:
          `Hello,\n\nThank you for reaching out. Here is the verified technical guidance for your question:\n\n${kbData.answer}${formattedSources}\n\nPlease let us know if you need any additional assistance!\n\nBest regards,\nTechnical Consultant Support`,
        sources: kbData.sources,
        answered: true,
        needs_escalation: false,
        provider: kbData.provider,
        is_mock: kbData.is_mock,
        disclaimer: kbData.disclaimer,
        status: "pending_review",
        created_at: now,
      };
    }

    // 5. Explicit abstention & escalation when Knowledge Brain has insufficient evidence
    return {
      id: `draft_${email.id}`,
      email_id: email.id,
      sender: email.sender,
      subject: email.subject,
      body: email.body,
      category: classification.category,
      priority: classification.priority,
      confidence: 0.0,
      suggested_reply:
        "Hello,\n\nThank you for contacting support. We have searched our platform technical documentation, but there is currently insufficient verified evidence to resolve your specific inquiry automatically. We have escalated this ticket to a senior technical consultant who will follow up with you directly.\n\nBest regards,\nTechnical Consultant Support",
      sources: [],
      answered: false,
      needs_escalation: true,
      provider: kbData.provider,
      is_mock: kbData.is_mock,
      disclaimer: "Knowledge Brain abstained due to insufficient evidence. Ticket flagged for human consultant escalation.",
      status: "pending_review",
      created_at: now,
    };
  }
}
