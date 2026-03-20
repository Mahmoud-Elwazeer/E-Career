/**
 * Media upload helpers — delegates to admin service.
 */
export { adminUploadMedia as uploadMedia, adminFetchMedia as fetchAllMedia, adminDeleteMedia as deleteMedia } from "@/services/admin";

export interface MediaItem {
  id: number;
  uuid: string;
  url: string;
  filename: string;
  size: number;
  mime_type: string;
  created_at: string;
}
