import { useState, useEffect, useRef } from "react";
import { Upload, Trash2, Loader2, ImageIcon, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";
import { adminFetchMedia, adminUploadMedia, adminDeleteMedia } from "@/services/admin";

interface MediaItem {
  uuid: string;
  filename: string;
  url: string;
  size: number;
  mime_type: string;
  created_at: string;
}

export function AdminMediaManager() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoading(true);
    try { setItems(await adminFetchMedia()); }
    catch { setItems([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await adminUploadMedia(file);
      toast({ title: isAr ? "تم رفع الملف" : "File uploaded" });
      load();
    } catch (err: any) {
      toast({ title: "Upload failed", description: err?.message, variant: "destructive" });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDelete = async (uuid: string) => {
    try {
      await adminDeleteMedia(uuid);
      toast({ title: isAr ? "تم الحذف" : "Deleted" });
      load();
    } catch {
      toast({ title: "Failed", variant: "destructive" });
    }
  };

  const copyUrl = (url: string, id: string) => {
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-body font-medium">{isAr ? "إدارة الوسائط" : "Media Manager"}</h3>
        <Button size="sm" className="gap-1" onClick={() => fileRef.current?.click()} disabled={uploading}>
          {uploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
          {isAr ? "رفع ملف" : "Upload"}
        </Button>
        <input ref={fileRef} type="file" accept="image/*,application/pdf" onChange={handleUpload} className="hidden" />
      </div>

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <ImageIcon className="h-10 w-10 mx-auto mb-2 opacity-30" />
          <p className="text-body">{isAr ? "لا توجد ملفات" : "No media files yet"}</p>
          <p className="text-caption mt-1">{isAr ? "ارفع ملفاً للبدء" : "Upload a file to get started"}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {items.map((item) => (
            <Card key={item.uuid} className="group overflow-hidden">
              <div className="aspect-square relative bg-muted flex items-center justify-center">
                {item.mime_type?.startsWith("image/") ? (
                  <img src={item.url} alt={item.filename} className="w-full h-full object-cover" />
                ) : (
                  <ImageIcon className="h-8 w-8 text-muted-foreground" />
                )}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5">
                  <Button size="icon" variant="secondary" className="h-7 w-7"
                    onClick={() => copyUrl(item.url, item.uuid)}>
                    {copiedId === item.uuid ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  </Button>
                  <Button size="icon" variant="destructive" className="h-7 w-7"
                    onClick={() => handleDelete(item.uuid)}>
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              <CardContent className="p-2">
                <p className="text-[10px] truncate font-medium">{item.filename}</p>
                <p className="text-[10px] text-muted-foreground">{formatSize(item.size)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
