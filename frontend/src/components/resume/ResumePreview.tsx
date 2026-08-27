import { forwardRef } from 'react';

interface Experience {
  id: string;
  company: string;
  title: string;
  start_date: string;
  end_date: string;
  current: boolean;
  description: string;
}

interface Education {
  id: string;
  school: string;
  degree: string;
  field?: string;
  start_date: string;
  end_date: string;
  current: boolean;
  gpa?: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  url?: string;
  technologies?: string[];
}

interface ResumeData {
  personal_info: {
    full_name: string;
    email: string;
    phone: string;
    location: string;
    linkedin?: string;
    github?: string;
    website?: string;
  };
  summary: string;
  experience: Experience[];
  education: Education[];
  skills: string[];
  projects: Project[];
  certifications: string[];
  languages: string[];
}

interface ResumePreviewProps {
  data: ResumeData;
  template?: string;
}

const ResumePreview = forwardRef<HTMLDivElement, ResumePreviewProps>(
  ({ data, template = 'modern' }, ref) => {
    const { personal_info, summary, experience, education, skills, projects, certifications, languages } = data;

    const formatDate = (date: string, current: boolean) => {
      if (current) return 'Present';
      if (!date) return '';
      const d = new Date(date);
      return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    };

    const hasContent = summary || experience.length > 0 || education.length > 0 ||
                       skills.length > 0 || projects.length > 0 || certifications.length > 0;

    return (
      <div ref={ref} className="resume-preview bg-white text-gray-900 p-8 min-h-[1056px] w-full max-w-[816px] mx-auto shadow-sm text-[11px] leading-relaxed font-[system-ui]">
        {/* Header */}
        <div className={`mb-4 pb-3 border-b-2 ${template === 'creative' ? 'border-indigo-500' : template === 'minimalist' ? 'border-gray-300' : 'border-blue-600'}`}>
          <h1 className={`text-2xl font-bold ${template === 'creative' ? 'text-indigo-700' : 'text-gray-900'}`}>
            {personal_info.full_name || 'Your Name'}
          </h1>
          <div className="flex flex-wrap gap-3 mt-1.5 text-gray-600 text-[10px]">
            {personal_info.email && <span>{personal_info.email}</span>}
            {personal_info.phone && <span>{personal_info.phone}</span>}
            {personal_info.location && <span>{personal_info.location}</span>}
            {personal_info.linkedin && <span>{personal_info.linkedin}</span>}
            {personal_info.github && <span>{personal_info.github}</span>}
            {personal_info.website && <span>{personal_info.website}</span>}
          </div>
        </div>

        {!hasContent && (
          <div className="text-center text-gray-400 py-16">
            <p className="text-lg">Start adding content to see your resume preview</p>
          </div>
        )}

        {/* Summary */}
        {summary && (
          <div className="mb-4">
            <h2 className={`text-xs font-bold uppercase tracking-wider mb-1 ${template === 'creative' ? 'text-indigo-600' : 'text-blue-700'}`}>
              Professional Summary
            </h2>
            <p className="text-gray-700">{summary}</p>
          </div>
        )}

        {/* Experience */}
        {experience.length > 0 && (
          <div className="mb-4">
            <h2 className={`text-xs font-bold uppercase tracking-wider mb-2 ${template === 'creative' ? 'text-indigo-600' : 'text-blue-700'}`}>
              Experience
            </h2>
            <div className="space-y-3">
              {experience.map((exp) => (
                <div key={exp.id}>
                  <div className="flex justify-between items-baseline">
                    <div>
                      <span className="font-semibold">{exp.title || 'Position'}</span>
                      {exp.company && <span className="text-gray-600"> at {exp.company}</span>}
                    </div>
                    <span className="text-gray-500 text-[10px] whitespace-nowrap ml-2">
                      {formatDate(exp.start_date, false)} — {formatDate(exp.end_date, exp.current)}
                    </span>
                  </div>
                  {exp.description && (
                    <p className="text-gray-600 mt-0.5 whitespace-pre-line">{exp.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {education.length > 0 && (
          <div className="mb-4">
            <h2 className={`text-xs font-bold uppercase tracking-wider mb-2 ${template === 'creative' ? 'text-indigo-600' : 'text-blue-700'}`}>
              Education
            </h2>
            <div className="space-y-2">
              {education.map((edu) => (
                <div key={edu.id}>
                  <div className="flex justify-between items-baseline">
                    <div>
                      <span className="font-semibold">{edu.degree || 'Degree'}</span>
                      {edu.field && <span className="text-gray-600"> in {edu.field}</span>}
                    </div>
                    <span className="text-gray-500 text-[10px] whitespace-nowrap ml-2">
                      {formatDate(edu.start_date, false)} — {formatDate(edu.end_date, edu.current)}
                    </span>
                  </div>
                  <p className="text-gray-600">{edu.school}{edu.gpa ? ` — GPA: ${edu.gpa}` : ''}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <div className="mb-4">
            <h2 className={`text-xs font-bold uppercase tracking-wider mb-1 ${template === 'creative' ? 'text-indigo-600' : 'text-blue-700'}`}>
              Skills
            </h2>
            <div className="flex flex-wrap gap-1.5">
              {skills.map((skill, i) => (
                <span key={i} className={`px-2 py-0.5 rounded text-[10px] ${
                  template === 'creative' ? 'bg-indigo-50 text-indigo-700' :
                  template === 'minimalist' ? 'bg-gray-100 text-gray-700' :
                  'bg-blue-50 text-blue-700'
                }`}>
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Projects */}
        {projects.length > 0 && (
          <div className="mb-4">
            <h2 className={`text-xs font-bold uppercase tracking-wider mb-2 ${template === 'creative' ? 'text-indigo-600' : 'text-blue-700'}`}>
              Projects
            </h2>
            <div className="space-y-2">
              {projects.map((proj) => (
                <div key={proj.id}>
                  <div className="flex items-baseline gap-2">
                    <span className="font-semibold">{proj.name}</span>
                    {proj.url && <span className="text-blue-600 text-[10px]">{proj.url}</span>}
                  </div>
                  {proj.description && <p className="text-gray-600 mt-0.5">{proj.description}</p>}
                  {proj.technologies && proj.technologies.length > 0 && (
                    <p className="text-gray-500 text-[10px] mt-0.5">Tech: {proj.technologies.join(', ')}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Certifications */}
        {certifications.length > 0 && (
          <div className="mb-4">
            <h2 className={`text-xs font-bold uppercase tracking-wider mb-1 ${template === 'creative' ? 'text-indigo-600' : 'text-blue-700'}`}>
              Certifications
            </h2>
            <ul className="list-disc list-inside text-gray-700">
              {certifications.map((cert, i) => (
                <li key={i}>{cert}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Languages */}
        {languages.length > 0 && (
          <div className="mb-4">
            <h2 className={`text-xs font-bold uppercase tracking-wider mb-1 ${template === 'creative' ? 'text-indigo-600' : 'text-blue-700'}`}>
              Languages
            </h2>
            <p className="text-gray-700">{languages.join(' • ')}</p>
          </div>
        )}
      </div>
    );
  }
);

ResumePreview.displayName = 'ResumePreview';
export default ResumePreview;
