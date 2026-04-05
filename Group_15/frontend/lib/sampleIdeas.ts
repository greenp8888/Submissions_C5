/**
 * Curated “Try an example” prompts — used when the LLM-backed /api/ideas
 * route is unavailable (no API key, network/upstream errors) or returns nothing.
 */
export const DEFAULT_SAMPLE_IDEAS: { prompt: string; tag: string }[] = [
  {
    tag: "B2B SAAS",
    prompt:
      "AI copilot for support teams that drafts replies from past tickets, help docs, and CRM context, with human review before send.",
  },
  {
    tag: "MOBILE",
    prompt:
      "Micro-learning app for busy parents: five-minute daily lessons on child development, paired with printable activity ideas.",
  },
  {
    tag: "MARKETPLACE",
    prompt:
      "Two-sided marketplace connecting small commercial kitchens with food truck operators who need prep space and licensed facilities.",
  },
  {
    tag: "DEVTOOL",
    prompt:
      "CLI and dashboard that scans Terraform and Kubernetes configs for misconfigurations, drift, and cost-heavy resources before deploy.",
  },
];
