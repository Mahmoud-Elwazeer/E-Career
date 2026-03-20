import { useState, useMemo, useEffect } from "react";
import {
  useReactTable, getCoreRowModel, getSortedRowModel,
  getFilteredRowModel, getPaginationRowModel, flexRender,
  createColumnHelper, type SortingState, type ColumnFiltersState, type RowSelectionState,
} from "@tanstack/react-table";
import { Link } from "react-router-dom";
import { ArrowUpDown, ArrowUp, ArrowDown, CheckCircle, XCircle, Eye, Trash2, MoreHorizontal, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Card } from "@/components/ui/card";
import { BulkActionsBar, AnimatedStatusBadge } from "@/components/admin/AdminMotion";
import { useTheme } from "@/hooks/use-theme";
import { fetchJobs, type Job } from "@/services/jobs";
import { adminDeleteJob, adminPublishJob, adminArchiveJob } from "@/services/admin";
import { useToast } from "@/hooks/use-toast";

const columnHelper = createColumnHelper<Job>();

export function AdminJobsTable() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetchJobs({ page_size: 100 });
      setJobs(res.results ?? []);
    } catch { setJobs([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (slug: string) => {
    try {
      await adminArchiveJob(slug);
      toast({ title: "Job archived" });
      load();
    } catch { toast({ title: "Failed", variant: "destructive" }); }
  };

  const handlePublish = async (slug: string) => {
    try {
      await adminPublishJob(slug);
      toast({ title: "Job published" });
      load();
    } catch { toast({ title: "Failed", variant: "destructive" }); }
  };

  const columns = useMemo(() => [
    columnHelper.display({
      id: "select",
      header: ({ table }) => (
        <Checkbox checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(v) => table.toggleAllPageRowsSelected(!!v)} aria-label="Select all" />
      ),
      cell: ({ row }) => (
        <Checkbox checked={row.getIsSelected()}
          onCheckedChange={(v) => row.toggleSelected(!!v)} aria-label="Select row" />
      ),
      size: 40,
    }),
    columnHelper.accessor("title", {
      header: ({ column }) => (
        <Button variant="ghost" size="sm" className="gap-1 -ms-3 text-caption font-medium"
          onClick={() => column.toggleSorting()}>
          {isAr ? "العنوان" : "Title"}
          {column.getIsSorted() === "asc" ? <ArrowUp className="h-3 w-3" /> :
           column.getIsSorted() === "desc" ? <ArrowDown className="h-3 w-3" /> :
           <ArrowUpDown className="h-3 w-3 opacity-40" />}
        </Button>
      ),
      cell: ({ row }) => (
        <Link to={`/app/jobs/${row.original.slug}`}
          className="font-medium hover:text-primary transition-colors">
          {row.original.title}
        </Link>
      ),
    }),
    columnHelper.accessor("company_name", {
      header: () => <span className="hidden md:inline">{isAr ? "الشركة" : "Company"}</span>,
      cell: ({ getValue }) => (
        <span className="hidden md:inline text-muted-foreground">{getValue()}</span>
      ),
    }),
    columnHelper.accessor("source_name", {
      header: () => <span className="hidden lg:inline">{isAr ? "المصدر" : "Source"}</span>,
      cell: ({ row }) => (
        <span className="hidden lg:flex items-center gap-1.5">
          {row.original.source_logo && <img src={row.original.source_logo} alt="" className="h-4 w-4 rounded" />}
          {row.original.source_name}
        </span>
      ),
    }),
    columnHelper.accessor("status", {
      header: () => <span>{isAr ? "الحالة" : "Status"}</span>,
      cell: ({ getValue }) => {
        const s = getValue();
        return (
          <AnimatedStatusBadge
            status={s === "active" ? "active" : s === "pending" ? "pending" : "expired"}
            label={s === "active" ? (isAr ? "نشطة" : "Active") : s === "pending" ? (isAr ? "قيد المراجعة" : "Pending") : (isAr ? "مؤرشفة" : "Archived")}
          />
        );
      },
    }),
    columnHelper.accessor("posted_at", {
      header: ({ column }) => (
        <Button variant="ghost" size="sm"
          className="gap-1 -ms-3 text-caption font-medium hidden sm:inline-flex"
          onClick={() => column.toggleSorting()}>
          {isAr ? "التاريخ" : "Date"}
          {column.getIsSorted() === "asc" ? <ArrowUp className="h-3 w-3" /> :
           column.getIsSorted() === "desc" ? <ArrowDown className="h-3 w-3" /> :
           <ArrowUpDown className="h-3 w-3 opacity-40" />}
        </Button>
      ),
      cell: ({ getValue }) => (
        <span className="hidden sm:inline text-muted-foreground">
          {new Date(getValue()).toLocaleDateString()}
        </span>
      ),
    }),
    columnHelper.display({
      id: "actions",
      size: 40,
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7">
              <MoreHorizontal className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem className="gap-2" asChild>
              <Link to={`/app/jobs/${row.original.slug}`}>
                <Eye className="h-3.5 w-3.5" /> {isAr ? "عرض" : "View"}
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem className="gap-2" onClick={() => handlePublish(row.original.slug)}>
              <CheckCircle className="h-3.5 w-3.5" /> {isAr ? "نشر" : "Publish"}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2 text-destructive" onClick={() => handleDelete(row.original.slug)}>
              <Trash2 className="h-3.5 w-3.5" /> {isAr ? "أرشفة" : "Archive"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    }),
  ], [isAr]);

  const table = useReactTable({
    data: jobs,
    columns,
    state: { sorting, columnFilters, rowSelection, globalFilter },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  });

  const selectedCount = Object.keys(rowSelection).length;

  if (loading) return (
    <div className="flex justify-center py-12">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );

  return (
    <div className="space-y-4">
      <BulkActionsBar visible={selectedCount > 0}>
        <Card className="border-primary/20">
          <div className="p-3 flex items-center gap-3">
            <span className="text-caption font-medium">{selectedCount} {isAr ? "محدد" : "selected"}</span>
            <Button size="sm" variant="outline" className="rounded-lg text-caption gap-1">
              <CheckCircle className="h-3 w-3" /> {isAr ? "موافقة" : "Approve"}
            </Button>
            <Button size="sm" variant="outline" className="rounded-lg text-caption gap-1 text-destructive">
              <XCircle className="h-3 w-3" /> {isAr ? "رفض" : "Reject"}
            </Button>
            <Button size="sm" variant="ghost" className="text-caption ms-auto" onClick={() => setRowSelection({})}>
              {isAr ? "إلغاء" : "Clear"}
            </Button>
          </div>
        </Card>
      </BulkActionsBar>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-caption">
            <thead>
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id} className="border-b bg-surface-2">
                  {hg.headers.map((header) => (
                    <th key={header.id} className="p-3 text-start">
                      {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id}
                  className={`border-b transition-colors duration-150 ${row.getIsSelected() ? "bg-primary-muted/30" : "hover:bg-accent/30"}`}>
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="p-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="p-3 border-t flex items-center justify-between">
          <span className="text-caption text-muted-foreground">
            {table.getState().pagination.pageIndex * 10 + 1}–
            {Math.min((table.getState().pagination.pageIndex + 1) * 10, table.getFilteredRowModel().rows.length)}{" "}
            of {table.getFilteredRowModel().rows.length}
          </span>
          <div className="flex gap-1">
            <Button variant="outline" size="sm" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()}>
              {isAr ? "السابق" : "Prev"}
            </Button>
            <Button variant="outline" size="sm" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()}>
              {isAr ? "التالي" : "Next"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
