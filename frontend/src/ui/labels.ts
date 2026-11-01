import type { Role } from "../session";

export const roleLabels: Record<Role, string> = {
  platform_admin: "מנהל הפלטפורמה",
  lead_projector: "פרויקטור ראשי",
  sub_projector: "תת-פרויקטור",
};

export const statusLabels = {
  open: "פתוח לגיוס",
  fundraising: "בגיוס מתקדם",
  realized: "תוקצב ומומש",
} as const;

export const leadStatusLabels = {
  new: "חדש",
  in_meeting: "בפגישה",
  proposal: "הצעה נשלחה",
  won: "נסגר",
  lost: "לא המשיך",
} as const;
