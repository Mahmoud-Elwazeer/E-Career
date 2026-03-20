/**
 * Legacy admin-api.ts shim — delegates to src/services/admin.ts
 */
export {
  adminCreateJob,
  adminUpdateJob,
  adminDeleteJob,
  adminPublishJob,
  adminArchiveJob,
  adminFetchAllCompanies,
  adminCreateCompany,
  adminUpdateCompany,
  adminDeleteCompany,
  adminFetchAllSources,
  adminCreateSource,
  adminUpdateSource,
  adminDeleteSource,
  adminFetchAllTags,
  adminCreateTag,
  adminDeleteTag,
  adminCsvImport,
  fetchClickAnalytics,
  fetchSearchAnalytics,
  fetchConversionAnalytics,
  fetchActivityLogs,
} from "@/services/admin";
