import type { Project, Session, Synagogue } from "./session";

type LoginPayload = {
  access_token: string;
  user_id: string;
  role: Session["role"];
  synagogue_id: string | null;
};

export async function login(email: string, password: string): Promise<Session> {
  const payload = await request<LoginPayload>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return {
    accessToken: payload.access_token,
    userId: payload.user_id,
    role: payload.role,
    synagogueId: payload.synagogue_id,
  };
}

export async function listSynagogues(session: Session): Promise<Synagogue[]> {
  return request<Synagogue[]>("/api/synagogues", { headers: authHeaders(session) });
}

export async function createSynagogue(session: Session, name: string): Promise<Synagogue> {
  return request<Synagogue>("/api/synagogues", {
    method: "POST",
    headers: authHeaders(session),
    body: JSON.stringify({ name }),
  });
}

export async function listProjects(session: Session): Promise<Project[]> {
  const rows = await request<Array<{ id: string; synagogue_id: string; name: string }>>("/api/projects", {
    headers: authHeaders(session),
  });
  return rows.map((row) => ({ id: row.id, synagogueId: row.synagogue_id, name: row.name }));
}

export type Budget = {
  projectId: string;
  constructionCost: string;
  targetPercent: string;
  currency: string;
  targetAmount: string;
  dedicationsTotal: string;
  gap: string;
};

export type PlanPoint = { x: number; y: number };

export type PlanPaint = {
  kind: "brush" | "polygon";
  width: number;
  strokes: PlanPoint[][];
};

export type Dedication = {
  id: string;
  projectId: string;
  name: string;
  price: string;
  status: "open" | "fundraising" | "realized";
  marker: PlanPoint | null;
  region: PlanPaint | null;
};

export type PriceWeight = { dedicationId: string; weight: string };

export type PricingPreview = {
  targetAmount: string;
  amountToSplit: string;
  items: Array<{ dedicationId: string; name: string; currentPrice: string; suggestedPrice: string }>;
};

export async function placeMarker(session: Session, dedicationId: string, x: number, y: number): Promise<Dedication> {
  return toDedication(
    await request<DedicationPayload>(`/api/dedications/${dedicationId}/marker`, {
      method: "PUT",
      headers: authHeaders(session),
      body: JSON.stringify({ x: x.toFixed(2), y: y.toFixed(2) }),
    }),
  );
}

export async function removeMarker(session: Session, dedicationId: string): Promise<Dedication> {
  return toDedication(
    await request<DedicationPayload>(`/api/dedications/${dedicationId}/marker`, {
      method: "DELETE",
      headers: authHeaders(session),
    }),
  );
}

export async function paintRegion(session: Session, dedicationId: string, region: PlanPaint): Promise<Dedication> {
  return toDedication(
    await request<DedicationPayload>(`/api/dedications/${dedicationId}/region`, {
      method: "PUT",
      headers: authHeaders(session),
      body: JSON.stringify({
        kind: region.kind,
        width: region.width.toFixed(2),
        strokes: region.strokes.map((stroke) => stroke.map((point) => ({ x: point.x.toFixed(2), y: point.y.toFixed(2) }))),
      }),
    }),
  );
}

export async function previewPricing(session: Session, projectId: string, items: PriceWeight[]): Promise<PricingPreview> {
  const payload = await request<PricingPayload>(`/api/projects/${projectId}/pricing/preview`, {
    method: "POST",
    headers: authHeaders(session),
    body: JSON.stringify(pricingBody(items)),
  });
  return toPricing(payload);
}

export async function applyPricing(session: Session, projectId: string, items: PriceWeight[]): Promise<Dedication[]> {
  const rows = await request<DedicationPayload[]>(`/api/projects/${projectId}/pricing/apply`, {
    method: "POST",
    headers: authHeaders(session),
    body: JSON.stringify(pricingBody(items)),
  });
  return rows.map(toDedication);
}

function pricingBody(items: PriceWeight[]) {
  return { items: items.map((item) => ({ dedication_id: item.dedicationId, weight: item.weight })) };
}

type PricingPayload = {
  target_amount: string;
  amount_to_split: string;
  items: Array<{ dedication_id: string; name: string; current_price: string; suggested_price: string }>;
};

function toPricing(payload: PricingPayload): PricingPreview {
  return {
    targetAmount: payload.target_amount,
    amountToSplit: payload.amount_to_split,
    items: payload.items.map((item) => ({
      dedicationId: item.dedication_id,
      name: item.name,
      currentPrice: item.current_price,
      suggestedPrice: item.suggested_price,
    })),
  };
}

export async function getBudget(session: Session, projectId: string): Promise<Budget | null> {
  const response = await fetch(`/api/projects/${projectId}/budget`, { headers: authHeaders(session) });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
  return toBudget(await response.json());
}

export async function saveBudget(
  session: Session,
  projectId: string,
  constructionCost: string,
  targetPercent: string,
): Promise<Budget> {
  const payload = await request<BudgetPayload>(`/api/projects/${projectId}/budget`, {
    method: "PUT",
    headers: authHeaders(session),
    body: JSON.stringify({ construction_cost: constructionCost, target_percent: targetPercent }),
  });
  return toBudget(payload);
}

export async function listDedications(session: Session, projectId: string): Promise<Dedication[]> {
  const rows = await request<DedicationPayload[]>(`/api/projects/${projectId}/dedications`, {
    headers: authHeaders(session),
  });
  return rows.map(toDedication);
}

export async function createDedication(
  session: Session,
  projectId: string,
  name: string,
  price: string,
): Promise<Dedication> {
  return toDedication(
    await request<DedicationPayload>(`/api/projects/${projectId}/dedications`, {
      method: "POST",
      headers: authHeaders(session),
      body: JSON.stringify({ name, price }),
    }),
  );
}

export async function updateDedication(
  session: Session,
  dedicationId: string,
  change: { price?: string; status?: Dedication["status"] },
): Promise<Dedication> {
  return toDedication(
    await request<DedicationPayload>(`/api/dedications/${dedicationId}`, {
      method: "PATCH",
      headers: authHeaders(session),
      body: JSON.stringify(change),
    }),
  );
}

export type CalculatorSettings = {
  minMonthly: string;
  maxMonthly: string;
  maxMonths: number;
  minPerDonor: string;
  maxPerDonor: string;
  minDonors: number;
  currency: string;
};

export type Simulation = {
  dedicationId: string;
  monthlyAmount: string;
  months: number;
  donorCount: number;
  monthlyWithinRange: boolean;
  termWithinLimit: boolean;
  donorsMeetMinimum: boolean;
  financedTotal: string | null;
  status: "awaiting_rate_table";
};

export type Proposal = {
  id: string;
  dedicationId: string;
  monthlyAmount: string;
  months: number;
  donorCount: number;
  currency: string;
  financedTotal: string | null;
  status: "awaiting_rate_table";
  createdAt: string;
};

export async function getCalculatorSettings(session: Session, projectId: string): Promise<CalculatorSettings> {
  return toSettings(
    await request<SettingsPayload>(`/api/projects/${projectId}/calculator-settings`, { headers: authHeaders(session) }),
  );
}

export async function saveCalculatorSettings(
  session: Session,
  projectId: string,
  settings: CalculatorSettings,
): Promise<CalculatorSettings> {
  return toSettings(
    await request<SettingsPayload>(`/api/projects/${projectId}/calculator-settings`, {
      method: "PUT",
      headers: authHeaders(session),
      body: JSON.stringify(settingsBody(settings)),
    }),
  );
}

export async function previewSimulation(
  session: Session,
  projectId: string,
  draft: SimulationDraft,
): Promise<Simulation> {
  return toSimulation(
    await request<SimulationPayload>(`/api/projects/${projectId}/calculator/preview`, {
      method: "POST",
      headers: authHeaders(session),
      body: JSON.stringify(draftBody(draft)),
    }),
  );
}

export async function createProposal(session: Session, projectId: string, draft: SimulationDraft): Promise<Proposal> {
  return toProposal(
    await request<ProposalPayload>(`/api/projects/${projectId}/proposals`, {
      method: "POST",
      headers: authHeaders(session),
      body: JSON.stringify(draftBody(draft)),
    }),
  );
}

export async function updateProposal(session: Session, proposalId: string, draft: SimulationDraft): Promise<Proposal> {
  return toProposal(
    await request<ProposalPayload>(`/api/proposals/${proposalId}`, {
      method: "PATCH",
      headers: authHeaders(session),
      body: JSON.stringify(draftBody(draft)),
    }),
  );
}

export async function deleteProposal(session: Session, proposalId: string): Promise<void> {
  const response = await fetch(`/api/proposals/${proposalId}`, {
    method: "DELETE",
    headers: authHeaders(session),
  });
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
}

export async function listProposals(session: Session, projectId: string): Promise<Proposal[]> {
  const rows = await request<ProposalPayload[]>(`/api/projects/${projectId}/proposals`, {
    headers: authHeaders(session),
  });
  return rows.map(toProposal);
}

export type LeadStatus = "new" | "in_meeting" | "proposal" | "won" | "lost";

export type Lead = {
  id: string;
  kind: "donor" | "synagogue_customer";
  name: string;
  phone: string;
  status: LeadStatus;
  projectId: string | null;
  dedicationId: string | null;
  assigneeId: string | null;
  requestedSynagogueName: string | null;
};

export type Meeting = {
  id: string;
  leadId: string;
  scheduledAt: string;
  note: string;
  closeChance: string | null;
};

export type Contractor = {
  dedicationId: string;
  name: string;
  phone: string;
  amount: string;
};

export type Assignee = { userId: string; email: string };

export async function listAssignees(session: Session, projectId: string): Promise<Assignee[]> {
  const rows = await request<Array<{ user_id: string; email: string }>>(
    `/api/projects/${projectId}/assignees`,
    { headers: authHeaders(session) },
  );
  return rows.map((row) => ({ userId: row.user_id, email: row.email }));
}

export async function listDonorLeads(session: Session, projectId: string): Promise<Lead[]> {
  const rows = await request<LeadPayload[]>(`/api/projects/${projectId}/leads`, { headers: authHeaders(session) });
  return rows.map(toLead);
}

export async function createDonorLead(
  session: Session,
  projectId: string,
  draft: { name: string; phone: string; dedicationId: string; assigneeId: string },
): Promise<Lead> {
  return toLead(
    await request<LeadPayload>(`/api/projects/${projectId}/leads`, {
      method: "POST",
      headers: authHeaders(session),
      body: JSON.stringify(donorBody(draft)),
    }),
  );
}

export async function listCustomerLeads(session: Session): Promise<Lead[]> {
  const rows = await request<LeadPayload[]>("/api/customer-leads", { headers: authHeaders(session) });
  return rows.map(toLead);
}

export async function createCustomerLead(
  session: Session,
  name: string,
  phone: string,
  requestedSynagogueName: string,
): Promise<Lead> {
  return toLead(
    await request<LeadPayload>("/api/customer-leads", {
      method: "POST",
      headers: authHeaders(session),
      body: JSON.stringify({ name, phone, requested_synagogue_name: requestedSynagogueName }),
    }),
  );
}

export async function updateLead(session: Session, leadId: string, status: LeadStatus): Promise<Lead> {
  return toLead(
    await request<LeadPayload>(`/api/leads/${leadId}`, {
      method: "PATCH",
      headers: authHeaders(session),
      body: JSON.stringify({ status }),
    }),
  );
}

export async function listMeetings(session: Session, leadId: string): Promise<Meeting[]> {
  const rows = await request<MeetingPayload[]>(`/api/leads/${leadId}/meetings`, { headers: authHeaders(session) });
  return rows.map(toMeeting);
}

export async function createMeeting(
  session: Session,
  leadId: string,
  scheduledAt: string,
  note: string,
  closeChance: string,
): Promise<Meeting> {
  return toMeeting(
    await request<MeetingPayload>(`/api/leads/${leadId}/meetings`, {
      method: "POST",
      headers: authHeaders(session),
      body: JSON.stringify({
        scheduled_at: new Date(scheduledAt).toISOString(),
        note,
        close_chance: closeChance === "" ? null : closeChance,
      }),
    }),
  );
}

export async function getContractor(session: Session, dedicationId: string): Promise<Contractor | null> {
  const response = await fetch(`/api/dedications/${dedicationId}/contractor`, { headers: authHeaders(session) });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
  return toContractor(await response.json());
}

export async function saveContractor(
  session: Session,
  dedicationId: string,
  draft: { name: string; phone: string; amount: string },
): Promise<Contractor> {
  return toContractor(
    await request<ContractorPayload>(`/api/dedications/${dedicationId}/contractor`, {
      method: "PUT",
      headers: authHeaders(session),
      body: JSON.stringify(draft),
    }),
  );
}

export type SimulationDraft = {
  dedicationId: string;
  monthlyAmount: string;
  months: number;
  donorCount: number;
};

export async function createProject(session: Session, synagogueId: string, name: string): Promise<Project> {
  const row = await request<{ id: string; synagogue_id: string; name: string }>("/api/projects", {
    method: "POST",
    headers: authHeaders(session),
    body: JSON.stringify({ synagogue_id: synagogueId, name }),
  });
  return { id: row.id, synagogueId: row.synagogue_id, name: row.name };
}

export async function fetchPlan(session: Session, projectId: string): Promise<string | null> {
  return fetchImage(session, `/api/projects/${projectId}/plan`);
}

export async function fetchImage(session: Session, path: string): Promise<string | null> {
  const response = await fetch(path, { headers: authHeaders(session) });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
  return URL.createObjectURL(await response.blob());
}

export type PublicPageSettings = { projectId: string; slug: string; vision: string; enabled: boolean };

export async function getPublicPageSettings(session: Session, projectId: string): Promise<PublicPageSettings | null> {
  const response = await fetch(`/api/projects/${projectId}/public-page`, { headers: authHeaders(session) });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
  return toPublicSettings(await response.json());
}

export async function savePublicPageSettings(
  session: Session,
  projectId: string,
  draft: { slug: string; vision: string; enabled: boolean },
): Promise<PublicPageSettings> {
  return toPublicSettings(
    await request<PublicSettingsPayload>(`/api/projects/${projectId}/public-page`, {
      method: "PUT",
      headers: authHeaders(session),
      body: JSON.stringify(draft),
    }),
  );
}

export async function listGallery(session: Session, projectId: string): Promise<string[]> {
  const rows = await request<Array<{ id: string }>>(`/api/projects/${projectId}/gallery`, {
    headers: authHeaders(session),
  });
  return rows.map((row) => row.id);
}

export async function uploadGalleryImage(session: Session, projectId: string, file: File): Promise<void> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`/api/projects/${projectId}/gallery`, {
    method: "POST",
    headers: authHeaders(session),
    body,
  });
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
}

export async function deleteGalleryImage(session: Session, imageId: string): Promise<void> {
  const response = await fetch(`/api/gallery/${imageId}`, { method: "DELETE", headers: authHeaders(session) });
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
}

export type PublicProject = {
  slug: string;
  projectName: string;
  synagogueName: string;
  vision: string;
  currency: string;
  hasPlan: boolean;
  galleryImageIds: string[];
  dedications: Dedication[];
};

export async function fetchPublicProject(slug: string): Promise<PublicProject | null> {
  const response = await fetch(`/api/public/${encodeURIComponent(slug)}`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
  return toPublicProject(await response.json());
}

export function publicPlanUrl(slug: string): string {
  return `/api/public/${encodeURIComponent(slug)}/plan`;
}

export function publicGalleryUrl(slug: string, imageId: string): string {
  return `/api/public/${encodeURIComponent(slug)}/gallery/${imageId}`;
}

export async function submitPublicContact(
  slug: string,
  draft: { name: string; phone: string; synagogueName: string },
): Promise<void> {
  const response = await fetch(`/api/public/${encodeURIComponent(slug)}/contact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: draft.name, phone: draft.phone, synagogue_name: draft.synagogueName }),
  });
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
}

type PublicSettingsPayload = { project_id: string; slug: string; vision: string; enabled: boolean };

function toPublicSettings(payload: PublicSettingsPayload): PublicPageSettings {
  return { projectId: payload.project_id, slug: payload.slug, vision: payload.vision, enabled: payload.enabled };
}

type PublicProjectPayload = {
  slug: string;
  project_name: string;
  synagogue_name: string;
  vision: string;
  currency: string;
  has_plan: boolean;
  gallery_image_ids: string[];
  dedications: Array<Omit<DedicationPayload, "project_id">>;
};

function toPublicProject(payload: PublicProjectPayload): PublicProject {
  return {
    slug: payload.slug,
    projectName: payload.project_name,
    synagogueName: payload.synagogue_name,
    vision: payload.vision,
    currency: payload.currency,
    hasPlan: payload.has_plan,
    galleryImageIds: payload.gallery_image_ids,
    dedications: payload.dedications.map((row) => toDedication({ ...row, project_id: "" })),
  };
}

export async function uploadPlan(session: Session, projectId: string, file: File): Promise<void> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`/api/projects/${projectId}/plan`, {
    method: "PUT",
    headers: authHeaders(session),
    body,
  });
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
}

function authHeaders(session: Session): HeadersInit {
  return { Authorization: `Bearer ${session.accessToken}` };
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, headers: jsonHeaders(init.headers) });
  if (!response.ok) {
    throw new Error(await messageFrom(response));
  }
  return (await response.json()) as T;
}

async function messageFrom(response: Response): Promise<string> {
  if (response.status !== 422) {
    return messageForStatus(response.status);
  }
  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  return hebrewValidation(typeof body?.detail === "string" ? body.detail : "");
}

function hebrewValidation(detail: string): string {
  if (detail.includes("wall")) {
    return "לחצו בתוך חדר, לא על קיר.";
  }
  if (detail.includes("too large")) {
    return "האזור גדול מדי. לחצו בתוך חדר או על האובייקט.";
  }
  if (detail.includes("could not be read")) {
    return "לא ניתן לקרוא את התוכנית.";
  }
  return "הנתונים אינם תקינים";
}

function jsonHeaders(headers: HeadersInit | undefined): HeadersInit {
  return { "Content-Type": "application/json", ...headers };
}

function messageForStatus(status: number): string {
  if (status === 401) {
    return "דואר או סיסמה שגויים";
  }
  if (status === 403) {
    return "אין הרשאה לפעולה זו";
  }
  if (status === 409) {
    return "הרשומה כבר קיימת";
  }
  if (status === 422) {
    return "הנתונים אינם תקינים";
  }
  return "הפעולה נכשלה";
}

type BudgetPayload = {
  project_id: string;
  construction_cost: string;
  target_percent: string;
  currency: string;
  target_amount: string;
  dedications_total: string;
  gap: string;
};

type DedicationPayload = {
  id: string;
  project_id: string;
  name: string;
  price: string;
  status: Dedication["status"];
  plan_x: string | null;
  plan_y: string | null;
  plan_region: {
    kind: "brush" | "polygon";
    width: string;
    strokes: Array<Array<{ x: string; y: string }>>;
  } | null;
};

function toBudget(payload: BudgetPayload): Budget {
  return {
    projectId: payload.project_id,
    constructionCost: payload.construction_cost,
    targetPercent: payload.target_percent,
    currency: payload.currency,
    targetAmount: payload.target_amount,
    dedicationsTotal: payload.dedications_total,
    gap: payload.gap,
  };
}

function toDedication(payload: DedicationPayload): Dedication {
  return {
    id: payload.id,
    projectId: payload.project_id,
    name: payload.name,
    price: payload.price,
    status: payload.status,
    marker: payload.plan_x === null || payload.plan_y === null
      ? null
      : { x: Number(payload.plan_x), y: Number(payload.plan_y) },
    region: toRegion(payload.plan_region),
  };
}

function toRegion(raw: DedicationPayload["plan_region"]): PlanPaint | null {
  if (raw === null || raw === undefined) {
    return null;
  }
  if (Array.isArray(raw)) {
    return null;
  }
  return {
    kind: raw.kind === "polygon" ? "polygon" : "brush",
    width: Number(raw.width),
    strokes: raw.strokes.map((stroke) => stroke.map((point) => ({ x: Number(point.x), y: Number(point.y) }))),
  };
}

type SettingsPayload = {
  min_monthly: string;
  max_monthly: string;
  max_months: number;
  min_per_donor: string;
  max_per_donor: string;
  min_donors: number;
  currency: string;
};

type SimulationPayload = {
  dedication_id: string;
  monthly_amount: string;
  months: number;
  donor_count: number;
  monthly_within_range: boolean;
  term_within_limit: boolean;
  donors_meet_minimum: boolean;
  financed_total: string | null;
  status: Simulation["status"];
};

type ProposalPayload = SimulationPayload & {
  id: string;
  currency: string;
  created_at: string;
};

function toSettings(payload: SettingsPayload): CalculatorSettings {
  return {
    minMonthly: payload.min_monthly,
    maxMonthly: payload.max_monthly,
    maxMonths: payload.max_months,
    minPerDonor: payload.min_per_donor,
    maxPerDonor: payload.max_per_donor,
    minDonors: payload.min_donors,
    currency: payload.currency,
  };
}

function settingsBody(settings: CalculatorSettings) {
  return {
    min_monthly: settings.minMonthly,
    max_monthly: settings.maxMonthly,
    max_months: settings.maxMonths,
    min_per_donor: settings.minPerDonor,
    max_per_donor: settings.maxPerDonor,
    min_donors: settings.minDonors,
  };
}

function draftBody(draft: SimulationDraft) {
  return {
    dedication_id: draft.dedicationId,
    monthly_amount: draft.monthlyAmount,
    months: draft.months,
    donor_count: draft.donorCount,
  };
}

function toSimulation(payload: SimulationPayload): Simulation {
  return {
    dedicationId: payload.dedication_id,
    monthlyAmount: payload.monthly_amount,
    months: payload.months,
    donorCount: payload.donor_count,
    monthlyWithinRange: payload.monthly_within_range,
    termWithinLimit: payload.term_within_limit,
    donorsMeetMinimum: payload.donors_meet_minimum,
    financedTotal: payload.financed_total,
    status: payload.status,
  };
}

function toProposal(payload: ProposalPayload): Proposal {
  return { ...toSimulation(payload), id: payload.id, currency: payload.currency, createdAt: payload.created_at };
}

type LeadPayload = {
  id: string;
  kind: Lead["kind"];
  name: string;
  phone: string;
  status: LeadStatus;
  project_id: string | null;
  dedication_id: string | null;
  assignee_id: string | null;
  requested_synagogue_name: string | null;
};

type MeetingPayload = {
  id: string;
  lead_id: string;
  scheduled_at: string;
  note: string;
  close_chance: string | null;
};

type ContractorPayload = {
  dedication_id: string;
  name: string;
  phone: string;
  amount: string;
};

function donorBody(draft: { name: string; phone: string; dedicationId: string; assigneeId: string }) {
  return {
    name: draft.name,
    phone: draft.phone,
    dedication_id: draft.dedicationId || null,
    assignee_id: draft.assigneeId || null,
  };
}

function toLead(payload: LeadPayload): Lead {
  return {
    id: payload.id,
    kind: payload.kind,
    name: payload.name,
    phone: payload.phone,
    status: payload.status,
    projectId: payload.project_id,
    dedicationId: payload.dedication_id,
    assigneeId: payload.assignee_id,
    requestedSynagogueName: payload.requested_synagogue_name,
  };
}

function toMeeting(payload: MeetingPayload): Meeting {
  return {
    id: payload.id,
    leadId: payload.lead_id,
    scheduledAt: payload.scheduled_at,
    note: payload.note,
    closeChance: payload.close_chance,
  };
}

function toContractor(payload: ContractorPayload): Contractor {
  return { dedicationId: payload.dedication_id, name: payload.name, phone: payload.phone, amount: payload.amount };
}
