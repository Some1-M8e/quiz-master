import { z } from "zod";

export const participantSchema = z.object({
  name: z.string().min(2, "Name muss mindestens 2 Zeichen lang sein").max(100, "Name ist zu lang"),
  email: z.string().email("Ungültige E-Mail-Adresse"),
});

export const rsvpSchema = z.object({
  response: z.enum(["yes", "no", "maybe"]),
  companions: z.number().int().min(0).max(1, "Max. 1 Begleitung"),
});

export const providerSchema = z.object({
  name: z.string().min(2, "Name muss mindestens 2 Zeichen lang sein"),
  url: z.string().url("Ungültige URL"),
});
