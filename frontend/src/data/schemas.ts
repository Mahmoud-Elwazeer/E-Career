import { z } from "zod";

// Source form validation schema
export const sourceFormSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  url: z.string().url("Must be a valid URL"),
  logoUrl: z.string().url("Must be a valid URL").optional().or(z.literal("")),
});

export type SourceFormValues = z.infer<typeof sourceFormSchema>;

// Job review schema (for admin moderation)
export const jobReviewSchema = z.object({
  status: z.enum(["approved", "rejected", "pending"]),
  notes: z.string().optional(),
});

export type JobReviewValues = z.infer<typeof jobReviewSchema>;
