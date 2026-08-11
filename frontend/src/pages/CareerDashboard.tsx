import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTheme } from "@/hooks/use-theme";
import {
  User,
  FileText,
  Award,
  Briefcase,
  GraduationCap,
  Target,
  TrendingUp,
  Edit,
  ExternalLink,
  Star,
} from "lucide-react";
import { AskRashidCard } from "@/components/rashid/AskRashidButton";

export default function CareerDashboard() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  // Mock profile completeness
  const profileCompleteness = 65;

  return (
    <AppLayout>
      <div className="container max-w-7xl py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-heading-1 mb-2">
            {isAr ? "مساري المهني" : "Career Dashboard"}
          </h1>
          <p className="text-muted-foreground">
            {isAr ? "إدارة ملفك المهني وتطوير مهاراتك" : "Manage your professional profile and develop your skills"}
          </p>
        </div>

        {/* Profile Completeness Card */}
        <Card className="mb-6 border-primary/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg mb-1">
                  {isAr ? "اكتمال الملف الشخصي" : "Profile Completeness"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {isAr ? "أكمل ملفك لتحسين فرصك" : "Complete your profile to improve your opportunities"}
                </p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-primary">{profileCompleteness}%</p>
              </div>
            </div>
            <Progress value={profileCompleteness} className="h-2" />
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant="outline" className="text-xs">
                {isAr ? "✓ المعلومات الأساسية" : "✓ Basic Info"}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {isAr ? "✓ الخبرات" : "✓ Experience"}
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {isAr ? "○ المهارات" : "○ Skills"}
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {isAr ? "○ السيرة الذاتية" : "○ Resume"}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Main Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-grid">
            <TabsTrigger value="overview">
              <User className="h-4 w-4 mr-2" />
              {isAr ? "نظرة عامة" : "Overview"}
            </TabsTrigger>
            <TabsTrigger value="resume">
              <FileText className="h-4 w-4 mr-2" />
              {isAr ? "السيرة الذاتية" : "Resume"}
            </TabsTrigger>
            <TabsTrigger value="skills">
              <Award className="h-4 w-4 mr-2" />
              {isAr ? "المهارات" : "Skills"}
            </TabsTrigger>
            <TabsTrigger value="preferences">
              <Target className="h-4 w-4 mr-2" />
              {isAr ? "التفضيلات" : "Preferences"}
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Talent Score */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    {isAr ? "نقاط الموهبة" : "Talent Score"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-4xl font-bold text-primary">72</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {isAr ? "من 100" : "out of 100"}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge variant="secondary" className="text-xs">
                        <Star className="h-3 w-3 mr-1" />
                        {isAr ? "جيد" : "Good"}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{isAr ? "المهارات" : "Skills"}</span>
                      <span className="font-medium">80/100</span>
                    </div>
                    <Progress value={80} className="h-1.5" />
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{isAr ? "الخبرة" : "Experience"}</span>
                      <span className="font-medium">65/100</span>
                    </div>
                    <Progress value={65} className="h-1.5" />
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{isAr ? "التعليم" : "Education"}</span>
                      <span className="font-medium">70/100</span>
                    </div>
                    <Progress value={70} className="h-1.5" />
                  </div>
                  <Button variant="outline" className="w-full mt-4" asChild>
                    <a href="/app/talent-score">
                      {isAr ? "عرض التفاصيل" : "View Details"}
                    </a>
                  </Button>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>{isAr ? "إجراءات سريعة" : "Quick Actions"}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button variant="outline" className="w-full justify-start" asChild>
                    <a href="/app/profile">
                      <Edit className="h-4 w-4 mr-2" />
                      {isAr ? "تعديل الملف الشخصي" : "Edit Profile"}
                    </a>
                  </Button>
                  <Button variant="outline" className="w-full justify-start" asChild>
                    <a href="/app/resume">
                      <FileText className="h-4 w-4 mr-2" />
                      {isAr ? "تحديث السيرة الذاتية" : "Update Resume"}
                    </a>
                  </Button>
                  <Button variant="outline" className="w-full justify-start" asChild>
                    <a href="/app/career/public-profile">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      {isAr ? "عرض الملف العام" : "View Public Profile"}
                    </a>
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Rashid Career Advice */}
            <AskRashidCard
              tool="career_path"
              title={isAr ? "احصل على نصيحة مهنية من راشد" : "Get Career Advice from Rashid"}
              description={isAr ? "اسأل راشد عن مسارك المهني وكيفية تطويره" : "Ask Rashid about your career path and how to develop it"}
            />

            {/* Experience Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5" />
                    {isAr ? "الخبرات العملية" : "Work Experience"}
                  </CardTitle>
                  <Button variant="outline" size="sm">
                    <Edit className="h-3 w-3 mr-2" />
                    {isAr ? "تعديل" : "Edit"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground text-center py-8">
                  {isAr ? "لم تضف أي خبرات عملية بعد" : "No work experience added yet"}
                </p>
                <Button variant="outline" className="w-full">
                  {isAr ? "إضافة خبرة" : "Add Experience"}
                </Button>
              </CardContent>
            </Card>

            {/* Education Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <GraduationCap className="h-5 w-5" />
                    {isAr ? "التعليم" : "Education"}
                  </CardTitle>
                  <Button variant="outline" size="sm">
                    <Edit className="h-3 w-3 mr-2" />
                    {isAr ? "تعديل" : "Edit"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground text-center py-8">
                  {isAr ? "لم تضف أي مؤهلات تعليمية بعد" : "No education added yet"}
                </p>
                <Button variant="outline" className="w-full">
                  {isAr ? "إضافة مؤهل" : "Add Education"}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Resume Tab */}
          <TabsContent value="resume">
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? "السيرة الذاتية" : "Resume"}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {isAr ? "أنشئ وحمّل سيرتك الذاتية المهنية" : "Create and upload your professional resume"}
                </p>
                <Button asChild>
                  <a href="/app/resume">
                    <FileText className="h-4 w-4 mr-2" />
                    {isAr ? "انتقل إلى منشئ السيرة الذاتية" : "Go to Resume Builder"}
                  </a>
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Skills Tab */}
          <TabsContent value="skills">
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? "المهارات" : "Skills"}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {isAr ? "أضف مهاراتك لتحسين فرص التوظيف" : "Add your skills to improve job opportunities"}
                </p>
                <Button>
                  {isAr ? "إضافة مهارات" : "Add Skills"}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences">
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? "تفضيلات الوظائف" : "Job Preferences"}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  {isAr ? "حدد تفضيلاتك للحصول على توصيات أفضل" : "Set your preferences for better job recommendations"}
                </p>
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium">{isAr ? "نوع العمل المفضل" : "Preferred Work Type"}</label>
                    <p className="text-sm text-muted-foreground">{isAr ? "عن بُعد، في المكتب، هجين" : "Remote, Onsite, Hybrid"}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium">{isAr ? "المواقع المفضلة" : "Preferred Locations"}</label>
                    <p className="text-sm text-muted-foreground">{isAr ? "اختر المدن المفضلة للعمل" : "Choose preferred cities to work"}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium">{isAr ? "نطاق الراتب" : "Salary Range"}</label>
                    <p className="text-sm text-muted-foreground">{isAr ? "حدد توقعاتك للراتب" : "Set your salary expectations"}</p>
                  </div>
                </div>
                <Button className="w-full">{isAr ? "حفظ التفضيلات" : "Save Preferences"}</Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
