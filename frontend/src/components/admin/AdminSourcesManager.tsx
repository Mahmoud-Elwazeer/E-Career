import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, RefreshCw, Trash2, Pencil, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose,
} from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";
import { sourceFormSchema, type SourceFormValues } from "@/data/schemas";
import {
  adminFetchAllSources, adminCreateSource, adminUpdateSource, adminDeleteSource,
} from "@/services/admin";
import type { Source } from "@/services/jobs";

export function AdminSourcesManager() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const form = useForm<SourceFormValues>({
    resolver: zodResolver(sourceFormSchema),
    defaultValues: { name: "", url: "", logoUrl: "" },
  });

  const load = async () => {
    setLoading(true);
    try { setSources(await adminFetchAllSources()); }
    catch { setSources([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openAdd = () => {
    setEditingSource(null);
    form.reset({ name: "", url: "", logoUrl: "" });
    setDialogOpen(true);
  };

  const openEdit = (source: Source) => {
    setEditingSource(source);
    form.reset({ name: source.name, url: source.url, logoUrl: source.logo_url });
    setDialogOpen(true);
  };

  const onSubmit = async (values: SourceFormValues) => {
    try {
      if (editingSource) {
        await adminUpdateSource(editingSource.slug, { name: values.name, url: values.url, logo_url: values.logoUrl });
        toast({ title: isAr ? "تم تحديث المصدر" : "Source updated" });
      } else {
        await adminCreateSource({ name: values.name, url: values.url, logo_url: values.logoUrl });
        toast({ title: isAr ? "تم إضافة المصدر" : "Source added" });
      }
      setDialogOpen(false);
      load();
    } catch (e: any) {
      toast({ title: "Error", description: e?.message, variant: "destructive" });
    }
  };

  const handleDelete = async (slug: string) => {
    try {
      await adminDeleteSource(slug);
      toast({ title: isAr ? "تم الحذف" : "Source removed" });
      load();
    } catch {
      toast({ title: "Failed", variant: "destructive" });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-body font-medium">{isAr ? "إدارة المصادر" : "Manage Sources"}</h3>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-1" onClick={load} disabled={loading}>
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            {isAr ? "تحديث" : "Refresh"}
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="gap-1" onClick={openAdd}>
                <Plus className="h-3.5 w-3.5" /> {isAr ? "إضافة" : "Add Source"}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingSource ? (isAr ? "تعديل المصدر" : "Edit Source") : (isAr ? "إضافة مصدر" : "Add Source")}</DialogTitle>
              </DialogHeader>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField control={form.control} name="name" render={({ field }) => (
                    <FormItem><FormLabel>{isAr ? "الاسم" : "Name"}</FormLabel>
                      <FormControl><Input {...field} /></FormControl>
                      <FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="url" render={({ field }) => (
                    <FormItem><FormLabel>URL</FormLabel>
                      <FormControl><Input {...field} placeholder="https://..." /></FormControl>
                      <FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="logoUrl" render={({ field }) => (
                    <FormItem><FormLabel>{isAr ? "رابط الشعار" : "Logo URL"}</FormLabel>
                      <FormControl><Input {...field} placeholder="https://..." /></FormControl>
                      <FormMessage /></FormItem>
                  )} />
                  <DialogFooter>
                    <DialogClose asChild><Button type="button" variant="outline">{isAr ? "إلغاء" : "Cancel"}</Button></DialogClose>
                    <Button type="submit">{editingSource ? (isAr ? "حفظ" : "Save") : (isAr ? "إضافة" : "Add")}</Button>
                  </DialogFooter>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      ) : (
        <div className="space-y-3">
          {sources.map((source) => (
            <Card key={source.id}>
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {source.logo_url && (
                    <img src={source.logo_url} alt={source.name} className="h-9 w-9 rounded-lg object-contain" />
                  )}
                  <div>
                    <p className="text-body font-medium">{source.name}</p>
                    <a href={source.url} target="_blank" rel="noopener noreferrer"
                      className="text-caption text-primary hover:underline">{source.url}</a>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={source.is_active ? "default" : "secondary"}>
                    {source.is_active ? (isAr ? "نشط" : "Active") : (isAr ? "متوقف" : "Paused")}
                  </Badge>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(source)}>
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive"
                    onClick={() => handleDelete(source.slug)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
