import { EmailCategory, Priority } from "../types.js";

export interface ClassificationResult {
  category: EmailCategory;
  priority: Priority;
  confidence: number;
  matchedKeywords: string[];
}

const CATEGORY_KEYWORDS: Record<EmailCategory, string[]> = {
  technical_support: [
    "dns", "a-record", "a record", "cname", "ssl", "certificate", "500", "error",
    "outage", "webhook", "api", "redirect", "cache", "pagination", "duplicate",
    "maps", "geocoding", "crash", "bug", "latency", "subdomain"
  ],
  billing: [
    "stripe", "payment", "gateway", "invoice", "receipt", "charge", "refund",
    "subscription", "credit card", "billed", "duplicate charge", "vat", "tax exempt",
    "annual", "discount", "prorated", "cancel", "checkout"
  ],
  onboarding: [
    "import", "csv", "template", "wizard", "checklist", "categories", "specialty",
    "tier", "tiers", "first time", "launch", "signup form", "custom fields",
    "radius", "kilometers", "miles", "welcome email", "approval"
  ],
  feature_requests: [
    "feature request", "roadmap", "zapier", "make", "mobile app", "ios", "android",
    "multi-currency", "eur", "gbp", "dark mode", "whatsapp", "calendar booking",
    "messaging", "gamification", "badges", "translation"
  ],
  account_configuration: [
    "sub-admin", "permission", "permissions", "notification email", "contact email",
    "timezone", "est", "utc", "session timeout", "recaptcha", "meta description",
    "browser title", "2fa", "two-factor", "billing address", "audit log", "gdpr"
  ],
  out_of_scope: [
    "sourdough", "starter", "fermentation", "honda", "civic", "transmission",
    "torque converter", "investment", "portfolio", "roth ira", "dog food",
    "golden retriever", "faucet", "moen", "tomatoes", "grow bags", "capital gains",
    "rental property", "espresso", "barista", "breville", "subaru", "ball joints"
  ],
};

const URGENT_TRIGGERS = [
  "urgent", "critical", "emergency", "outage", "down", "500 internal server error",
  "failing for all", "entire site", "broken for everyone"
];

const HIGH_PRIORITY_TRIGGERS = [
  "duplicate charge", "refund immediately", "payment failing", "checkout",
  "ssl pending", "redirect loop", "403 forbidden", "quota exceeded"
];

export class EmailClassifier {
  classify(subject: string, body: string): ClassificationResult {
    const text = `${subject} ${body}`.toLowerCase();

    // Check for out-of-scope triggers first
    const outOfScopeMatches = this.findMatches(text, CATEGORY_KEYWORDS.out_of_scope);
    if (outOfScopeMatches.length >= 1) {
      return {
        category: "out_of_scope",
        priority: "low",
        confidence: 0.95,
        matchedKeywords: outOfScopeMatches,
      };
    }

    // Score all categories
    let bestCategory: EmailCategory = "technical_support";
    let maxMatches = -1;
    let bestMatches: string[] = [];

    const categories: EmailCategory[] = [
      "technical_support",
      "billing",
      "onboarding",
      "feature_requests",
      "account_configuration",
    ];

    for (const cat of categories) {
      const matches = this.findMatches(text, CATEGORY_KEYWORDS[cat]);
      if (matches.length > maxMatches) {
        maxMatches = matches.length;
        bestCategory = cat;
        bestMatches = matches;
      }
    }

    // Determine priority
    let priority: Priority = "medium";
    if (URGENT_TRIGGERS.some(trigger => text.includes(trigger))) {
      priority = "urgent";
    } else if (HIGH_PRIORITY_TRIGGERS.some(trigger => text.includes(trigger)) || bestCategory === "billing") {
      priority = "high";
    } else if (bestCategory === "feature_requests" || bestCategory === "out_of_scope") {
      priority = "low";
    }

    // Determine confidence
    let confidence = 0.70;
    if (maxMatches >= 3) {
      confidence = 0.95;
    } else if (maxMatches >= 2) {
      confidence = 0.88;
    } else if (maxMatches === 1) {
      confidence = 0.78;
    }

    return {
      category: bestCategory,
      priority,
      confidence,
      matchedKeywords: bestMatches,
    };
  }

  private findMatches(text: string, keywords: string[]): string[] {
    return keywords.filter(kw => text.includes(kw));
  }
}
