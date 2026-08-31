import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AuthNavbar } from '@/components/AuthNavbar';
import { apiRequest } from '@/services/client';
import { useTheme } from '@/hooks/use-theme';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DollarSign, TrendingUp, AlertTriangle, CheckCircle2,
  Bell, BarChart3, Search, ArrowUp, ArrowDown, Minus,
} from 'lucide-react';
import { motion } from 'framer-motion';

interface MarketRate {
  id: number;
  role: string;
  location: string;
  experience_level: string;
  currency: string;
  percentile_25: string;
  percentile_50: string;
  percentile_75: string;
  percentile_90: string;
  sample_size: number;
}

interface BenchmarkResult {
  market_median: string;
  market_25th: string;
  market_75th: string;
  percentile_rank: number;
  is_underpaid: string;
  role: string;
  location: string;
  experience_level: string;
}

interface SalaryInsight {
  id: number;
  insight_type: string;
  title: string;
  description: string;
  priority: string;
  is_actionable: boolean;
}

interface SalaryAlert {
  id: number;
  alert_type: string;
  title: string;
  description: string;
  impact: string;
  is_read: boolean;
  is_resolved: boolean;
}

function BenchmarkCard({ isAr }: { isAr: boolean }) {
  const [form, setForm] = useState({
    role: '',
    location: '',
    experience_level: 'mid',
    salary_min: '',
    salary_max: '',
  });

  const benchmark = useMutation({
    mutationFn: () =>
      apiRequest<BenchmarkResult>(`/salary/benchmark/?${new URLSearchParams(form).toString()}`),
  });

  const result = benchmark.data;

  const underpaidLabel: Record<string, { icon: typeof ArrowUp; color: string; text: string; textAr: string }> = {
    yes: { icon: ArrowDown, color: 'text-red-500', text: 'Below Market', textAr: 'أقل من السوق' },
    maybe: { icon: Minus, color: 'text-yellow-500', text: 'Near Market', textAr: 'قريب من السوق' },
    fair: { icon: CheckCircle2, color: 'text-green-500', text: 'Fair', textAr: 'عادل' },
    above: { icon: ArrowUp, color: 'text-blue-500', text: 'Above Market', textAr: 'أعلى من السوق' },
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          {isAr ? 'مقارنة راتبك بالسوق' : 'Benchmark Your Salary'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
          <Input
            placeholder={isAr ? 'المسمى الوظيفي' : 'Job title / role'}
            value={form.role}
            onChange={(e) => setForm(p => ({ ...p, role: e.target.value }))}
          />
          <Input
            placeholder={isAr ? 'الموقع' : 'Location'}
            value={form.location}
            onChange={(e) => setForm(p => ({ ...p, location: e.target.value }))}
          />
          <select
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={form.experience_level}
            onChange={(e) => setForm(p => ({ ...p, experience_level: e.target.value }))}
          >
            <option value="entry">{isAr ? 'مبتدئ' : 'Entry'}</option>
            <option value="mid">{isAr ? 'متوسط' : 'Mid-level'}</option>
            <option value="senior">{isAr ? 'خبير' : 'Senior'}</option>
            <option value="lead">{isAr ? 'قيادي' : 'Lead'}</option>
          </select>
          <Input
            type="number"
            placeholder={isAr ? 'الحد الأدنى للراتب' : 'Your salary min'}
            value={form.salary_min}
            onChange={(e) => setForm(p => ({ ...p, salary_min: e.target.value }))}
          />
          <Input
            type="number"
            placeholder={isAr ? 'الحد الأقصى للراتب' : 'Your salary max'}
            value={form.salary_max}
            onChange={(e) => setForm(p => ({ ...p, salary_max: e.target.value }))}
          />
          <Button
            onClick={() => benchmark.mutate()}
            disabled={!form.role || !form.location || benchmark.isPending}
            className="h-10"
          >
            <Search className="h-4 w-4 me-2" />
            {benchmark.isPending ? (isAr ? 'جاري البحث...' : 'Searching...') : (isAr ? 'قارن' : 'Compare')}
          </Button>
        </div>

        {benchmark.isError && (
          <div className="text-center py-6 text-muted-foreground">
            {isAr ? 'لا توجد بيانات سوقية لهذا الدور والموقع' : 'No market data found for this role and location'}
          </div>
        )}

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4"
          >
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground mb-1">{isAr ? 'الشريحة 25' : '25th Percentile'}</p>
              <p className="text-xl font-bold">${Number(result.market_25th).toLocaleString()}</p>
            </div>
            <div className="text-center p-4 rounded-lg bg-primary/10 border border-primary/20">
              <p className="text-sm text-muted-foreground mb-1">{isAr ? 'متوسط السوق' : 'Market Median'}</p>
              <p className="text-2xl font-bold text-primary">${Number(result.market_median).toLocaleString()}</p>
            </div>
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground mb-1">{isAr ? 'الشريحة 75' : '75th Percentile'}</p>
              <p className="text-xl font-bold">${Number(result.market_75th).toLocaleString()}</p>
            </div>
            <div className="text-center p-4 rounded-lg bg-muted/50">
              {(() => {
                const info = underpaidLabel[result.is_underpaid] || underpaidLabel['fair'];
                const Icon = info.icon;
                return (
                  <>
                    <p className="text-sm text-muted-foreground mb-1">{isAr ? 'تقييمك' : 'Your Standing'}</p>
                    <div className={`flex items-center justify-center gap-1 text-xl font-bold ${info.color}`}>
                      <Icon className="h-5 w-5" />
                      {isAr ? info.textAr : info.text}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {isAr ? `الشريحة ${result.percentile_rank}` : `${result.percentile_rank}th percentile`}
                    </p>
                  </>
                );
              })()}
            </div>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}

function MarketRatesSection({ isAr }: { isAr: boolean }) {
  const [roleFilter, setRoleFilter] = useState('');

  const { data: rates, isLoading } = useQuery({
    queryKey: ['market-rates', roleFilter],
    queryFn: () => apiRequest<MarketRate[]>(`/salary/market-rates/${roleFilter ? `?role=${roleFilter}` : ''}`),
    enabled: roleFilter.length >= 2,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          {isAr ? 'أسعار السوق' : 'Market Rates'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Input
          placeholder={isAr ? 'ابحث عن دور وظيفي...' : 'Search for a role...'}
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="mb-4"
        />

        {isLoading && <div className="text-center py-6 text-muted-foreground">{isAr ? 'جاري التحميل...' : 'Loading...'}</div>}

        {rates && rates.length === 0 && (
          <div className="text-center py-6 text-muted-foreground">
            {isAr ? 'لا توجد بيانات لهذا الدور' : 'No data found for this role'}
          </div>
        )}

        {rates && rates.length > 0 && (
          <div className="space-y-3">
            {rates.map((rate) => (
              <div key={rate.id} className="p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-medium">{rate.role}</h4>
                    <p className="text-sm text-muted-foreground">{rate.location} &middot; {rate.experience_level}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">{rate.sample_size} {isAr ? 'عينة' : 'samples'}</span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center text-sm">
                  <div>
                    <p className="text-muted-foreground text-xs">P25</p>
                    <p className="font-medium">${Number(rate.percentile_25).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">P50</p>
                    <p className="font-semibold text-primary">${Number(rate.percentile_50).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">P75</p>
                    <p className="font-medium">${Number(rate.percentile_75).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">P90</p>
                    <p className="font-medium">${Number(rate.percentile_90).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!roleFilter && (
          <div className="text-center py-6 text-muted-foreground">
            {isAr ? 'اكتب اسم الدور للبحث عن أسعار السوق' : 'Type a role name to search market rates'}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function SalaryInsightsPage() {
  const { lang } = useTheme();
  const isAr = lang === 'ar';
  const queryClient = useQueryClient();

  const { data: insights } = useQuery({
    queryKey: ['salary-insights'],
    queryFn: () => apiRequest<SalaryInsight[]>('/salary/insights/'),
  });

  const { data: alerts } = useQuery({
    queryKey: ['salary-alerts'],
    queryFn: () => apiRequest<SalaryAlert[]>('/salary/alerts/'),
  });

  const markRead = useMutation({
    mutationFn: (id: number) => apiRequest(`/salary/alerts/${id}/read/`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salary-alerts'] }),
  });

  const priorityColor: Record<string, string> = {
    high: 'border-red-500/30 bg-red-500/5',
    medium: 'border-yellow-500/30 bg-yellow-500/5',
    low: 'border-green-500/30 bg-green-500/5',
  };

  return (
    <div className="min-h-screen bg-background">
      <AuthNavbar />
      <main className="container py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">
            <DollarSign className="inline h-8 w-8 text-primary me-2" />
            {isAr ? 'رؤى الرواتب' : 'Salary Insights'}
          </h1>
          <p className="text-muted-foreground mt-1">
            {isAr ? 'قارن راتبك بالسوق واحصل على رؤى ذكية' : 'Compare your salary with the market and get smart insights'}
          </p>
        </div>

        <BenchmarkCard isAr={isAr} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MarketRatesSection isAr={isAr} />

          <div className="space-y-6">
            {/* Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  {isAr ? 'رؤى شخصية' : 'Personal Insights'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!insights || insights.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    {isAr ? 'لا توجد رؤى حالياً. قم بمقارنة راتبك أولاً.' : 'No insights yet. Run a benchmark comparison first.'}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {insights.map((insight) => (
                      <div key={insight.id} className={`p-3 rounded-lg border ${priorityColor[insight.priority] || ''}`}>
                        <h4 className="font-medium text-sm">{insight.title}</h4>
                        <p className="text-sm text-muted-foreground mt-1">{insight.description}</p>
                        {insight.is_actionable && (
                          <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                            {isAr ? 'قابل للتنفيذ' : 'Actionable'}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Alerts */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-primary" />
                  {isAr ? 'تنبيهات الرواتب' : 'Salary Alerts'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!alerts || alerts.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    {isAr ? 'لا توجد تنبيهات حالياً' : 'No salary alerts right now'}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className={`p-3 rounded-lg border transition-colors ${alert.is_read ? 'opacity-60' : 'bg-accent/30'}`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h4 className="font-medium text-sm">{alert.title}</h4>
                            <p className="text-sm text-muted-foreground mt-1">{alert.description}</p>
                          </div>
                          {!alert.is_read && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => markRead.mutate(alert.id)}
                              className="shrink-0"
                            >
                              <CheckCircle2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
